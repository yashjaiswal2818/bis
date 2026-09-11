"""High-Performance In-Memory Government Procurement Schedule Engine.

Provides sub-millisecond, deterministic keyword automaton and trie matching
across all CPWD DSR subheads, MoRTH specifications, and GeM product categories.
Operates in O(M) time where M is query character length.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ITEM_MASTER_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "government_procurement_item_master.json"


class TrieNode:
    __slots__ = ("children", "item_data", "alias_length")

    def __init__(self):
        self.children: dict[str, TrieNode] = {}
        self.item_data: dict[str, Any] | None = None
        self.alias_length: int = 0


class GovernmentScheduleEngine:
    """Singleton in-memory automaton for CPWD DSR / GeM schedule matching."""

    _instance: GovernmentScheduleEngine | None = None

    def __init__(self):
        self.root = TrieNode()
        self.total_items = 0
        self.total_aliases = 0
        self.load_and_compile()

    @classmethod
    def get_instance(cls) -> GovernmentScheduleEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_and_compile(self):
        """Loads schedule master and builds prefix token trie."""
        t0 = time.perf_counter()
        if not ITEM_MASTER_PATH.exists():
            print(f"[Warning] Schedule item master not found at: {ITEM_MASTER_PATH}", file=sys.stderr)
            return

        try:
            items = json.loads(ITEM_MASTER_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Error] Failed to read schedule item master: {e}", file=sys.stderr)
            return

        self.total_items = len(items)
        alias_count = 0

        for item in items:
            aliases = item.get("aliases", [])
            for alias in aliases:
                norm_alias = self._normalize(alias)
                if not norm_alias:
                    continue

                # Insert into trie
                current = self.root
                tokens = norm_alias.split()
                for tok in tokens:
                    if tok not in current.children:
                        current.children[tok] = TrieNode()
                    current = current.children[tok]

                # Store matching item data on terminal node
                current.item_data = item
                current.alias_length = len(tokens)
                alias_count += 1

        self.total_aliases = alias_count
        dur = (time.perf_counter() - t0) * 1000.0
        print(f"[ScheduleEngine] Compiled {self.total_items} items ({self.total_aliases} aliases) into in-memory trie in {dur:.2f}ms")

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalizes text for trie insertion and matching."""
        clean = re.sub(r"[^\w\s\-]", " ", text.lower())
        clean = re.sub(r"[\-_]", " ", clean)
        return " ".join(clean.split())

    def match_schedule(self, query: str, cleaned_query: str = "") -> dict[str, Any] | None:
        """Finds longest matching schedule entry in O(M) time across query words."""
        candidates = [query]
        if cleaned_query and cleaned_query != query:
            candidates.append(cleaned_query)

        best_match: dict[str, Any] | None = None
        max_length = 0

        for text in candidates:
            tokens = self._normalize(text).split()
            n = len(tokens)

            # Check every starting token position
            for i in range(n):
                current = self.root
                for j in range(i, n):
                    tok = tokens[j]
                    if tok in current.children:
                        current = current.children[tok]
                        if current.item_data and current.alias_length > max_length:
                            max_length = current.alias_length
                            best_match = current.item_data
                    else:
                        break

        return best_match


if __name__ == "__main__":
    engine = GovernmentScheduleEngine.get_instance()
    test_queries = [
        "Supply of 43 Grade Ordinary Portland Cement for structural bridge works",
        "Procurement of TMT 500D rebar for RCC slab",
        "Centrifugally cast DI K9 pipes 300mm for municipal water transmission",
        "Viscosity Grade VG-30 bitumen for road surfacing",
        "Interlocking concrete paver blocks M40",
        "1100V PVC copper insulated wires for building electrification",
        "Gold jewellery 22k with mandatory 6-digit HUID hallmarking",
    ]

    print("\n--- TEST RUN ON GOVERNMENT QUERIES ---")
    for q in test_queries:
        m = engine.match_schedule(q)
        if m:
            print(f"✓ \"{q[:45]}...\" -> {m['is_code']} ({m['canonical_title'][:35]} | {m['schedule_category'][:25]})")
        else:
            print(f"✗ Missed: {q}")

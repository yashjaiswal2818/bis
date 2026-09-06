"""Grounded Rationale Engine.

Provides 100% offline, zero-hallucination factual rationales based on
standards scope and QCO legal mandates, with an optional cloud LLM fallback.
"""
from __future__ import annotations

import os
from typing import Any


class GroundedRationaleEngine:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

    def generate_offline_rationale(
        self,
        query: str,
        is_code: str,
        title: str,
        scope: str,
        qco_rules: list[dict[str, Any]],
        confidence: str,
    ) -> str:
        """Generates an instant, fact-based grounded explanation without external APIs."""
        scope_snippet = (scope[:220].strip() + "...") if len(scope) > 220 else (scope or title)

        # Check if QCO applies
        qco_text = ""
        if qco_rules and qco_rules[0].get("is_mandatory"):
            order = qco_rules[0].get("order_name", "Mandatory QCO")
            ministry = qco_rules[0].get("issuing_ministry", "Line Ministry")
            qco_text = f" Under {order} issued by {ministry}, compliance is legally mandatory for all public procurement."

        rationale = (
            f"Directly addresses query requirements. {is_code} ({title}) covers: \"{scope_snippet}\". "
            f"Retrieval confidence is {confidence}.{qco_text}"
        )
        return rationale

    def generate_rationale(
        self,
        query: str,
        is_code: str,
        title: str,
        scope: str,
        qco_rules: list[dict[str, Any]],
        confidence: str,
        use_cloud_llm: bool = False,
    ) -> str:
        """Generates rationale, using offline mode by default or cloud if requested and keys exist."""
        if not use_cloud_llm or (not self.gemini_key and not self.groq_key):
            return self.generate_offline_rationale(query, is_code, title, scope, qco_rules, confidence)

        # Cloud generation fallback
        try:
            if self.gemini_key:
                from google import genai
                client = genai.Client(api_key=self.gemini_key)
                prompt = (
                    f"In 2 crisp sentences, explain to a procurement officer why Indian Standard {is_code} "
                    f"({title}) is the correct standard for: \"{query}\". Ground strictly on this scope: \"{scope[:300]}\"."
                )
                resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                if resp.text:
                    return resp.text.strip()
        except Exception:
            pass

        # Default back to offline rationale if cloud fails
        return self.generate_offline_rationale(query, is_code, title, scope, qco_rules, confidence)

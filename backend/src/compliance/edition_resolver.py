import re
import time
import sqlite3
from collections import defaultdict
from src.database.sqlite_manager import DB_PATH

class EditionResolver:
    _instance = None
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.strict_index = defaultdict(list)
        self.root_index = defaultdict(list)
        self.build_time_ms = 0
        self.multi_edition_count = 0
        self.build_index()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def build_index(self):
        start = time.time()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        rows = cur.execute("SELECT is_code, title FROM standards_registry").fetchall()
        
        for (code, title) in rows:
            parts = code.split(":")
            base_code = parts[0].strip().upper()
            year = None
            if len(parts) >= 2:
                ymatch = re.search(r'\d{4}', parts[1])
                if ymatch:
                    year = int(ymatch.group(0))
            
            rmatch = re.match(r'^(IS\s*\d+)\b', base_code, re.IGNORECASE)
            root_code = rmatch.group(1).upper() if rmatch else base_code
            
            has_part_in_code = bool(re.search(r'\bPART\b', base_code, re.IGNORECASE))
            has_sec_in_code = bool(re.search(r'\bSEC(?:TION)?\b', base_code, re.IGNORECASE))
            title_upper = title.upper() if title else ""
            has_part_in_title = bool(re.search(r'\bPART\s*\d+', title_upper))
            has_sec_in_title = bool(re.search(r'\bSEC(?:TION)?\s*\d+', title_upper))
            is_malformed = (has_part_in_title and not has_part_in_code) or (has_sec_in_title and not has_sec_in_code)
            if is_malformed:
                continue
            
            if year:
                self.strict_index[base_code].append((year, code))
                self.root_index[root_code].append((year, code))
                
        # Sort and count
        multi = set()
        for k in self.strict_index:
            self.strict_index[k].sort(key=lambda x: x[0], reverse=True)
            if len(self.strict_index[k]) > 1:
                multi.add(k)
                
        self.multi_edition_count = len(multi)
        self.build_time_ms = int((time.time() - start) * 1000)
        print(f"[EditionResolver] Built index in {self.build_time_ms}ms. {self.multi_edition_count} strict base codes have multiple editions.")
            
    def resolve(self, is_code: str) -> dict:
        parts = is_code.split(":")
        base_code = parts[0].strip().upper()
        
        year = None
        if len(parts) >= 2:
            ymatch = re.search(r'\d{4}', parts[1])
            if ymatch:
                year = int(ymatch.group(0))
                
        if not year:
            return {
                "base_code": base_code,
                "this_edition": None,
                "editions_in_registry": [],
                "later_edition_available": None,
                "state": "no_edition_data"
            }
            
        strict_editions = self.strict_index.get(base_code, [])
        editions_in_registry = [str(y) for y, _ in strict_editions]
        
        if strict_editions and strict_editions[0][0] > year:
            return {
                "base_code": base_code,
                "this_edition": str(year),
                "editions_in_registry": editions_in_registry,
                "later_edition_available": strict_editions[0][1],
                "state": "later_edition_exists"
            }
            
        this_has_part = bool(re.search(r'\bPART\b', base_code, re.IGNORECASE))
        if not this_has_part:
            rmatch = re.match(r'^(IS\s*\d+)\b', base_code, re.IGNORECASE)
            root_code = rmatch.group(1).upper() if rmatch else base_code
            root_editions = self.root_index.get(root_code, [])
            
            valid_restructured = []
            for y, c in root_editions:
                if y > year:
                    c_base = c.split(":")[0].strip().upper()
                    c_has_part = bool(re.search(r'\bPART\b', c_base, re.IGNORECASE))
                    if c_has_part:
                        valid_restructured.append((y, c))
                        
            if valid_restructured:
                valid_restructured.sort(key=lambda x: x[0], reverse=True)
                all_root_editions = sorted(list(set(str(y) for y, _ in root_editions)), reverse=True)
                return {
                    "base_code": base_code,
                    "this_edition": str(year),
                    "editions_in_registry": all_root_editions,
                    "later_edition_available": valid_restructured[0][1],
                    "state": "restructured_edition_exists"
                }
            
        return {
            "base_code": base_code,
            "this_edition": str(year),
            "editions_in_registry": editions_in_registry,
            "later_edition_available": None,
            "state": "latest_in_registry"
        }

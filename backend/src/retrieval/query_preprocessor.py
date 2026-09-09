"""Adaptive Query Preprocessor for Indian Standards Recommendation.

Solves vector dilution and lexical pollution by:
1. Dynamically stripping conversational noise, procurement boilerplate, and inquiry templates.
2. Mapping commercial/industry trade terms to canonical Bureau of Indian Standards (BIS) technical terminology.
3. Extracting exact engineering constraints (grades, parts, materials, direct IS codes).
4. Accurately classifying intent (SPECIFICATION, TEST_METHOD, CODE_OF_PRACTICE).
5. Producing dual representations:
   - cleaned_query: Minimal, noise-free technical text for dense embedding (FAISS).
   - bm25_expanded_query: Technical synonym & domain-augmented text for lexical search (BM25).
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProcessedQuery:
    raw_query: str
    cleaned_query: str
    bm25_expanded_query: str
    intent: str  # 'SPECIFICATION' | 'TEST_METHOD' | 'CODE_OF_PRACTICE'
    detected_grades: set[str] = field(default_factory=set)
    detected_parts: set[str] = field(default_factory=set)
    detected_materials: set[str] = field(default_factory=set)
    direct_is_codes: list[str] = field(default_factory=list)


# Conversational prefixes and inquiry boilerplate to strip
NOISE_PREFIX_PATTERNS = [
    r"^(?:hello|hi|hey|good morning|good afternoon|good evening|please|kindly|can you|could you)\b[\s,]*",
    r"^(?:tell me|can you tell me|could you tell me|let me know)\s+(?:which|what)?\s*(?:standard|code|norm)?\s*(?:we should follow|to follow|to use|is required|covers|applies to)?\s*(?:for)?\s*",
    r"^(?:which standard should we follow for|which code to follow for|which standard to use for|standard for|code for)\s*",
    r"^(?:we are|our company is|we operate as|i am)\s+(?:a\s+)?(?:small|medium|large|prominent|leading)?\s*(?:enterprise|company|firm|contractor|builder|manufacturer|distributor|supplier|agency|plant)?\s*",
    r"^(?:shifting to|setting up|planning to|engaged in|working on|looking to|starting|manufacturing|producing|procuring|supplying|installing|ordering|purchasing)\b[\s,]*",
    r"^(?:i need to|we need to|we want to|we require|we are looking for|looking for|require|need)\s+(?:comply with|find|know|procure|order|source|identify|get)?\s*",
    r"^(?:what is the|which is the|tell me the|give me the|which)\s+(?:official|applicable|relevant|governing|mandatory|current|indian|bis)?\s*(?:standard|specification|code|norm|regulation)?\s*(?:for|covering|governing|outlining|detailing|pertaining to)?\s*",
    r"^(?:which\s+(?:bis|indian)?\s*standard\s+(?:covers|applies to|governs|details|outlines|specifies|is applicable to))\s*",
    r"^(?:as per bis|according to indian standards|under bis norms|for public procurement|on gem portal)\b[\s,]*",
]

NOISE_SUFFIX_PATTERNS = [
    r"(?:\s*(?:which\s+(?:bis|indian)?\s*standard\s+(?:covers|governs|applies|is applicable).*?|"
    r"what\s+is\s+the\s+(?:applicable|relevant)\s+standard.*?|"
    r"what\s+standard\s+(?:outlines|governs|covers|applies).*?|"
    r"which\s+standard\s+governs.*?|"
    r"as per indian standards\??|"
    r"according to bis\??|"
    r"can you suggest\??|"
    r"please suggest\??|"
    r"for our product\??|"
    r"for this requirement\??))\s*$",
]

# BIS Domain Taxonomy: Maps informal/trade terms to canonical standard vocabulary
DOMAIN_SYNONYMS: dict[str, list[str]] = {
    # Cement types
    "portland slag cement": ["IS 455", "portland slag cement", "granulated slag", "iron blastfurnace"],
    "slag cement": ["IS 455", "portland slag cement", "slag"],
    "supersulphated cement": ["IS 6909", "supersulphated cement", "marine works", "aggressive water", "sulphate resistant"],
    "sulphate resisting cement": ["IS 12330", "sulphate resisting portland cement", "tricalcium aluminate"],
    "calcined clay": ["IS 1489 (Part 2)", "portland pozzolana cement", "calcined clay based"],
    "fly ash cement": ["IS 1489 (Part 1)", "portland pozzolana cement", "fly ash based", "ppc"],
    "ppc": ["IS 1489", "portland pozzolana cement", "fly ash", "calcined clay"],
    "opc 33": ["IS 269", "ordinary portland cement 33 grade"],
    "33 grade": ["IS 269", "ordinary portland cement 33 grade"],
    "opc 43": ["IS 8112", "43 grade ordinary portland cement"],
    "43 grade": ["IS 8112", "43 grade ordinary portland cement"],
    "opc 53": ["IS 12269", "53 grade ordinary portland cement"],
    "53 grade": ["IS 12269", "53 grade ordinary portland cement"],
    "white cement": ["IS 8042", "white portland cement", "decorative architectural"],
    "white portland cement": ["IS 8042", "white portland cement", "decorative"],
    "rapid hardening": ["IS 8041", "rapid hardening portland cement", "high early strength"],
    "hydrophobic cement": ["IS 8043", "hydrophobic portland cement"],
    "masonry cement": ["IS 3466", "masonry cement", "mortar", "non structural"],

    # Steel & Reinforcement
    "tmt": ["IS 1786", "high strength deformed steel bars", "concrete reinforcement", "fe 500d", "fe 415", "fe 550"],
    "tmt bars": ["IS 1786", "high strength deformed steel bars", "concrete reinforcement"],
    "saria": ["IS 1786", "high strength deformed steel bars", "concrete reinforcement"],
    "rebar": ["IS 1786", "high strength deformed steel bars", "concrete reinforcement"],
    "reinforcing bars": ["IS 1786", "high strength deformed steel bars", "concrete reinforcement"],
    "structural steel": ["IS 2062", "steel for general structural purposes", "beams", "angles", "channels"],
    "mild steel": ["IS 432", "mild steel bars", "IS 2062"],

    # Concrete & Masonry
    "rcc": ["IS 456", "code of practice for plain and reinforced concrete"],
    "reinforced concrete": ["IS 456", "plain and reinforced concrete", "code of practice"],
    "plain concrete": ["IS 456", "plain and reinforced concrete"],
    "aggregates": ["IS 383", "coarse and fine aggregates from natural sources for concrete"],
    "coarse aggregate": ["IS 383", "coarse and fine aggregates"],
    "fine aggregate": ["IS 383", "coarse and fine aggregates"],
    "concrete blocks": ["IS 2185", "concrete masonry units", "hollow and solid"],
    "lightweight concrete blocks": ["IS 2185 (Part 2)", "lightweight concrete masonry blocks"],
    "autoclaved cellular concrete": ["IS 2185 (Part 3)", "autoclaved aerated concrete blocks"],
    "concrete pipes": ["IS 458", "precast concrete pipes with and without reinforcement", "water mains"],
    "cable covers": ["IS 5820", "precast concrete cable covers"],

    # Pipes & Plumbing
    "hdpe pipes": ["IS 4984", "IS 14333", "high density polyethylene pipes", "water supply", "sewerage"],
    "upvc pipes": ["IS 4985", "unplasticized pvc pipes", "potable water supply"],
    "pvc pipes": ["IS 4985", "unplasticized pvc pipes"],
    "ductile iron pipes": ["IS 1536", "centrifugally cast ductile iron pipes", "water gas sewage"],
    "cast iron pipes": ["IS 1536", "IS 3989", "cast iron pipes"],

    # Water, Roofing & Waterproofing
    "drinking water": ["IS 10500", "drinking water specification", "potable water"],
    "potable water": ["IS 10500", "drinking water specification"],
    "asbestos sheets": ["IS 459", "corrugated and semi-corrugated asbestos cement sheets", "roofing cladding"],
    "roofing sheets": ["IS 459", "corrugated asbestos cement sheets"],
    "mastic asphalt": ["IS 1195", "bitumen mastic for flooring"],
    "bitumen flooring": ["IS 1195", "bitumen mastic for flooring"],
    "roof waterproofing": ["IS 3037", "bitumen mastic for use in water-proofing of roofs"],
    "damp proofing": ["IS 5871", "bitumen mastic for tanking and damp-proofing"],
    "waterproofing compound": ["IS 2645", "integral cement water-proofing compounds"],

    # Structural & Seismic Codes
    "earthquake": ["IS 1893", "criteria for earthquake resistant design of structures", "seismic forces"],
    "seismic": ["IS 1893", "earthquake resistant design of structures", "IS 13920", "ductile detailing"],
    "ductile detailing": ["IS 13920", "ductile design and detailing of reinforced concrete structures"],
    "wind load": ["IS 875 (Part 3)", "code of practice for design loads for buildings", "wind loads"],
    "design loads": ["IS 875", "design loads other than earthquake for buildings"],
}

# Distinctive Materials to guard against mutual cross-contamination
MATERIAL_GROUPS: dict[str, set[str]] = {
    "slag_cement": {"portland slag cement", "slag cement", "blast furnace slag"},
    "calcined_clay": {"calcined clay", "calcined clay based"},
    "fly_ash": {"fly ash based", "flyash"},
    "supersulphated": {"supersulphated cement", "super sulphated"},
    "white_cement": {"white portland cement", "white cement"},
    "masonry_cement": {"masonry cement"},
    "asbestos_sheets": {"asbestos cement sheets", "corrugated asbestos"},
    "concrete_pipes": {"precast concrete pipes", "concrete pipes"},
    "concrete_blocks": {"concrete masonry blocks", "lightweight concrete masonry", "concrete blocks"},
    "aggregates": {"coarse and fine aggregates", "natural aggregates for concrete"},
    "drinking_water": {"drinking water", "potable water"},
    "deformed_bars": {"high strength deformed steel", "tmt", "rebar", "fe 500"},
}


class AdaptiveQueryPreprocessor:
    """Preprocesses and enriches queries for high-precision standards matching."""

    @staticmethod
    def strip_conversational_noise(query: str) -> str:
        """Removes multi-pattern conversational fluff iteratively."""
        text = query.strip()

        # Repeatedly strip known prefixes
        changed = True
        while changed:
            original = text
            for pattern in NOISE_PREFIX_PATTERNS:
                text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
            if text == original:
                changed = False

        # Repeatedly strip known suffixes
        for pattern in NOISE_SUFFIX_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()

        # Remove trailing question marks or punctuation
        text = re.sub(r"[?!.,;]+$", "", text).strip()

        # If over-stripped, fallback to original query
        if len(text) < 4:
            return query.strip()
        return text

    @staticmethod
    def detect_intent(query: str) -> str:
        """Determines whether query targets a SPECIFICATION, TEST_METHOD, or CODE_OF_PRACTICE."""
        q = query.lower()
        if any(w in q for w in [
            "method of test", "testing", "sampling", "determination", "analysis",
            "laboratory test", "chemical analysis", "physical test", "how to test"
        ]):
            return "TEST_METHOD"
        if any(w in q for w in [
            "code of practice", "design criteria", "seismic forces", "ductile detailing",
            "wind loads", "dead loads", "imposed loads", "structural design", "installation practice"
        ]):
            return "CODE_OF_PRACTICE"
        return "SPECIFICATION"

    @staticmethod
    def extract_grades(text: str) -> set[str]:
        """Extracts numerical grade identifiers."""
        text_lower = text.lower()
        grades = set()
        for pattern in [
            r"\b(?:33|43|53)\s*grade\b",
            r"\bgrade\s*(?:33|43|53)\b",
            r"\bfe\s*(?:415|500|550|600)[d]?\b",
            r"\be\s*(?:250|300|350|410)\b",
            r"\bpe\s*(?:63|80|100)\b",
            r"\bm\s*(?:15|20|25|30|35|40|45|50|60)\b",
        ]:
            for m in re.finditer(pattern, text_lower):
                grades.add(re.sub(r"\s+", "", m.group(0)))
        return grades

    @staticmethod
    def extract_parts(text: str) -> set[str]:
        """Extracts standard part specifiers (e.g., 'part 1', 'part 2')."""
        parts = set()
        for m in re.finditer(r"\bpart\s*(\d+)\b", text.lower()):
            parts.add(f"part{m.group(1)}")
        return parts

    @staticmethod
    def extract_direct_is_codes(query: str) -> list[str]:
        """Finds explicit standard numbers mentioned in the query."""
        direct = []
        is_pattern = re.compile(r"\b(?:is|IS)[\s:]*([0-9]+(?:\s*(?:\([^\)]+\)|part\s*[0-9]+))?)\b", re.IGNORECASE)
        for m in is_pattern.finditer(query):
            direct.append(f"IS {m.group(1)}".strip())
        return direct

    @staticmethod
    def detect_materials(text: str) -> set[str]:
        """Identifies specific technical material categories to prevent cross-bleeding."""
        t = text.lower()
        detected = set()
        for mat_key, patterns in MATERIAL_GROUPS.items():
            for p in patterns:
                if p in t:
                    detected.add(mat_key)
                    break
        return detected

    @classmethod
    def expand_bm25_query(cls, cleaned_query: str, detected_grades: set[str], detected_parts: set[str]) -> str:
        """Enriches the query with canonical BIS terminology for BM25 sparse retrieval."""
        q_lower = cleaned_query.lower()
        expansions = [cleaned_query]

        # Check domain dictionary
        matched_keys = 0
        for keyword, bis_terms in DOMAIN_SYNONYMS.items():
            # Whole word or phrase matching
            if re.search(r"\b" + re.escape(keyword) + r"\b", q_lower):
                expansions.extend(bis_terms)
                matched_keys += 1
                if matched_keys >= 4:
                    break

        # Re-inject detected grades and parts for high BM25 term weighting
        for g in detected_grades:
            expansions.append(g)
        for p in detected_parts:
            expansions.append(p)

        # De-duplicate words while maintaining order
        words = []
        seen = set()
        for phrase in expansions:
            for w in phrase.split():
                w_clean = re.sub(r"[^\w\-]", "", w).strip()
                if w_clean and w_clean.lower() not in seen:
                    seen.add(w_clean.lower())
                    words.append(w_clean)

        return " ".join(words)

    @classmethod
    def process(cls, query: str, use_cloud_llm: bool = False) -> ProcessedQuery:
        """Main entry point: processes a raw query into an adaptive retrieval representation."""
        # 1. Strip conversational fluff
        cleaned = cls.strip_conversational_noise(query)

        # 2. Extract technical entities and constraints
        intent = cls.detect_intent(query)
        grades = cls.extract_grades(query) | cls.extract_grades(cleaned)
        parts = cls.extract_parts(query) | cls.extract_parts(cleaned)
        direct_codes = cls.extract_direct_is_codes(query)
        materials = cls.detect_materials(query) | cls.detect_materials(cleaned)

        # 3. Build BM25 expanded query
        bm25_expanded = cls.expand_bm25_query(cleaned, grades, parts)

        # 4. Optional Cloud LLM Deconstruction for complex queries
        if use_cloud_llm and os.getenv("GEMINI_API_KEY"):
            try:
                from google import genai
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                prompt = (
                    f"Extract only the core civil/materials technical keywords and any Bureau of Indian Standards (IS) "
                    f"code mentioned or relevant for: '{query}'. Reply in 1 comma-separated line."
                )
                resp = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                if resp.text:
                    llm_terms = [t.strip() for t in resp.text.split(",") if t.strip()]
                    bm25_expanded += " " + " ".join(llm_terms[:6])
            except Exception:
                pass

        return ProcessedQuery(
            raw_query=query,
            cleaned_query=cleaned,
            bm25_expanded_query=bm25_expanded,
            intent=intent,
            detected_grades=grades,
            detected_parts=parts,
            detected_materials=materials,
            direct_is_codes=direct_codes,
        )

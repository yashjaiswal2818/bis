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

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Government Procurement Item Master (CPWD DSR, GeM, MoRTH schedule specifications)
GOVERNMENT_ITEM_MASTER: list[dict[str, Any]] = []
_ITEM_MASTER_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "government_procurement_item_master.json"
if _ITEM_MASTER_PATH.exists():
    try:
        GOVERNMENT_ITEM_MASTER = json.loads(_ITEM_MASTER_PATH.read_text(encoding="utf-8"))
    except Exception as _e:
        print(f"[Warning] Failed to load government procurement item master: {_e}")


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
    matched_government_item: dict[str, Any] | None = None


# Conversational prefixes and inquiry boilerplate to strip (English, Hindi, and Natural Language)
NOISE_PREFIX_PATTERNS = [
    # English Natural Language Inquiries
    r"^(?:hello|hi|hey|good morning|good afternoon|good evening|please|kindly|can you|could you)\b[\s,]*",
    r"^(?:which|what)\s+(?:bis\s+|indian\s+)?(?:standard|specification|code|norm|is\s+code)?\s+(?:should|do|can|must)\s+(?:we|i|one)\s+(?:follow|use|refer\s+to|apply)\s+(?:for|to)?\s*",
    r"^(?:tell me|can you tell me|could you tell me|let me know)\s+(?:which|what)?\s*(?:standard|code|norm)?\s*(?:we should follow|to follow|to use|is required|covers|applies to)?\s*(?:for)?\s*",
    r"^(?:which standard should we follow for|which code to follow for|which standard to use for|standard for|code for)\s*",
    r"^(?:we are|our company is|we operate as|i am)\s+(?:a\s+)?(?:small|medium|large|prominent|leading)?\s*(?:enterprise|company|firm|contractor|builder|manufacturer|distributor|supplier|agency|plant)?\s*",
    r"^(?:shifting to|setting up|planning to|engaged in|working on|looking to|starting|manufacturing|producing|procuring|supplying|installing|ordering|purchasing)\b[\s,]*",
    r"^(?:i need to|we need to|we want to|we require|we are looking for|looking for|require|need)\s+(?:comply with|find|know|procure|order|source|identify|get)?\s*",
    r"^(?:what is the|which is the|tell me the|give me the|which)\s+(?:official|applicable|relevant|governing|mandatory|current|indian|bis)?\s*(?:standard|specification|code|norm|regulation)?\s*(?:for|covering|governing|outlining|detailing|pertaining to)?\s*",
    r"^(?:which\s+(?:bis|indian)?\s*standard\s+(?:covers|applies to|governs|details|outlines|specifies|is applicable to))\s*",
    r"^(?:what are the\s+(?:testing methods|test requirements|testing standards|safety norms|installation codes|standards)\s+for\s+)",
    r"^(?:is there any\s+(?:mandatory\s+)?(?:standard|is code|qco)\s+for\s+)",
    r"^(?:as per bis|according to indian standards|under bis norms|for public procurement|on gem portal)\b[\s,]*",
    r"^(?:tender\s+specification\s+for|tender\s+for|notice\s+inviting\s+tender\s+for|nit\s+for|bid\s+for)\s*",
    r"^(?:procurement\s+of|supply\s+of|purchase\s+of|work\s+order\s+for)\s*",
    r"^(?:the\s+contractor\s+shall\s+(?:ensure|supply|provide|use|execute))\s*",
    r"^(?:turnkey\s+project\s+for|contract\s+for)\s*",

    # Hindi / Devanagari Conversational Prefixes
    r"^(?:कृपया|नमस्ते|क्या आप|मुझे|हमें)\b[\s,]*",
    r"^(?:बताएं कि|बताइए कि|जानना चाहते हैं कि|बताएं|ढूंढें|सजेस्ट करें)\s*",
    r"^(?:कौन\s+सा\s+मानक|किस\s+मानक|कौन\s+सा\s+कोड|किस\s+कोड|मानक\s+बताएं|कोड\s+बताएं)\s*(?:लागू\s+होता\s+है|चाहिए|फॉलो\s+करें|उपयोग\s+करें)?\s*(?:के\s+लिए)?\s*",
    r"^(?:सरकारी\s+खरीद\s+के\s+लिए|टेंडर\s+के\s+लिए|खरीदने\s+के\s+लिए|सप्लाई\s+के\s+लिए)\s*",
    r"^(?:हमें\s+खरीदना\s+है|हम\s+खरीदना\s+चाहते\s+हैं|हम\s+आर्डर\s+देना\s+चाहते\s+हैं)\s*",
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
    r"for this requirement\??|"
    r"in government tender\??|"
    r"on gem portal\??|"
    r"के लिए कौन सा मानक है\??|"
    r"का भारतीय मानक क्या है\??|"
    r"लागू होता है\??|"
    r"बताएं\??|"
    r"मानक चाहिए\??))\s*$",
]

# BIS Domain Taxonomy: Maps informal, trade, Hindi (Devanagari), and Hinglish terms to canonical standard vocabulary
DOMAIN_SYNONYMS: dict[str, list[str]] = {
    # Multilingual Indic: Cables & Electricals (Hindi & Hinglish)
    "बिजली के तार": ["IS 694", "electric cables", "pvc insulated cables", "building wiring", "1100V"],
    "बिजली का तार": ["IS 694", "electric cables", "pvc insulated cables"],
    "बिजली के केबल": ["IS 694", "IS 7098", "electric power cables", "cables"],
    "bijli ke taar": ["IS 694", "pvc insulated electric cables", "building wiring", "1100V"],
    "bijli ka taar": ["IS 694", "pvc insulated electric cables"],
    "bijli ke cable": ["IS 694", "IS 7098", "electric power cables"],
    "power cable": ["IS 694", "IS 7098", "electric cables", "1100V"],
    "वितरण ट्रांसफार्मर": ["IS 1180", "three phase distribution transformers"],
    "ट्रांसफार्मर": ["IS 1180", "three phase distribution transformers"],
    "पंखे": ["IS 374", "electric ceiling fans and regulators"],
    "बिजली का पंखा": ["IS 374", "electric ceiling fans"],
    "bijli ka pankha": ["IS 374", "electric ceiling fans and regulators"],
    "अर्थिंग": ["IS 3043", "code of practice for earthing", "grounding"],
    "स्विचगियर": ["IS/IEC 60947", "low-voltage switchgear and controlgear"],
    "एलटी पैनल": ["IS/IEC 61439", "IS 8623", "low-voltage switchgear", "distribution board"],

    # Multilingual Indic: Gold & Hallmarking (Hindi & Hinglish)
    "सोने के आभूषण": ["IS 1417", "gold and gold alloys jewellery artefacts", "hallmarking", "huid"],
    "सोने के गहने": ["IS 1417", "gold and gold alloys jewellery artefacts", "hallmarking", "huid"],
    "सोना": ["IS 1417", "gold and gold alloys", "hallmarking"],
    "हॉलमार्किंग": ["IS 1417", "hallmarking with 6-digit huid", "gold jewellery"],
    "हॉलमार्क": ["IS 1417", "hallmarking", "huid"],
    "sone ke gehne": ["IS 1417", "gold jewellery and artefacts", "hallmarking", "huid"],
    "sone ke aabhushan": ["IS 1417", "gold jewellery", "hallmarking"],
    "sona hallmarking": ["IS 1417", "gold jewellery", "hallmarking", "huid"],
    "चांदी": ["IS 2112", "silver and silver alloys jewellery artefacts", "hallmarking"],
    "चांदी के बर्तन": ["IS 2112", "silver artefacts and jewellery"],
    "chandi": ["IS 2112", "silver alloys and jewellery"],

    # Multilingual Indic: Cement, Concrete & Construction (Hindi & Hinglish)
    "सीमेंट": ["IS 269", "IS 1489", "IS 455", "ordinary portland cement", "portland pozzolana cement"],
    "siment": ["IS 269", "IS 1489", "ordinary portland cement"],
    "कंक्रीट": ["IS 456", "plain and reinforced concrete", "code of practice"],
    "kankrit": ["IS 456", "plain and reinforced concrete"],
    "छत ढलाई": ["IS 456", "plain and reinforced concrete", "rcc slab construction"],
    "chhat dhalai": ["IS 456", "reinforced cement concrete structural slab"],
    "प्लास्टर": ["IS 1661", "code of practice for application of cement and lime plasters"],
    "plaster": ["IS 1661", "application of cement and lime plasters"],

    # Multilingual Indic: Steel & Reinforcement (Hindi & Hinglish)
    "लोहा": ["IS 1786", "IS 2062", "structural steel", "deformed steel bars"],
    "सरिया": ["IS 1786", "high strength deformed steel bars", "concrete reinforcement", "fe 500d", "tmt"],
    "लोहे का सरिया": ["IS 1786", "high strength deformed steel bars", "tmt bars", "fe 500d"],
    "lohe ka sariya": ["IS 1786", "high strength deformed steel bars", "tmt", "fe 500d"],
    "sariya tmt": ["IS 1786", "high strength deformed steel bars", "tmt"],
    "संरचनात्मक स्टील": ["IS 2062", "steel for general structural purposes", "beams", "angles"],

    # Multilingual Indic: Water & Sanitation (Hindi & Hinglish)
    "पीने का पानी": ["IS 10500", "drinking water specification", "potable water"],
    "पीने का साफ पानी": ["IS 10500", "drinking water quality specification"],
    "peene ka paani": ["IS 10500", "drinking water quality specification"],
    "peene ka pani": ["IS 10500", "drinking water specification"],
    "पानी की गुणवत्ता": ["IS 10500", "drinking water physical chemical bacteriological parameters"],
    "जल गुणवत्ता": ["IS 10500", "drinking water quality specifications"],
    "पाइप": ["IS 4984", "IS 4985", "IS 1536", "pipes for water supply"],
    "पानी का पाइप": ["IS 4984", "IS 4985", "pipes for water supply"],
    "paani ka pipe": ["IS 4984", "IS 4985", "pipes for water supply"],
    "सीवेज": ["IS 458", "precast concrete pipes", "sewerage and drainage"],
    "नाली": ["IS 458", "precast concrete pipes for drainage and sewerage"],

    # Multilingual Indic: Safety, PPE & Fire (Hindi & Hinglish)
    "हेलमेट": ["IS 4151", "protective helmets for two wheeler riders"],
    "helmet": ["IS 4151", "protective helmets for two wheeler riders"],
    "अग्निशमन": ["IS 1641", "IS 2190", "fire safety in buildings", "fire extinguisher"],
    "आग से सुरक्षा": ["IS 1641", "IS 1642", "fire safety of buildings"],
    "aag se suraksha": ["IS 1641", "fire safety in buildings"],
    "सुरक्षा जूते": ["IS 15298", "personal protective equipment footwear", "safety footwear"],
    "safety shoes": ["IS 15298", "safety footwear"],
    "भूकंप": ["IS 1893", "earthquake resistant design of structures", "seismic forces"],
    "bhukamp": ["IS 1893", "earthquake resistant design of structures"],

    # Multilingual Indic: Electronics, Solar & Battery (Hindi & Hinglish)
    "सौर पैनल": ["IS 14286", "IS/IEC 61730", "terrestrial photovoltaic modules", "solar pv"],
    "सौर ऊर्जा": ["IS 14286", "solar photovoltaic modules"],
    "solar panel": ["IS 14286", "solar photovoltaic modules"],
    "बैटरी": ["IS 16046", "secondary lithium cells and batteries", "compulsory registration scheme"],
    "एलईडी बल्ब": ["IS 16102", "self-ballasted led lamps for general lighting"],
    "led bulb": ["IS 16102", "self-ballasted led lamps"],

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
    "ready mixed concrete": ["IS 4926", "ready-mixed concrete", "ready mixed concrete", "rmc"],
    "ready-mixed concrete": ["IS 4926", "ready-mixed concrete", "ready mixed concrete", "rmc"],
    "rmc": ["IS 4926", "ready-mixed concrete", "code of practice ready-mixed concrete"],
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

    # Testing Methods
    "concrete testing": ["IS 516", "IS 1199", "methods of tests for strength of concrete", "sampling and analysis of concrete"],
    "compressive strength of concrete": ["IS 516", "methods of tests for strength of concrete", "compressive strength"],
    "tensile testing of metals": ["IS 1608", "metallic materials tensile testing"],
    "tensile test": ["IS 1608", "metallic materials tensile testing"],
    "testing of cement": ["IS 4031", "methods of physical tests for hydraulic cement"],

    # Safety & Personal Protective Equipment
    "safety footwear": ["IS 15298", "personal protective equipment footwear", "safety footwear"],
    "safety shoes": ["IS 15298", "personal protective equipment footwear", "safety footwear"],
    "fire safety": ["IS 1641", "IS 1642", "IS 1643", "code of practice for fire safety of buildings"],
    "fire safety in buildings": ["IS 1641", "IS 1642", "IS 1643", "code of practice for fire safety of buildings"],

    # Structural & Seismic Codes
    "structural steel design": ["IS 800", "code of practice for general construction in steel", "structural steel design"],
    "steel design": ["IS 800", "code of practice for general construction in steel"],
    "earthquake": ["IS 1893", "criteria for earthquake resistant design of structures", "seismic forces"],
    "seismic": ["IS 1893", "earthquake resistant design of structures", "seismic forces"],
    "earthquake resistant design": ["IS 1893", "criteria for earthquake resistant design of structures", "seismic forces"],
    "seismic design": ["IS 1893", "criteria for earthquake resistant design of structures", "seismic forces"],
    "ductile detailing": ["IS 13920", "ductile design and detailing of reinforced concrete structures"],
    "wind load": ["IS 875 (Part 3)", "code of practice for design loads for buildings", "wind loads"],
    "design loads": ["IS 875", "design loads other than earthquake for buildings"],

    # Electrotechnical (ETD)
    "energy meter": ["IS 13779", "IS 14697", "IS 15884", "ac static watt-hour meters", "electricity meters"],
    "static energy meters": ["IS 13779", "IS 14697", "ac static watt-hour meters"],
    "electricity meter": ["IS 13779", "IS 14697", "ac static watt-hour meters"],
    "distribution transformer": ["IS 1180", "three phase distribution transformers", "copper wound"],
    "power transformer": ["IS 2026", "power transformers"],
    "ceiling fan": ["IS 374", "electric ceiling fans and regulators"],
    "earthing": ["IS 3043", "code of practice for earthing", "grounding"],
    "switchgear": ["IS/IEC 60947", "low-voltage switchgear and controlgear", "circuit breakers"],
    "circuit breaker": ["IS/IEC 60947-2", "IS/IEC 60898", "circuit breakers"],
    "electric cables": ["IS 694", "IS 7098", "pvc insulated cables", "xlpe cables"],

    # Electronics & Information Technology (LITD / CRS)
    "lithium battery": ["IS 16046", "secondary cells and batteries containing alkaline or other non-acid electrolytes"],
    "lithium cells": ["IS 16046", "secondary lithium cells and batteries for portable applications"],
    "secondary cells": ["IS 16046", "secondary lithium cells and batteries"],
    "led lamp": ["IS 16102", "self-ballasted led lamps for general lighting services"],
    "led lamps": ["IS 16102", "self-ballasted led lamps for general lighting services"],
    "led luminaire": ["IS 10322", "luminaires general requirements"],
    "it equipment": ["IS 13252", "information technology equipment safety general requirements"],
    "uninterruptible power system": ["IS 16242", "uninterruptible power systems ups"],

    # Textiles (TXD)
    "firefighter clothing": ["IS 16890", "IS 15748", "protective clothing for firefighters"],
    "protective clothing": ["IS 16890", "IS 15748", "protective clothing"],
    "surgical mask": ["IS 16289", "medical face masks specification"],
    "face mask": ["IS 16289", "medical face masks specification"],
    "jute bags": ["IS 12650", "IS 16186", "jute bags for packing foodgrains"],
    "geotextiles": ["IS 16391", "geosynthetics geotextiles for subsurface drainage"],

    # Chemical, Paints & Petroleum (CHD / PCD)
    "synthetic enamel": ["IS 2932", "enamel synthetic exterior interior"],
    "enamel paint": ["IS 2932", "enamel synthetic exterior interior"],
    "caustic soda": ["IS 252", "caustic soda pure and technical"],
    "bitumen": ["IS 73", "paving bitumen viscosity grade"],
    "lpg cylinder": ["IS 3196", "welded low carbon steel cylinders for lpg"],

    # Food & Agriculture (FAD)
    "packaged drinking water": ["IS 14543", "packaged drinking water other than natural mineral water"],
    "mineral water": ["IS 13428", "packaged natural mineral water"],
    "agricultural tractor": ["IS 12239", "IS 5994", "agricultural tractors guidelines for safety devices and safety requirements"],
    "agricultural tractors": ["IS 12239", "IS 5994", "agricultural tractors guidelines for safety devices and safety requirements"],

    # Mechanical Engineering (MED)
    "centrifugal pump": ["IS 1520", "IS 6595", "horizontal centrifugal pumps for clear cold water"],
    "centrifugal pumps": ["IS 1520", "IS 6595", "horizontal centrifugal pumps for agricultural purposes"],
    "gate valve": ["IS 14846", "IS 778", "sluice valves for water works purposes"],
    "sluice valve": ["IS 14846", "sluice valves for water works purposes"],

    # Transport Engineering (TED)
    "helmets": ["IS 4151", "protective helmets for two wheeler riders"],
    "motorcycle helmet": ["IS 4151", "protective helmets for two wheeler riders"],
    "automotive glass": ["IS 2553", "safety glass for road transport vehicles"],
    "safety glass": ["IS 2553", "safety glass for road transport vehicles windscreens"],
    "tyres": ["IS 15633", "IS 15636", "pneumatic tyres for automotive vehicles"],

    # Consumer Affairs / Precious Metals (DoCA)
    "gold hallmarking": ["IS 1417", "gold and gold alloys jewellery artefacts", "hallmarking", "huid"],
    "gold jewellery": ["IS 1417", "gold and gold alloys jewellery artefacts", "hallmarking"],
    "silver hallmarking": ["IS 2112", "silver and silver alloys jewellery artefacts"],
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
    "earthing": {"earthing", "grounding", "earth electrode", "earth electrodes"},
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
            "method of test", "methods of test", "test method", "test methods", "testing",
            "sampling", "determination", "analysis", "laboratory test", "chemical analysis",
            "physical test", "how to test", "tests for", "test for", "tensile test",
            "compressive test", "slump test", "cube test", "bend test", "impact test",
            "abrasion test", "soundness test", "penetration test", "flash point test",
            "परीक्षण", "जांच", "टेस्ट", "सैंपलिंग", "गुणवत्ता जांच"
        ]):
            return "TEST_METHOD"
        if any(w in q for w in [
            "code of practice", "design criteria", "seismic forces", "ductile detailing",
            "wind loads", "dead loads", "imposed loads", "structural design", "installation practice",
            "design of", "design code", "earthquake resistant", "seismic design",
            "earthquake design", "building code", "general construction in steel",
            "fire safety in buildings", "fire safety", "fire protection", "fire fighting",
            "electrical installation code", "safety code",
            "कोड ऑफ प्रैक्टिस", "डिजाइन", "स्थापना", "लगाने का नियम", "सुरक्षा नियम", "भूकंप रोधी"
        ]):
            return "CODE_OF_PRACTICE"
        return "SPECIFICATION"

    @staticmethod
    def extract_grades(text: str) -> set[str]:
        """Extracts numerical grade and class identifiers across English and Indic scripts."""
        text_lower = text.lower()
        # Convert Devanagari numerals if present
        devanagari_map = {'०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'}
        for d_char, a_char in devanagari_map.items():
            text_lower = text_lower.replace(d_char, a_char)

        grades = set()
        for pattern in [
            r"\b(?:33|43|53)\s*(?:grade|ग्रेड)\b",
            r"\b(?:grade|ग्रेड)\s*(?:33|43|53)\b",
            r"\b(?:fe|एफई)\s*(?:415|500|550|600)[d]?\b",
            r"\be\s*(?:250|300|350|410)\b",
            r"\bpe\s*(?:63|80|100)\b",
            r"\b(?:m|एम)\s*[-]?\s*(?:15|20|25|30|35|40|45|50|60)\b",
            r"\bvg\s*[-]?\s*(?:10|20|30|40)\b",
            r"\bclass\s*k\s*(?:7|9|12)\b",
            r"\bk\s*[-]?\s*(?:7|9)\b",
            r"\bclass\s*np\s*(?:2|3|4)\b",
            r"\bnp\s*(?:2|3|4)\b",
            r"\b(?:22k|24k|916)\b",
            r"\b(?:22|24)\s*(?:carat|karat|कैरेट|करट)\b",
            r"\b(?:1100|415)\s*(?:v|volt|volts|वोल्ट)\b",
        ]:
            for m in re.finditer(pattern, text_lower):
                g_str = re.sub(r"[\s\-]+", "", m.group(0))
                if "कैरेट" in g_str or "karat" in g_str or "carat" in g_str:
                    g_str = "22k" if "22" in g_str else "24k"
                elif "वोल्ट" in g_str or "volt" in g_str:
                    g_str = "1100v" if "1100" in g_str else "415v"
                elif "ग्रेड" in g_str:
                    g_str = g_str.replace("ग्रेड", "grade")
                elif "एम" in g_str:
                    g_str = g_str.replace("एम", "m")
                elif "एफई" in g_str:
                    g_str = g_str.replace("एफई", "fe")
                grades.add(g_str)
        return grades

    @classmethod
    def match_government_item(cls, query: str, cleaned_query: str) -> dict[str, Any] | None:
        """Deterministically matches against standard CPWD DSR / GeM / MoRTH line items using in-memory trie."""
        try:
            from src.retrieval.government_schedule_engine import GovernmentScheduleEngine
            return GovernmentScheduleEngine.get_instance().match_schedule(query, cleaned_query)
        except Exception:
            if not GOVERNMENT_ITEM_MASTER:
                return None
            candidates = [query.lower(), cleaned_query.lower()]
            for item in GOVERNMENT_ITEM_MASTER:
                aliases = item.get("aliases", [])
                for alias in aliases:
                    a_clean = alias.strip().lower()
                    pattern = r"\b" + re.escape(a_clean) + r"\b"
                    for cand in candidates:
                        if re.search(pattern, cand):
                            return item
            return None

    @staticmethod
    def extract_parts(text: str, is_query: bool = True) -> set[str]:
        """Extracts standard part specifiers (e.g., 'part 1', 'part 2', 'भाग 1') and domain subtype clues."""
        parts = set()
        for m in re.finditer(r"\b(?:part|भाग)\s*(\d+)\b", text.lower()):
            parts.add(f"part{m.group(1)}")
        if is_query:
            t_low = text.lower()
            if "lithium" in t_low and ("secondary" in t_low or "cell" in t_low or "batter" in t_low):
                parts.add("part2")  # IS 16046 (Part 2) is Lithium systems
            elif "nickel" in t_low and ("secondary" in t_low or "cell" in t_low or "batter" in t_low):
                parts.add("part1")  # IS 16046 (Part 1) is Nickel systems
            elif "calcined clay" in t_low:
                parts.add("part2")  # IS 1489 (Part 2) is Calcined clay based PPC
            elif "fly ash" in t_low and "pozzolana" in t_low:
                parts.add("part1")  # IS 1489 (Part 1) is Fly ash based PPC
            elif "fitting" in t_low and ("tubular" in t_low or "pipe" in t_low or "steel" in t_low):
                parts.add("part2")  # IS 1239 (Part 2) is Mild steel tubular fittings
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

        # Check domain dictionary with support for Indic script matching
        matched_keys = 0
        for keyword, bis_terms in DOMAIN_SYNONYMS.items():
            is_non_ascii = any(ord(c) > 127 for c in keyword)
            matched = False
            if is_non_ascii:
                matched = keyword in q_lower
            else:
                matched = bool(re.search(r"\b" + re.escape(keyword) + r"\b", q_lower))
            if matched:
                expansions.extend(bis_terms)
                matched_keys += 1
                if matched_keys >= 8:
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
        """Main entry point: processes raw/multilingual query into an adaptive retrieval representation."""
        # 1. Strip conversational fluff
        cleaned = cls.strip_conversational_noise(query)

        # 2. Extract technical entities and constraints
        intent = cls.detect_intent(query)
        grades = cls.extract_grades(query) | cls.extract_grades(cleaned)
        parts = cls.extract_parts(query) | cls.extract_parts(cleaned)
        direct_codes = cls.extract_direct_is_codes(query)
        materials = cls.detect_materials(query) | cls.detect_materials(cleaned)

        # 3. Multilingual Bridge: Enrich cleaned_query with canonical technical terms if Indic script or Hinglish terms are present
        has_non_ascii = any(ord(c) > 127 for c in query)
        q_lower = query.lower()
        bridge_terms = []
        for k, terms in DOMAIN_SYNONYMS.items():
            is_non_ascii = any(ord(c) > 127 for c in k)
            if is_non_ascii:
                if k in q_lower:
                    bridge_terms.extend(terms)
            elif any(hw in k for hw in ["bijli", "sone", "taar", "gehne", "sariya", "lohe", "peene", "paani", "pani", "chandi", "siment", "kankrit", "dhalai", "bhukamp"]):
                if re.search(r"\b" + re.escape(k) + r"\b", q_lower):
                    bridge_terms.extend(terms)
        if bridge_terms:
            unique_bridge = list(dict.fromkeys(bridge_terms))[:8]
            cleaned = f"{cleaned} {' '.join(unique_bridge)}"

        # 4. Build BM25 expanded query
        bm25_expanded = cls.expand_bm25_query(cleaned, grades, parts)

        # 4. Contextual Government Schedule Match (CPWD DSR, GeM, MoRTH)
        # Only match procurement schedule specifications if query intent matches or is neutral
        gov_item = None
        if intent == "SPECIFICATION" or any(w in query.lower() for w in ["procurement", "supply", "tender", "contract", "purchase"]):
            candidate_gov = cls.match_government_item(query, cleaned)
            if candidate_gov:
                cand_code = candidate_gov.get("is_code", "")
                conflict = False
                # Conflict guard: do not allow fly-ash PPC to override calcined-clay PPC
                if "calcined_clay" in materials and "Part 1" in cand_code:
                    conflict = True
                if "fly_ash" in materials and "Part 2" in cand_code:
                    conflict = True
                if not conflict:
                    gov_item = candidate_gov
                    c_code = gov_item.get("is_code")
                    b_code = gov_item.get("base_code")
                    if c_code:
                        bm25_expanded += f" {c_code}"
                    if b_code and b_code != c_code:
                        bm25_expanded += f" {b_code}"
                    if gov_item.get("required_grade") and not grades:
                        grades.add(gov_item["required_grade"].lower().replace(" ", ""))

        # 5. Optional Cloud LLM Deconstruction for complex queries
        # if use_cloud_llm and os.getenv("GEMINI_API_KEY"):
        #     try:
        #         from google import genai
        #         client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        #         prompt = (
        #             f"Extract only the core civil/materials technical keywords and any Bureau of Indian Standards (IS) "
        #             f"code mentioned or relevant for: '{query}'. Reply in 1 comma-separated line."
        #         )
        #         resp = client.models.generate_content(
        #             model="gemini-2.0-flash",
        #             contents=prompt,
        #         )
        #         if resp.text:
        #             llm_terms = [t.strip() for t in resp.text.split(",") if t.strip()]
        #             bm25_expanded += " " + " ".join(llm_terms[:6])
        #     except Exception:
        #         pass

        return ProcessedQuery(
            raw_query=query,
            cleaned_query=cleaned,
            bm25_expanded_query=bm25_expanded,
            intent=intent,
            detected_grades=grades,
            detected_parts=parts,
            detected_materials=materials,
            direct_is_codes=direct_codes,
            matched_government_item=gov_item,
        )

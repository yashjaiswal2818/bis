"""Categorization and Global Standard Comparison Analysis."""
import sqlite3
import re
from pathlib import Path

DB_PATH = Path("backend/data/standards_master.db")

# Extended taxonomy mapping matching BIS 15 Directorates / Technical Divisions
EXTENDED_DIVISIONS = {
    "Civil Engineering (CED)": [
        r"\b(cement|concrete|mortar|aggregates?|brick|blocks?|tiles?|timber|plywood|masonry|soil|foundation|asphalt|bitumen|roofing|doors?|windows?|earthquake|seismic|plumbing|sanitary|drainage|waterproofing|building|structural|dam|reservoir|bridge)\b"
    ],
    "Electrotechnical (ETD)": [
        r"\b(electrical|electricity|cables?|wires?|transformers?|switchgear|insulators?|generators?|motors?|voltage|relay|luminaire|substation|high\s*voltage|earthing|conductors?|lighting|batteries|power\s*system|capacitors?)\b"
    ],
    "Electronics & Information Technology (LITD / CRS)": [
        r"\b(electronics?|computer|lithium|cell|software|telecom|smart|led|microprocessor|inverter|photovoltaic|solar|audio|video|display|semiconductor|cybersecurity|data|information\s*technology|radio|television|fibre\s*optics?)\b"
    ],
    "Mechanical Engineering (MED)": [
        r"\b(boiler|valves?|pumps?|compressors?|bearings?|gears?|cranes?|hoists?|pressure\s*vessels?|turbines?|cylinders?|automotive|conveyor|tools?|dies|fasteners?|nuts?|bolts?|screws?|washers?|refrigeration|air\s*conditioning|machinery|welding)\b"
    ],
    "Metallurgical Engineering (MTD)": [
        r"\b(steel|iron|alloy|rebar|tmt|gold|silver|hallmark|castings?|wrought|aluminium|copper|brass|wire\s*mesh|zinc|lead|foundry|ferro|metallurgy|sheet\s*metal|pipes?\s*and\s*tubes?|tin|nickel|ore|corrosion)\b"
    ],
    "Chemical Engineering (CHD)": [
        r"\b(chemical|paint|varnish|acids?|fertilizers?|polymers?|plastics?|adhesives?|rubber|dyes?|cosmetics?|soaps?|detergents?|solvents?|resins?|petroleum|fuel|lubricant|grease|gas|glass|ceramic|leather|paper|pulp)\b"
    ],
    "Food & Agriculture (FAD)": [
        r"\b(drinking\s*water|food|grain|tea|coffee|milk|dairy|spices?|pesticides?|sugar|oilseeds?|flour|bakery|cereal|meat|beverages?|packaging|fish|poultry|fertilizer|edible|agrochemical|seeds?|tobacco|feed)\b"
    ],
    "Textiles (TXD)": [
        r"\b(cotton|yarn|fabric|cloth|silk|jute|wool|fibres?|geotextiles?|garments?|tarpaulin|weaving|spinning|threads?|hosiery|carpets?|nonwoven|ropes?|twines?|textile)\b"
    ],
    "Transport Engineering (TED)": [
        r"\b(railways?|locomotive|aircraft|marine|ships?|vehicles?|tyres?|brakes?|road\s*vehicles?|suspension|bicycles?|automobiles?|tractors?|airports?|harbours?)\b"
    ],
    "Medical Equipment & Hospital Planning (MHD)": [
        r"\b(medical|surgical|implants?|hospital|syringes?|orthopaedic|diagnostic|gloves?|catheter|dental|prosthetics?|rehabilitation|sterilization|anaesthetic|electromedical)\b"
    ],
    "Production & General Engineering (PGD)": [
        r"\b(gauges?|metrology|drawings?|tolerances?|limits\s*and\s*fits|sampling|inspection|measurement|instruments?|quality\s*management|ergonomics?|symbols?|terminology|glossary)\b"
    ],
    "Petroleum, Coal & Related Products (PCD)": [
        r"\b(petroleum|crude\s*oil|diesel|petrol|kerosene|bitumen|asphalt|coal|coke|wax|lubricating|natural\s*gas|lpg)\b"
    ],
    "Management & Systems (MSD)": [
        r"\b(management|environmental\s*management|occupational\s*health|safety|risk|audit|conformity|guidelines|quality\s*assurance)\b"
    ]
}

def analyze():
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    c.execute("SELECT is_code, title, scope FROM standards_registry")
    rows = c.fetchall()
    total = len(rows)
    print(f"Total Standards Analyzed: {total:,}\n")

    category_counts = {k: 0 for k in EXTENDED_DIVISIONS}
    category_counts["Other / Specialized Specifications"] = 0

    # Specific domains prioritized before generic terms
    priority_order = [
        "Civil Engineering (CED)",
        "Metallurgical Engineering (MTD)",
        "Electrotechnical (ETD)",
        "Electronics & Information Technology (LITD / CRS)",
        "Mechanical Engineering (MED)",
        "Chemical Engineering (CHD)",
        "Food & Agriculture (FAD)",
        "Textiles (TXD)",
        "Medical Equipment & Hospital Planning (MHD)",
        "Transport Engineering (TED)",
        "Petroleum, Coal & Related Products (PCD)",
        "Management & Systems (MSD)",
        "Production & General Engineering (PGD)",
    ]

    for code, title, scope in rows:
        combined = f"{code} {title} {scope}".lower()
        matched = False
        for cat in priority_order:
            patterns = EXTENDED_DIVISIONS[cat]
            if any(re.search(pat, combined) for pat in patterns):
                category_counts[cat] += 1
                matched = True
                break
        if not matched:
            category_counts["Other / Specialized Specifications"] += 1

    sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    print("=" * 80)
    print(f"{'BIS Category / Technical Division':<48} | {'Count':>8} | {'Share':>7}")
    print("=" * 80)
    for cat, cnt in sorted_cats:
        pct = (cnt / total) * 100
        print(f"{cat:<48} | {cnt:>8,d} | {pct:>6.1f}%")
    print("=" * 80)

if __name__ == "__main__":
    analyze()

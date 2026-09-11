"""Script to seed high-value canonical normative, test, safety, and installation edges into SQLite."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "standards_master.db"

EDGES = [
    # IS 694 Cables
    ("IS 694: 2010", "IS 10810 (Part 1): 1984", "NORM_TEST", "Normative Test & Sampling Method", 1, "Methods of Test for Cables - Annealing Test"),
    ("IS 694: 2010", "IS 10810 (Part 2): 1984", "NORM_TEST", "Normative Test & Sampling Method", 1, "Methods of Test for Cables - Tensile Test"),
    ("IS 694: 2010", "IS 8130: 2013", "RAW_MATERIAL", "Allied Material / Component Specification", 0, "Conductors for Insulated Electric Cables"),
    ("IS 694: 2010", "IS 5831: 1984", "RAW_MATERIAL", "Allied Material / Component Specification", 0, "PVC Insulation and Sheath of Electric Cables"),
    ("IS 694: 2010", "IS 732: 2019", "INSTALLATION", "Installation & Workmanship Code", 0, "Code of Practice for Electrical Wiring Installations"),
    ("IS 694: 2010", "IS 3043: 2018", "SAFETY", "Safety & Environmental Standard", 1, "Code of Practice for Earthing"),
    ("IS 694: 2010", "IS 1885 (Part 32): 1993", "TERMINOLOGY", "Terminology & Definitions Standard", 0, "Electrotechnical Vocabulary - Electric Cables"),
    ("IS 694: 2010", "IS 1554 (Part 1): 1988", "RELATED_PRODUCT", "Allied Co-Dependent Product Standard", 0, "PVC Insulated (Heavy Duty) Electric Cables"),
    ("IS 694: 2010", "IS 7098 (Part 1): 1988", "RELATED_PRODUCT", "Allied Co-Dependent Product Standard", 0, "Crosslinked Polyethylene Insulated Cables"),

    # IS 1786 TMT Steel Bars
    ("IS 1786: 2008", "IS 1608 (Part 1): 2018", "NORM_TEST", "Normative Test & Sampling Method", 1, "Metallic Materials - Tensile Testing"),
    ("IS 1786: 2008", "IS 1599: 2019", "NORM_TEST", "Normative Test & Sampling Method", 1, "Metallic Materials - Bend Test"),
    ("IS 1786: 2008", "IS 2502: 1963", "INSTALLATION", "Installation & Workmanship Code", 0, "Bending and Fixing of Bars for Concrete Reinforcement"),
    ("IS 1786: 2008", "IS 13920: 2016", "SAFETY", "Safety & Environmental Standard", 1, "Ductile Design and Detailing of Reinforced Concrete Structures"),
    ("IS 1786: 2008", "IS 2770 (Part 1): 1967", "NORM_TEST", "Normative Test & Sampling Method", 1, "Methods of Testing Bond in Reinforced Concrete"),
    ("IS 1786: 2008", "IS 456: 2000", "INSTALLATION", "Installation & Workmanship Code", 0, "Plain and Reinforced Concrete - Code of Practice"),

    # IS 1417 Gold Hallmarking
    ("IS 1417: 2016", "IS 1418: 2009", "NORM_TEST", "Normative Test & Sampling Method", 1, "Assaying of Gold in Gold Bullion, Gold Alloys and Gold Jewellery/Artefacts"),
    ("IS 1417: 2016", "IS 2112: 2014", "RELATED_PRODUCT", "Allied Co-Dependent Product Standard", 0, "Silver and Silver Alloys, Jewellery/Artefacts - Fineness and Marking"),
    ("IS 1417: 2016", "IS 15820: 2009", "INSTALLATION", "Installation & Workmanship Code", 0, "General Requirements for Competence of Assaying and Hallmarking Centres"),
    ("IS 1417: 2016", "IS 2790: 1979", "RAW_MATERIAL", "Allied Material / Component Specification", 0, "Guidelines for Manufacture of 14, 18, 22 and 24 Carat Gold Alloys"),

    # IS 10500 Drinking Water
    ("IS 10500: 2012", "IS 3025 (Part 1): 1987", "NORM_TEST", "Normative Test & Sampling Method", 1, "Methods of Sampling and Test for Water and Wastewater - General"),
    ("IS 10500: 2012", "IS 3025 (Part 11): 1983", "NORM_TEST", "Normative Test & Sampling Method", 1, "Methods of Sampling and Test for Water and Wastewater - pH"),
    ("IS 10500: 2012", "IS 1622: 1981", "NORM_TEST", "Normative Test & Sampling Method", 1, "Sampling and Microbiological Examination of Water"),
    ("IS 10500: 2012", "IS 14543: 2016", "RELATED_PRODUCT", "Allied Co-Dependent Product Standard", 0, "Packaged Drinking Water"),

    # IS/IEC 61439 & IS 8623 Switchgear / LT Panel
    ("IS 8623 (Part 1): 1993", "IS/IEC 60947 (Part 1): 2004", "SAFETY", "Safety & Environmental Standard", 1, "Low-Voltage Switchgear and Controlgear - General Rules"),
    ("IS 8623 (Part 1): 1993", "IS/IEC 60947 (Part 2): 2016", "SAFETY", "Safety & Environmental Standard", 1, "Low-Voltage Switchgear and Controlgear - Circuit Breakers"),
    ("IS 8623 (Part 1): 1993", "IS 10118 (Part 1): 1982", "INSTALLATION", "Installation & Workmanship Code", 0, "Code of Practice for Selection, Installation and Maintenance of Switchgear"),
    ("IS 8623 (Part 1): 1993", "IS 3043: 2018", "SAFETY", "Safety & Environmental Standard", 1, "Code of Practice for Earthing"),
]

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Ensure target standards exist in standards_registry
    for src, tgt, rel_type, rel_label, is_norm, tgt_title in EDGES:
        cur.execute(
            """
            INSERT OR IGNORE INTO standards_registry 
            (is_code, is_code_norm, base_code, title, revision, scope, full_text, division, status, superseded_by, reaffirmation_year, amendments_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (tgt, tgt.lower().replace(" ", ""), tgt.split(":")[0].strip().lower(), tgt_title, "Latest Published Edition", tgt_title, tgt_title, "Electrotechnical / Civil Engineering", "ACTIVE", None, 2021, 0)
        )

        cur.execute(
            """
            INSERT OR REPLACE INTO allied_standards_edges
            (source_is_code, target_is_code, relation_type, relation_label, is_normative)
            VALUES (?, ?, ?, ?, ?)
            """,
            (src, tgt, rel_type, rel_label, is_norm)
        )

    conn.commit()
    cur.execute("SELECT COUNT(*) FROM allied_standards_edges")
    print(f"Enriched allied standards edges. Total count: {cur.fetchone()[0]}")
    conn.close()

if __name__ == "__main__":
    main()

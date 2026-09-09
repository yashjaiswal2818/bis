"""Seeder for DoCA Hallmarking, Scheme-II CRS, Public Safety Standards, and 6-Way Taxonomy."""
from __future__ import annotations

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

NEW_STANDARDS = [
    # --- DoCA Scheme-IV Hallmarking Standards ---
    {
        "is_code": "IS 1417: 2016",
        "is_code_norm": "is1417:2016",
        "title": "GOLD AND GOLD ALLOYS, JEWELLERY/ARTEFACTS — FINENESS AND MARKING",
        "revision": "Fourth Revision",
        "page_start": 1,
        "page_end": 12,
        "scope": "Specifies requirements for fineness grades of gold alloys used in the manufacture of gold jewellery and artefacts, and guidelines for mandatory marking including the 6-digit alphanumeric Hallmark Unique Identification (HUID) and BIS Logo under the Department of Consumer Affairs (DoCA) Hallmarking Orders.",
        "full_text": "IS 1417: 2016 covers fineness in carats (24K, 22K, 18K, 14K) and parts per thousand (999, 916, 750, 585) for gold jewellery. Mandates the 3 mandatory hallmark marks: BIS Mark, Purity in Karats and fineness, and 6-digit HUID issued by BIS recognized assaying and hallmarking centres under DoCA regulations.",
        "division": "Metallurgical Engineering (MTD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 2
    },
    {
        "is_code": "IS 2112: 2014",
        "is_code_norm": "is2112:2014",
        "title": "SILVER AND SILVER ALLOYS, JEWELLERY/ARTEFACTS — FINENESS AND MARKING",
        "revision": "Third Revision",
        "page_start": 1,
        "page_end": 10,
        "scope": "Specifies fineness grades of silver and silver alloys used in jewellery, tableware, and silver artefacts, along with hallmarking guidelines and mandatory markings under the Department of Consumer Affairs (DoCA).",
        "full_text": "IS 2112: 2014 defines silver fineness grades including 999, 990, 925 (Sterling Silver), 900, 835, and 800 parts per thousand. Prescribes hallmarking procedures and verification protocols for silver artefacts.",
        "division": "Metallurgical Engineering (MTD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2019,
        "amendments_count": 1
    },
    {
        "is_code": "IS 15820: 2009",
        "is_code_norm": "is15820:2009",
        "title": "GENERAL REQUIREMENTS FOR COMPETENCE OF ASSAYING AND HALLMARKING CENTRES",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 20,
        "scope": "Specifies general requirements for the competence, impartiality, and consistent operation of assaying and hallmarking centres testing gold and silver jewellery under BIS and Department of Consumer Affairs (DoCA) supervision.",
        "full_text": "Covers fire assay and XRF spectrometer testing protocols, sampling criteria, and traceability requirements for issuing 6-digit HUID marks on precious metal artefacts.",
        "division": "Metallurgical Engineering (MTD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2020,
        "amendments_count": 1
    },

    # --- Scheme-II Compulsory Registration Scheme (CRS) ---
    {
        "is_code": "IS 16046 (Part 1): 2018",
        "is_code_norm": "is16046(part1):2018",
        "title": "SECONDARY CELLS AND BATTERIES CONTAINING ALKALINE OR OTHER NON-ACID ELECTROLYTES — NICKEL SYSTEMS",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 28,
        "scope": "Specifies requirements and tests for the safe operation of portable secondary nickel cells and batteries under the MeitY/DoCA Compulsory Registration Scheme (CRS).",
        "full_text": "Harmonized with IEC 62133-1 for portable equipment, medical devices, emergency lighting, and uninterruptible power systems.",
        "division": "Electrotechnical (ETD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2023,
        "amendments_count": 1
    },
    {
        "is_code": "IS 16046 (Part 2): 2018",
        "is_code_norm": "is16046(part2):2018",
        "title": "SECONDARY CELLS AND BATTERIES CONTAINING ALKALINE OR OTHER NON-ACID ELECTROLYTES — LITHIUM SYSTEMS",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 35,
        "scope": "Specifies safety requirements and tests for portable sealed secondary lithium cells and batteries (Li-ion/Li-polymer) under MeitY and DoCA Compulsory Registration Scheme (CRS). Mandates R-Registration numbers for commercial tenders.",
        "full_text": "Harmonized with IEC 62133-2. Prescribes overcharge, thermal abuse, short circuit, and mechanical drop tests for lithium-ion batteries in consumer electronics, IT equipment, and smart devices.",
        "division": "Electrotechnical (ETD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2023,
        "amendments_count": 2
    },
    {
        "is_code": "IS 13252 (Part 1): 2010",
        "is_code_norm": "is13252(part1):2010",
        "title": "INFORMATION TECHNOLOGY EQUIPMENT — SAFETY — PART 1: GENERAL REQUIREMENTS",
        "revision": "Second Revision",
        "page_start": 1,
        "page_end": 120,
        "scope": "Applicable to mains-powered or battery-powered information technology equipment, including computer servers, laptops, printers, scanners, and telecommunication terminal equipment under MeitY/DoCA Compulsory Registration Scheme (CRS).",
        "full_text": "Harmonized with IEC 60950-1. Covers electrical safety, insulation resistance, touch current, flammability ratings, and power supply standards.",
        "division": "Electronics and Information Technology (LITD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2020,
        "amendments_count": 4
    },
    {
        "is_code": "IS 16102 (Part 1): 2012",
        "is_code_norm": "is16102(part1):2012",
        "title": "SELF-BALLASTED LED LAMPS FOR GENERAL LIGHTING SERVICES — PART 1: SAFETY REQUIREMENTS",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 22,
        "scope": "Specifies safety and interchangeability requirements, together with test methods, for self-ballasted LED lamps for general lighting services under the BIS Compulsory Registration Scheme (CRS).",
        "full_text": "Prescribes insulation resistance, mechanical strength of lamp caps, heat resistance, and fire resistance limits for LED lighting procurement.",
        "division": "Electrotechnical (ETD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2022,
        "amendments_count": 2
    },
    {
        "is_code": "IS 16102 (Part 2): 2012",
        "is_code_norm": "is16102(part2):2012",
        "title": "SELF-BALLASTED LED LAMPS FOR GENERAL LIGHTING SERVICES — PART 2: PERFORMANCE REQUIREMENTS",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 18,
        "scope": "Specifies performance requirements (luminous efficacy, rated wattage, color rendering index CRI, life expectancy) for self-ballasted LED lamps for general lighting under government and municipal procurement tenders.",
        "full_text": "Defines minimum lumen efficacy requirements (>100 lm/W), power factor (>0.90), and harmonic distortion tolerances for public tenders.",
        "division": "Electrotechnical (ETD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2022,
        "amendments_count": 1
    },
    {
        "is_code": "IS 16221 (Part 2): 2015",
        "is_code_norm": "is16221(part2):2015",
        "title": "SAFETY OF POWER CONVERTERS FOR USE IN PHOTOVOLTAIC POWER SYSTEMS — PARTICULAR REQUIREMENTS FOR INVERTERS",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 45,
        "scope": "Specifies particular safety requirements for utility-interactive and standalone grid-tied solar photovoltaic inverters under the Ministry of New and Renewable Energy (MNRE) and DoCA/CRS regulations.",
        "full_text": "Harmonized with IEC 62109-2. Mandates anti-islanding protection, surge withstand, DC ground fault protection, and thermal safety.",
        "division": "Electrotechnical (ETD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 1
    },

    # --- Scheme-I Public Safety & Materials ---
    {
        "is_code": "IS 14543: 2016",
        "is_code_norm": "is14543:2016",
        "title": "PACKAGED DRINKING WATER (OTHER THAN PACKAGED NATURAL MINERAL WATER) — SPECIFICATION",
        "revision": "Second Revision",
        "page_start": 1,
        "page_end": 30,
        "scope": "Prescribes requirements and methods of sampling and test for packaged drinking water filled in hermetically sealed containers of various sizes, with mandatory BIS ISI Mark certification under Food Safety & Consumer Affairs QCO.",
        "full_text": "Specifies microbiological, pesticide residue limits (max 0.0001 mg/l), toxic heavy metals (arsenic, lead, mercury), and sensory parameters. Mandatory ISI Mark Scheme-I under DoCA/FSSAI statutory notifications.",
        "division": "Food and Agriculture (FAD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 3
    },
    {
        "is_code": "IS 2925: 1984",
        "is_code_norm": "is2925:1984",
        "title": "SPECIFICATION FOR INDUSTRIAL SAFETY HELMETS",
        "revision": "Second Revision",
        "page_start": 1,
        "page_end": 18,
        "scope": "Covers physical and performance requirements, methods of test, and mandatory ISI marking for industrial safety helmets providing head protection against falling objects and mechanical impact on construction and manufacturing sites.",
        "full_text": "Prescribes shock absorption testing (maximum transmitted force <5.0 kN), penetration resistance, flammability, electrical insulation (up to 2000 V), and mandatory ISI marking under Scheme-I.",
        "division": "Chemical (CHD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2020,
        "amendments_count": 2
    },
    {
        "is_code": "IS 3196 (Part 1): 2013",
        "is_code_norm": "is3196(part1):2013",
        "title": "WELDED LOW CARBON STEEL CYLINDERS EXCEEDING 5 LITRE WATER CAPACITY FOR LOW PRESSURE LIQUEFIABLE GASES — LPG CYLINDERS",
        "revision": "Fifth Revision",
        "page_start": 1,
        "page_end": 42,
        "scope": "Specifies requirements for design, manufacture, testing, and mandatory ISI certification of welded steel LPG cylinders for domestic and commercial distribution under PESO and DoCA gas cylinder regulations.",
        "full_text": "Mandatory Scheme-I certification. Outlines hydrostatic pressure testing (2.45 MPa), bursting test, weld radioscopy, and CML licensing.",
        "division": "Mechanical Engineering (MED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2018,
        "amendments_count": 2
    },

    # --- Normative Laboratory Test Methods ---
    {
        "is_code": "IS 4031 (Part 1): 1996",
        "is_code_norm": "is4031(part1):1996",
        "title": "METHODS OF PHYSICAL TESTS FOR HYDRAULIC CEMENT — PART 1: DETERMINATION OF FINENESS BY DRY SIEVING",
        "revision": "Second Revision",
        "page_start": 1,
        "page_end": 8,
        "scope": "Specifies the procedure for determining the fineness of hydraulic cements by dry sieving on a 90-micron IS sieve as a normative quality verification method for cement manufacturing and construction compliance.",
        "full_text": "Defines test apparatus, representative sampling protocol, sieving motion, and calculation of residue percentage to verify compliance with IS 269, IS 8112, and IS 12269.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2022,
        "amendments_count": 1
    },
    {
        "is_code": "IS 4031 (Part 4): 1988",
        "is_code_norm": "is4031(part4):1988",
        "title": "METHODS OF PHYSICAL TESTS FOR HYDRAULIC CEMENT — PART 4: DETERMINATION OF CONSISTENCY OF STANDARD CEMENT PASTE",
        "revision": "First Revision",
        "page_start": 1,
        "page_end": 10,
        "scope": "Specifies the procedure for determining standard consistency of cement paste using the Vicat apparatus, required as a prerequisite test for determining setting times and soundness.",
        "full_text": "Prescribes Vicat plunger dimensions (10mm diameter), test conditions (27°C, 90% humidity), and gauge penetration depth (5 to 7 mm from bottom of mould).",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2023,
        "amendments_count": 1
    },
    {
        "is_code": "IS 4031 (Part 5): 1988",
        "is_code_norm": "is4031(part5):1988",
        "title": "METHODS OF PHYSICAL TESTS FOR HYDRAULIC CEMENT — PART 5: DETERMINATION OF INITIAL AND FINAL SETTING TIMES",
        "revision": "First Revision",
        "page_start": 1,
        "page_end": 10,
        "scope": "Specifies the method for determining initial and final setting times of hydraulic cement using the Vicat needle apparatus for site construction and laboratory compliance.",
        "full_text": "Defines initial setting time (needle fails to pierce beyond 5mm of mould base, min 30 minutes) and final setting time (attachment fails to make impression, max 600 minutes).",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2023,
        "amendments_count": 0
    },
    {
        "is_code": "IS 4031 (Part 6): 1988",
        "is_code_norm": "is4031(part6):1988",
        "title": "METHODS OF PHYSICAL TESTS FOR HYDRAULIC CEMENT — PART 6: DETERMINATION OF COMPRESSIVE STRENGTH OF HYDRAULIC CEMENT",
        "revision": "First Revision",
        "page_start": 1,
        "page_end": 16,
        "scope": "Specifies the standard laboratory procedure for determining the compressive strength of mortar cubes (70.6 mm) made with standard Ennore sand at 3, 7, and 28 days.",
        "full_text": "Primary normative testing standard referenced by IS 269, IS 8112, and IS 12269 to verify 33 MPa, 43 MPa, and 53 MPa grade compliance.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2023,
        "amendments_count": 2
    },
    {
        "is_code": "IS 516: 2021",
        "is_code_norm": "is516:2021",
        "title": "HARDENED CONCRETE — METHODS OF TEST — PART 1: COMPRESSIVE, FLEXURAL AND SPLIT TENSILE STRENGTH",
        "revision": "Second Revision",
        "page_start": 1,
        "page_end": 38,
        "scope": "Specifies procedures for casting, curing, and testing compressive strength (150 mm cubes or cylinders), flexural strength of beams, and split tensile strength of hardened concrete.",
        "full_text": "Normative test standard referenced by IS 456 for concrete acceptance in government construction, bridge building, and quality audits.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 1
    },
    {
        "is_code": "IS 1608 (Part 1): 2022",
        "is_code_norm": "is1608(part1):2022",
        "title": "METALLIC MATERIALS — TENSILE TESTING — PART 1: METHOD OF TEST AT ROOM TEMPERATURE",
        "revision": "Fourth Revision",
        "page_start": 1,
        "page_end": 50,
        "scope": "Specifies the method for tensile testing of metallic materials and defines the mechanical properties (yield strength, 0.2% proof stress, ultimate tensile strength, percentage elongation) for steels and reinforcement bars.",
        "full_text": "Mandatory testing method cited in IS 1786 (TMT Rebars) and IS 2062 (Structural Steel) to certify Fe 415, Fe 500, and Fe 550D yield properties.",
        "division": "Metallurgical Engineering (MTD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2022,
        "amendments_count": 0
    },
    {
        "is_code": "IS 3025 (Part 11): 1983",
        "is_code_norm": "is3025(part11):1983",
        "title": "METHODS OF SAMPLING AND TEST (PHYSICAL AND CHEMICAL) FOR WATER AND WASTEWATER — PART 11: PH VALUE",
        "revision": "First Revision",
        "page_start": 1,
        "page_end": 8,
        "scope": "Specifies the electrometric method using a glass electrode for the determination of pH value in drinking water, surface water, and industrial effluents.",
        "full_text": "Normative testing reference cited in IS 10500 (Drinking Water) to verify permissible pH range between 6.5 and 8.5.",
        "division": "Chemical (CHD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2022,
        "amendments_count": 1
    },
    {
        "is_code": "IS 2386 (Part 1): 1963",
        "is_code_norm": "is2386(part1):1963",
        "title": "METHODS OF TEST FOR AGGREGATES FOR CONCRETE — PART 1: PARTICLE SIZE AND SHAPE",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 26,
        "scope": "Specifies sieve analysis, flakiness index, and elongation index test procedures for coarse and fine aggregates for concrete construction.",
        "full_text": "Normative testing standard cited by IS 383 and IS 456 to verify aggregate grading zones and particle shape criteria.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 3
    },

    # --- Installation & Workmanship Codes ---
    {
        "is_code": "IS 7634 (Part 1): 1975",
        "is_code_norm": "is7634(part1):1975",
        "title": "CODE OF PRACTICE FOR PLASTICS PIPES SELECTION, HANDLING, STORAGE AND LAYING",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 20,
        "scope": "Provides guidance on the selection, transit handling, site storage, and trench excavation for laying plastic piping systems for water supply and drainage.",
        "full_text": "Outlines bed preparation, trench depth, thermal expansion allowance, and backfilling practices for uPVC and HDPE piping installations.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2020,
        "amendments_count": 1
    },
    {
        "is_code": "IS 7634 (Part 2): 2012",
        "is_code_norm": "is7634(part2):2012",
        "title": "LAYING AND JOINTING OF POLYETHYLENE (PE) PIPES FOR POTABLE WATER SUPPLY — CODE OF PRACTICE",
        "revision": "Second Revision",
        "page_start": 1,
        "page_end": 24,
        "scope": "Specifies requirements for laying, butt fusion welding, electrofusion jointing, anchoring, and hydrostatic testing of HDPE pipes for water supply.",
        "full_text": "Direct companion installation code cited in tenders procuring HDPE pipes conforming to IS 4984.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2022,
        "amendments_count": 0
    },
    {
        "is_code": "IS 14489: 1998",
        "is_code_norm": "is14489:1998",
        "title": "CODE OF PRACTICE ON OCCUPATIONAL HEALTH AND SAFETY AUDITS",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 32,
        "scope": "Establishes audit objectives, criteria, and methodology for evaluating an organization's occupational health and safety management system in industrial plants and public works projects.",
        "full_text": "Provides standard audit checklists for chemical hazard control, personal protective gear verification, fire safety readiness, and regulatory compliance under DoCA and Ministry of Labour.",
        "division": "Chemical (CHD)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 0
    },
    {
        "is_code": "IS 4021: 1995",
        "is_code_norm": "is4021:1995",
        "title": "TIMBER DOOR, WINDOW AND VENTILATOR FRAMES — CODE OF PRACTICE FOR INSTALLATION",
        "revision": "Third Revision",
        "page_start": 1,
        "page_end": 18,
        "scope": "Specifies materials, fabrication details, holdfast anchor placement, and installation workmanship for timber door and window frames in masonry walls.",
        "full_text": "Direct installation standard cited in public works specifications for flush door shutters (IS 2202) and timber panel doors (IS 1003).",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2020,
        "amendments_count": 1
    },

    # --- Terminology & Glossaries ---
    {
        "is_code": "IS 4845: 1968",
        "is_code_norm": "is4845:1968",
        "title": "DEFINITIONS AND TERMINOLOGY RELATING TO HYDRAULIC CEMENT AND POZZOLANA",
        "revision": "First Edition",
        "page_start": 1,
        "page_end": 14,
        "scope": "Defines technical terms used in the manufacture, testing, and application of hydraulic cements, pozzolana, blast-furnace slag, fly ash, and calcined clays.",
        "full_text": "Establishes canonical terminology definitions to eliminate ambiguity in technical tenders and procurement documents.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 0
    },
    {
        "is_code": "IS 2248: 1992",
        "is_code_norm": "is2248:1992",
        "title": "GLOSSARY OF TERMS RELATING TO STRUCTURAL CLAY PRODUCTS",
        "revision": "First Revision",
        "page_start": 1,
        "page_end": 16,
        "scope": "Defines terms relating to common burnt clay building bricks, hollow clay blocks, structural tiles, and terra-cotta products.",
        "full_text": "Provides official terminology for brick classifications, efflorescence grading, and dimensional terms.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2022,
        "amendments_count": 0
    },
    {
        "is_code": "IS 195: 1991",
        "is_code_norm": "is195:1991",
        "title": "FIRE SAFETY TERMINOLOGY AND GRAPHICAL SYMBOLS",
        "revision": "First Revision",
        "page_start": 1,
        "page_end": 24,
        "scope": "Specifies definitions and graphical symbols relating to fire safety, fire fighting appliances, egress routes, and building protection.",
        "full_text": "Standard terminology referenced in fire tender specifications and building bylaws.",
        "division": "Civil Engineering (CED)",
        "status": "ACTIVE",
        "reaffirmation_year": 2021,
        "amendments_count": 0
    }
]

NEW_QCOS = [
    # --- DoCA Hallmarking Orders (Scheme-IV) ---
    {
        "is_code": "IS 1417: 2016",
        "product_category": "Gold Jewellery and Gold Artefacts (Fineness & Marking)",
        "scheme_type": "Scheme-IV (Mandatory Hallmarking with HUID)",
        "is_mandatory": True,
        "issuing_ministry": "Department of Consumer Affairs (DoCA)",
        "order_name": "Hallmarking of Gold Jewellery and Gold Artefacts Order, 2020",
        "effective_date": "2021-06-23",
        "compliance_warning": "CRITICAL: Under the Department of Consumer Affairs (DoCA) Hallmarking Order, sale or procurement of gold jewellery without 6-digit alphanumeric HUID (Hallmark Unique Identification) is an offense under Section 29 of the BIS Act, 2016. Tenders must mandate certified BIS Hallmarked supply."
    },
    {
        "is_code": "IS 2112: 2014",
        "product_category": "Silver Jewellery and Silver Artefacts",
        "scheme_type": "Scheme-IV (Hallmarking Scheme)",
        "is_mandatory": True,
        "issuing_ministry": "Department of Consumer Affairs (DoCA)",
        "order_name": "Silver Artefacts (Quality Control) Order",
        "effective_date": "2022-04-01",
        "compliance_warning": "MANDATORY: Silver items must bear official BIS Hallmark indicating fineness (925/999) from an authorized Assaying and Hallmarking Centre."
    },
    {
        "is_code": "IS 15820: 2009",
        "product_category": "Assaying and Hallmarking Centres Competence",
        "scheme_type": "Scheme-IV (Hallmarking Centre Recognition)",
        "is_mandatory": True,
        "issuing_ministry": "Department of Consumer Affairs (DoCA)",
        "order_name": "Assaying and Hallmarking Centres Recognition Guidelines",
        "effective_date": "2020-01-15",
        "compliance_warning": "MANDATORY: Testing protocols for gold/silver purity must strictly follow IS 15820 under DoCA monitoring."
    },

    # --- Scheme-II CRS Orders ---
    {
        "is_code": "IS 16046 (Part 1): 2018",
        "product_category": "Secondary Nickel Cells and Batteries",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY / Department of Consumer Affairs (DoCA)",
        "order_name": "Electronics and IT Goods (Compulsory Registration) Order",
        "effective_date": "2019-01-01",
        "compliance_warning": "MANDATORY: Nickel battery systems require valid BIS Registration Number (R-Number) under MeitY/DoCA CRS scheme."
    },
    {
        "is_code": "IS 16102 (Part 1): 2012",
        "product_category": "Self-Ballasted LED Lamps (Safety)",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY / Department of Consumer Affairs (DoCA)",
        "order_name": "Electronics and IT Goods (Compulsory Registration) Order",
        "effective_date": "2015-05-07",
        "compliance_warning": "MANDATORY: Self-ballasted LED lamps must carry valid BIS CRS Registration (R-Number) under government energy procurement mandates."
    },
    {
        "is_code": "IS 16102 (Part 2): 2012",
        "product_category": "Self-Ballasted LED Lamps (Performance)",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "MeitY / Department of Consumer Affairs (DoCA)",
        "order_name": "Electronics and IT Goods (Compulsory Registration) Order",
        "effective_date": "2015-05-07",
        "compliance_warning": "MANDATORY: LED lamp efficiency and lumen performance must conform to IS 16102 (Part 2) under public lighting tenders."
    },
    {
        "is_code": "IS 16221 (Part 2): 2015",
        "product_category": "Solar Photovoltaic Power Inverters",
        "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
        "is_mandatory": True,
        "issuing_ministry": "Ministry of New and Renewable Energy (MNRE) / DoCA",
        "order_name": "Solar Photovoltaics, Systems, Devices and Components Goods Order",
        "effective_date": "2018-04-16",
        "compliance_warning": "MANDATORY: Solar grid-tied inverters require valid BIS CRS certification. Tenders must reject uncertified solar inverter brands."
    },

    # --- Scheme-I Public Safety ---
    {
        "is_code": "IS 10500: 2012",
        "product_category": "Drinking Water (Piped / Potable Supply)",
        "scheme_type": "Scheme-I (Mandatory Conformance under Jal Jeevan Mission & DoCA)",
        "is_mandatory": True,
        "issuing_ministry": "Department of Consumer Affairs (DoCA) & Jal Shakti",
        "order_name": "Uniform Drinking Water Quality Standards Order",
        "effective_date": "2019-11-20",
        "compliance_warning": "CRITICAL: Potable drinking water supply projects, municipal water distribution, and water purification units must strictly conform to IS 10500: 2012 parameters without relaxation."
    },
    {
        "is_code": "IS 14543: 2016",
        "product_category": "Packaged Drinking Water",
        "scheme_type": "Scheme-I (Mandatory ISI Mark)",
        "is_mandatory": True,
        "issuing_ministry": "Department of Consumer Affairs (DoCA) & FSSAI",
        "order_name": "Food Safety & Standards / Packaged Water Mandatory Certification Order",
        "effective_date": "2001-03-29",
        "compliance_warning": "CRITICAL: Packaged drinking water cannot be manufactured or procured without mandatory BIS Standard Mark (ISI Mark) and FSSAI license under Supreme Court and DoCA notifications."
    },
    {
        "is_code": "IS 2925: 1984",
        "product_category": "Industrial Safety Helmets",
        "scheme_type": "Scheme-I (Mandatory ISI Mark)",
        "is_mandatory": True,
        "issuing_ministry": "Department of Consumer Affairs (DoCA) / DPIIT",
        "order_name": "Personal Protective Equipment (Quality Control) Order, 2023",
        "effective_date": "2023-12-06",
        "compliance_warning": "MANDATORY: Industrial protective helmets must bear the ISI Mark under Scheme-I for all government infrastructure and construction tenders."
    },
    {
        "is_code": "IS 3196 (Part 1): 2013",
        "product_category": "LPG Gas Cylinders",
        "scheme_type": "Scheme-I (Mandatory ISI Mark)",
        "is_mandatory": True,
        "issuing_ministry": "Department of Consumer Affairs (DoCA) / MoPNG / PESO",
        "order_name": "Gas Cylinders Rules & Mandatory Certification Order",
        "effective_date": "2004-09-21",
        "compliance_warning": "CRITICAL: LPG cylinders are strictly mandatory under Scheme-I. Bidders must produce valid BIS CML license and PESO manufacture approval."
    }
]

NEW_XREFS = {
    # Gold Hallmarking
    "IS 1417: 2016": ["IS 2112: 2014", "IS 15820: 2009"],
    "IS 2112: 2014": ["IS 1417: 2016", "IS 15820: 2009"],
    
    # Cement connected to Test Methods and Terminology
    "IS 269: 1989": ["IS 4031 (Part 1): 1996", "IS 4031 (Part 4): 1988", "IS 4031 (Part 5): 1988", "IS 4031 (Part 6): 1988", "IS 4845: 1968", "IS 383: 1970"],
    "IS 269: 2015": ["IS 4031 (Part 1): 1996", "IS 4031 (Part 4): 1988", "IS 4031 (Part 5): 1988", "IS 4031 (Part 6): 1988", "IS 4845: 1968", "IS 383: 1970"],
    "IS 8112: 1989": ["IS 4031 (Part 1): 1996", "IS 4031 (Part 5): 1988", "IS 4031 (Part 6): 1988", "IS 4845: 1968"],
    "IS 12269: 1987": ["IS 4031 (Part 1): 1996", "IS 4031 (Part 5): 1988", "IS 4031 (Part 6): 1988", "IS 4845: 1968"],
    "IS 455: 1989": ["IS 4031 (Part 6): 1988", "IS 4845: 1968"],
    "IS 1489 (Part 1): 1991": ["IS 4031 (Part 6): 1988", "IS 4845: 1968"],

    # Concrete connected to Installation, Testing, and Safety
    "IS 456: 2000": ["IS 516: 2021", "IS 383: 1970", "IS 1786: 2008", "IS 2386 (Part 1): 1963", "IS 14489: 1998", "IS 195: 1991"],
    "IS 1786: 2008": ["IS 1608 (Part 1): 2022", "IS 456: 2000"],
    "IS 2062: 2011": ["IS 1608 (Part 1): 2022"],

    # Pipes connected to Installation and Raw Materials
    "IS 4984: 2016": ["IS 7634 (Part 1): 1975", "IS 7634 (Part 2): 2012"],
    "IS 4985: 2000": ["IS 7634 (Part 1): 1975"],

    # Doors connected to Installation
    "IS 2202 (Part 1): 1999": ["IS 4021: 1995"],
    "IS 1003 (Part 1): 2003": ["IS 4021: 1995"],

    # Water connected to Testing
    "IS 10500: 2012": ["IS 3025 (Part 11): 1983", "IS 14543: 2016"],
    "IS 14543: 2016": ["IS 3025 (Part 11): 1983", "IS 10500: 2012"],

    # Electronics CRS
    "IS 16046 (Part 2): 2018": ["IS 13252 (Part 1): 2010"],
    "IS 16102 (Part 1): 2012": ["IS 16102 (Part 2): 2012"]
}


def main():
    print("=== SEEDING DoCA CERTIFICATION & ALLIED STANDARDS DATA ===")
    
    # 1. Update parsed_standards.json
    parsed_path = DATA_DIR / "parsed_standards.json"
    existing_st = json.loads(parsed_path.read_text(encoding="utf-8"))
    existing_codes = {s["is_code"].lower(): s for s in existing_st}
    
    added_st_count = 0
    for ns in NEW_STANDARDS:
        code_l = ns["is_code"].lower()
        if code_l in existing_codes:
            existing_codes[code_l].update(ns)
        else:
            existing_st.append(ns)
            existing_codes[code_l] = ns
            added_st_count += 1
            
    parsed_path.write_text(json.dumps(existing_st, indent=2), encoding="utf-8")
    print(f"[*] parsed_standards.json updated: {len(existing_st)} total standards (+{added_st_count} new).")

    # 2. Update qco_mandatory_catalog.json
    qco_path = DATA_DIR / "qco_mandatory_catalog.json"
    existing_qco = json.loads(qco_path.read_text(encoding="utf-8"))
    qco_codes = {q["is_code"].lower(): q for q in existing_qco}
    
    added_qco_count = 0
    for nq in NEW_QCOS:
        ql = nq["is_code"].lower()
        if ql in qco_codes:
            qco_codes[ql].update(nq)
        else:
            existing_qco.append(nq)
            qco_codes[ql] = nq
            added_qco_count += 1
            
    qco_path.write_text(json.dumps(existing_qco, indent=2), encoding="utf-8")
    print(f"[*] qco_mandatory_catalog.json updated: {len(existing_qco)} total rules (+{added_qco_count} new).")

    # 3. Update raw_xrefs.json
    xrefs_path = DATA_DIR / "raw_xrefs.json"
    existing_xrefs = json.loads(xrefs_path.read_text(encoding="utf-8"))
    for src, tgts in NEW_XREFS.items():
        if src in existing_xrefs:
            cur = set(existing_xrefs[src])
            cur.update(tgts)
            existing_xrefs[src] = sorted(list(cur))
        else:
            existing_xrefs[src] = tgts
            
    total_edges = sum(len(v) for v in existing_xrefs.values())
    xrefs_path.write_text(json.dumps(existing_xrefs, indent=2), encoding="utf-8")
    print(f"[*] raw_xrefs.json updated: {len(existing_xrefs)} source nodes, {total_edges} relationship edges.")

    # 4. Update is_code_whitelist.json
    wl_path = DATA_DIR / "is_code_whitelist.json"
    wl_data = json.loads(wl_path.read_text(encoding="utf-8"))
    canon = set(wl_data.get("canonical", []))
    norm = set(wl_data.get("normalized", []))
    for s in existing_st:
        c = s["is_code"]
        canon.add(c)
        norm.add(re.sub(r"\s+", "", c).lower())
    wl_data["canonical"] = sorted(list(canon))
    wl_data["normalized"] = sorted(list(norm))
    wl_path.write_text(json.dumps(wl_data, indent=2), encoding="utf-8")
    print(f"[*] is_code_whitelist.json updated: {len(wl_data['canonical'])} canonical, {len(wl_data['normalized'])} normalized.")
    print("=== DATA SEEDING COMPLETE ===")


if __name__ == "__main__":
    main()

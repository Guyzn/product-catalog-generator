# -*- coding: utf-8 -*-
"""示例数据：通用占位公司 + 4 个公开牌号(数据源自公开标准，无公司信息)。"""

SAMPLE_CONFIG = dict(
    brand="#1B3A5C",
    accent="#E8712C",
    company="YOUR COMPANY",
    company_en="Your Company Ltd.",
    website="www.example.com",
    logo_text="◣ COMPANY",
    contact=dict(
        phone="86-000 0000 0000",
        email="sales@example.com",
        address="No.1 Example St., Industrial Zone, Your City, China",
    ),
)

SAMPLE_GRADES = [
    dict(grade="1.2311", std="DIN EN ISO 4957", category="plastic",
         chem={"C": "0.35-0.45", "Si": "0.20-0.40", "Mn": "1.30-1.60",
               "Cr": "1.80-2.10", "Mo": "0.15-0.25"},
         sm="EAF+LF+VD", ft="Hot rolled / forged",
         ht="Spheroidizing anneal 770-790℃; quench 850-880℃ oil; temper 100-700℃.",
         desc="Pre-hardened plastic mould steel with excellent polishability and machinability."),
    dict(grade="1.2344", std="DIN 17350", category="hot",
         chem={"C": "0.37-0.43", "Si": "0.90-1.20", "Mn": "0.30-0.50",
               "Cr": "4.80-5.50", "Mo": "1.20-1.50", "V": "0.90-1.10"},
         sm="EAF+LF+VD", ft="Hot rolled / forged",
         ht="Spheroidizing anneal 860-890℃; quench 1020-1050℃; temper 560-580℃.",
         desc="Hot work tool steel: high tempering resistance, thermal shock resistance, toughness."),
    dict(grade="4140", std="ASTM A29", category="alloy",
         chem={"C": "0.38-0.43", "Si": "0.15-0.35", "Mn": "0.75-1.00",
               "Cr": "0.80-1.10", "Mo": "0.15-0.25"},
         sm="EAF+LF+VD", ft="Hot rolled / forged",
         ht="Normalize 850-900℃; quench 850℃ water/oil; temper 550-700℃.",
         desc="Chromium-molybdenum alloy structural steel: good weldability, hardenability, machinability."),
    dict(grade="4340", std="ASTM A29", category="alloy",
         chem={"C": "0.38-0.43", "Si": "0.15-0.35", "Mn": "0.60-0.80",
               "Cr": "0.70-0.90", "Ni": "1.65-2.00", "Mo": "0.20-0.30"},
         sm="EAF+LF+VD", ft="Hot rolled / forged",
         ht="Normalize 840-900℃; quench 830-860℃; temper 200-650℃.",
         desc="Nickel-chromium-molybdenum quenched & tempered alloy steel: high toughness and strength."),
]

"""
Print Category 1 and Category 2 papers in full detail.
"""

import json

with open("data/raw/tofilski_scholar_all.json", encoding="utf-8") as f:
    papers = json.load(f)

geo_kw = [
    "asia", "kazakhstan", "serbia", "mexico", "india", "morocco", "africa", 
    "europe", "romania", "malta", "lineage m", "sahariensis", "pomonella", "ethiopia"
]

print("================================================================================")
print("CATEGORY 1: GEOGRAPHIC SUBSPECIES & REGIONAL DIVERSITY (PROJECT REGIONS)")
print("================================================================================")

cat1_count = 0
for p in papers:
    t = p["title"].lower()
    is_bee = any(k in t for k in ["honey", "apis", "bee", "pszczoły"])
    if is_bee and any(k in t for k in geo_kw):
        cat1_count += 1
        print(f"{cat1_count}. {p['title']}")
        print(f"   Citations: {p['cites']} | Scholar ID: {p['cid']}")

print("\n================================================================================")
print("CATEGORY 2: WING GEOMETRIC MORPHOMETRICS & IDENTIFICATION TOOLS")
print("================================================================================")

tool_kw = ["deepwings", "cubital index", "wing images", "drawwing", "standard morphometry", "automatic measurement", "forewings", "venation", "asymmetry", "morphometric"]
cat2_count = 0
for p in papers:
    t = p["title"].lower()
    is_bee = any(k in t for k in ["honey", "apis", "bee", "pszczoły"])
    if is_bee and any(k in t for k in tool_kw) and not any(k in t for k in geo_kw):
        cat2_count += 1
        print(f"{cat2_count}. {p['title']}")
        print(f"   Citations: {p['cites']} | Scholar ID: {p['cid']}")

"""
Categorize and analyze all Adam Tofilski publications from Google Scholar
for their relevance to our Honey Bee (Apis mellifera) x Plants x Regions project.
"""

import json
from pathlib import Path

with open("data/raw/tofilski_scholar_all.json", encoding="utf-8") as f:
    papers = json.load(f)

categories = {
    "1. Geographic Subspecies & Regional Diversity (Direct Match to Project Regions)": [],
    "2. Wing Geometric Morphometrics, Venation & Automated Identification Tools": [],
    "3. Foraging Ecology, Flight Mechanics, Waggle Dance & Resource Quality": [],
    "4. Environmental Factors (Temperature, Heat Stress, Larval Starvation, Pollen Deprivation)": [],
    "5. Honey Bee Colony Dynamics, Queens, Drones, Hybrids & Conservation": [],
    "6. Other Insect Research (Non-Honeybee: Ants, Wasps, Syrphidae, Beetles)": [],
}

geo_kw = [
    "asia", "kazakhstan", "serbia", "mexico", "india", "morocco", "africa", 
    "europe", "romania", "malta", "lineage m", "sahariensis", "pomonella", "ethiopia"
]
tool_kw = ["deepwings", "cubital index", "wing images", "drawwing", "standard morphometry", "automatic measurement", "forewings estimated"]
forage_kw = ["foraging", "waggle dance", "wing beating", "food sources", "foraging distance", "bee trees"]
env_kw = ["temperature", "heat stress", "starvation", "pollen deprivation", "monthly changes", "climatic", "pollen"]
repro_kw = ["queen", "drone", "swarming", "hybrids", "maternal", "semen", "sperm", "venom", "brood", "mating", "bartnictwo"]

for p in papers:
    t = p["title"].lower()
    is_bee = any(k in t for k in ["honey", "apis", "bee", "pszczoły", "pszczoła", "bartnictwo"]) or "osmia" in t
    
    if is_bee and any(k in t for k in geo_kw):
        categories["1. Geographic Subspecies & Regional Diversity (Direct Match to Project Regions)"].append(p)
    elif is_bee and any(k in t for k in tool_kw):
        categories["2. Wing Geometric Morphometrics, Venation & Automated Identification Tools"].append(p)
    elif is_bee and any(k in t for k in forage_kw):
        categories["3. Foraging Ecology, Flight Mechanics, Waggle Dance & Resource Quality"].append(p)
    elif is_bee and any(k in t for k in env_kw):
        categories["4. Environmental Factors (Temperature, Heat Stress, Larval Starvation, Pollen Deprivation)"].append(p)
    elif is_bee and any(k in t for k in repro_kw):
        categories["5. Honey Bee Colony Dynamics, Queens, Drones, Hybrids & Conservation"].append(p)
    elif is_bee and any(k in t for k in ["wing", "morph", "asymmetry", "venation", "fore wing"]):
        categories["2. Wing Geometric Morphometrics, Venation & Automated Identification Tools"].append(p)
    elif is_bee:
        categories["5. Honey Bee Colony Dynamics, Queens, Drones, Hybrids & Conservation"].append(p)
    else:
        categories["6. Other Insect Research (Non-Honeybee: Ants, Wasps, Syrphidae, Beetles)"].append(p)

# Output summary
print("=" * 80)
print("ADAM TOFILSKI RESEARCH RELEVANCE AUDIT (From Google Scholar Profile)")
print("=" * 80)

total_relevant = 0
for cat, items in categories.items():
    if not cat.startswith("6."):
        total_relevant += len(items)
    print(f"\n{cat} ({len(items)} papers)")
    for p in items:
        cite_str = f"Cited: {p['cites']}" if p['cites'] else "Recent"
        print(f"  * [{p['year']}] {p['title']} ({cite_str})")

print("\n" + "=" * 80)
print(f"SUMMARY: Out of {len(papers)} unique publications, {total_relevant} directly relate to Apis mellifera,")
print("its regional ecotypes, wing venation morphometrics, foraging flight, and environmental factors!")
print("=" * 80)

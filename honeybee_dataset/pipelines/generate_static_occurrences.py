"""Generate bootstrapped GBIF bee occurrence data from seed JSON."""
import json, pandas as pd, numpy as np
from pathlib import Path

RAW = Path("E:/AISA/honeybee_dataset/data/raw")
seed = json.loads((RAW / "region_plant_bee_seed.json").read_text(encoding="utf-8"))

rows = []
rng = np.random.default_rng(42)

for region in seed["regions"]:
    iso   = region.get("iso_country", "")
    lat_c = region.get("latitude_approx", 0)
    lon_c = region.get("longitude_approx", 0)
    subs  = region.get("known_subspecies", "")
    # extract first subspecies short name
    sub_short = subs.split("(")[0].split("/")[0].strip()
    sub_short = sub_short.replace("Apis mellifera", "").strip()

    n = int(rng.integers(20, 45))
    for i in range(n):
        lat  = float(round(lat_c + float(rng.normal(0, 1.5)), 4))
        lon  = float(round(lon_c + float(rng.normal(0, 2.0)), 4))
        year = int(rng.integers(2005, 2024))
        rows.append({
            "gbif_key":       f"STATIC_{iso}_{i:04d}",
            "species":        "Apis mellifera",
            "subspecies":     sub_short,
            "country":        region.get("country"),
            "country_code":   iso,
            "state_province": region.get("region", ""),
            "latitude":       lat,
            "longitude":      lon,
            "event_date":     f"{year}-06-01",
            "year":           year,
            "month":          int(rng.integers(4, 10)),
            "basis_of_record":"STATIC_BOOTSTRAP",
            "institution_code":"SEED_DATA",
            "dataset_name":   "Honeybee Dataset Bootstrap (replace with GBIF when online)",
            "occurrence_id":  f"bootstrap_{iso}_{i:04d}",
            "taxon_rank":     "SPECIES",
            "vernacular_name":"Western Honey Bee",
        })

df = pd.DataFrame(rows)
out = RAW / "gbif_apis_mellifera_occurrences.csv"
df.to_csv(out, index=False)
print(f"Saved {len(df)} bootstrapped bee occurrence rows")
print(df.groupby("country_code")["gbif_key"].count())

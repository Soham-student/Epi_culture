"""
Query real GBIF occurrence counts and sample records using verified Apis mellifera key 1341976.
"""

import requests
import pandas as pd
from pathlib import Path

RAW_DIR = Path("E:/AISA/honeybee_dataset/data/raw")
APIS_KEY = 1341976

countries = [
    "AZ", "BY", "CY", "DE", "DZ", "ES", "FR", "GB", "GE", "IE", 
    "IN", "IQ", "IR", "KZ", "LT", "MX", "NL", "NO", "PL", "RS", 
    "SA", "TJ", "TR"
]

headers = {"User-Agent": "HoneybeeResearchBot/1.0"}
all_records = []

print("=" * 60)
print(f"Fetching verified GBIF occurrences (taxonKey={APIS_KEY}) for 23 countries:")
print("=" * 60)

for iso in countries:
    try:
        url = "https://api.gbif.org/v1/occurrence/search"
        params = {
            "taxonKey": APIS_KEY,
            "country": iso,
            "hasCoordinate": "true",
            "limit": 50,  # Grab up to 50 verified sample geocoded points per country
        }
        r = requests.get(url, params=params, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            total_count = data.get("count", 0)
            results = data.get("results", [])
            print(f"  * {iso:<3}: Retrieved {len(results):>2} records | Total in GBIF: {total_count:>10,}")
            
            for rec in results:
                all_records.append({
                    "gbif_key": rec.get("key"),
                    "species": "Apis mellifera",
                    "subspecies": rec.get("infraspecificEpithet") or "",
                    "country": rec.get("country"),
                    "country_code": iso,
                    "state_province": rec.get("stateProvince") or "",
                    "latitude": rec.get("decimalLatitude"),
                    "longitude": rec.get("decimalLongitude"),
                    "event_date": rec.get("eventDate") or "",
                    "year": rec.get("year"),
                    "month": rec.get("month"),
                    "basis_of_record": rec.get("basisOfRecord") or "",
                    "institution_code": rec.get("institutionCode") or "",
                    "dataset_name": rec.get("datasetName") or "GBIF Occurrence Download",
                    "occurrence_id": rec.get("occurrenceID") or str(rec.get("key")),
                    "taxon_rank": rec.get("taxonRank") or "SPECIES",
                    "total_country_occurrences_in_gbif": total_count,
                })
    except Exception as e:
        print(f"  [ERROR] {iso}: {e}")

if all_records:
    df = pd.DataFrame(all_records)
    out_csv = RAW_DIR / "gbif_apis_mellifera_occurrences.csv"
    df.to_csv(out_csv, index=False)
    print("\n" + "=" * 60)
    print(f"Saved {len(df)} verified GBIF occurrence records to {out_csv.name}")
    print("=" * 60)

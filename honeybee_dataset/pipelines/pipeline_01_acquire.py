"""
Pipeline 01 - Data Acquisition
=================================
Downloads data from:
  - GBIF (Apis mellifera occurrences)
  - OpenAlex (research papers by Tofilski and related)
  - GBIF Plant occurrence records for each listed plant
  - World Clim / climate metadata (static lookup)

Outputs:
  - data/raw/gbif_apis_mellifera_occurrences.csv
  - data/raw/research_papers_metadata.csv
  - data/raw/plant_occurrences_gbif.csv
"""

import json
import os
import time
import requests
import pandas as pd
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent.parent
RAW_DIR    = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

SEED_FILE  = RAW_DIR / "region_plant_bee_seed.json"
GBIF_API   = "https://api.gbif.org/v1"
OPENALEX_API = "https://api.openalex.org"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def gbif_occurrence_search(taxon_key: int, country: str = None, limit: int = 300) -> list:
    """Fetch occurrences from GBIF with optional country filter."""
    params = {
        "taxonKey": taxon_key,
        "hasCoordinate": "true",
        "limit": limit,
    }
    if country:
        params["country"] = country

    resp = requests.get(f"{GBIF_API}/occurrence/search", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


def gbif_species_match(scientific_name: str) -> dict:
    """Match a species name to GBIF backbone."""
    resp = requests.get(
        f"{GBIF_API}/species/match",
        params={"name": scientific_name, "verbose": "false"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def openalex_search_papers(query: str, per_page: int = 25, pages: int = 4) -> list:
    """Search OpenAlex for research papers."""
    all_results = []
    for page in range(1, pages + 1):
        params = {
            "search": query,
            "per-page": per_page,
            "page": page,
            "mailto": "research@honeybee-dataset.org",  # polite pool
        }
        resp = requests.get(f"{OPENALEX_API}/works", params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  [WARN] OpenAlex page {page} failed: {resp.status_code}")
            break
        data = resp.json()
        results = data.get("results", [])
        if not results:
            break
        all_results.extend(results)
        time.sleep(0.5)  # rate limit courtesy
    return all_results


# ─── Step 1: Load seed data ────────────────────────────────────────────────────

def load_seed() -> dict:
    with open(SEED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── Step 2: Fetch Apis mellifera GBIF occurrences ────────────────────────────

def fetch_apis_mellifera_occurrences(seed: dict) -> pd.DataFrame:
    print("Fetching Apis mellifera occurrences from GBIF...")
    # GBIF taxon key for Apis mellifera: 1271638
    APIS_TAXON_KEY = 1271638
    iso_codes = list({r["iso_country"] for r in seed["regions"] if "iso_country" in r})

    all_records = []
    for iso in iso_codes:
        print(f"  Querying country: {iso}")
        try:
            records = gbif_occurrence_search(APIS_TAXON_KEY, country=iso, limit=300)
            for rec in records:
                all_records.append({
                    "gbif_key": rec.get("key"),
                    "species": rec.get("species"),
                    "subspecies": rec.get("infraspecificEpithet"),
                    "country": rec.get("country"),
                    "country_code": rec.get("countryCode"),
                    "state_province": rec.get("stateProvince"),
                    "latitude": rec.get("decimalLatitude"),
                    "longitude": rec.get("decimalLongitude"),
                    "event_date": rec.get("eventDate"),
                    "year": rec.get("year"),
                    "month": rec.get("month"),
                    "basis_of_record": rec.get("basisOfRecord"),
                    "institution_code": rec.get("institutionCode"),
                    "dataset_name": rec.get("datasetName"),
                    "occurrence_id": rec.get("occurrenceID"),
                    "taxon_rank": rec.get("taxonRank"),
                    "vernacular_name": rec.get("vernacularName"),
                })
            time.sleep(1)
        except Exception as e:
            print(f"  [ERROR] {iso}: {e}")

    df = pd.DataFrame(all_records)
    out = RAW_DIR / "gbif_apis_mellifera_occurrences.csv"
    df.to_csv(out, index=False)
    print(f"  Saved {len(df)} records -> {out.name}")
    return df


# ─── Step 3: Fetch plant GBIF occurrences ─────────────────────────────────────

def fetch_plant_occurrences(seed: dict) -> pd.DataFrame:
    print("Fetching plant occurrence data from GBIF...")
    plant_set = {}  # scientific_name -> taxon_key

    for region in seed["regions"]:
        for plant in region["plants"]:
            sn = plant["scientific_name"]
            if sn not in plant_set:
                plant_set[sn] = plant

    all_records = []
    for sn, plant_meta in plant_set.items():
        # Get primary name (first before /)
        query_name = sn.split("/")[0].strip()
        try:
            match = gbif_species_match(query_name)
            taxon_key = match.get("usageKey") or match.get("speciesKey")
            if not taxon_key:
                print(f"  [SKIP] No GBIF key for: {query_name}")
                continue
            records = gbif_occurrence_search(taxon_key, limit=100)
            for rec in records:
                all_records.append({
                    "plant_scientific_name": sn,
                    "plant_common_name": plant_meta["common_name"],
                    "plant_type": plant_meta["plant_type"],
                    "gbif_taxon_key": taxon_key,
                    "gbif_occ_key": rec.get("key"),
                    "country": rec.get("country"),
                    "country_code": rec.get("countryCode"),
                    "latitude": rec.get("decimalLatitude"),
                    "longitude": rec.get("decimalLongitude"),
                    "year": rec.get("year"),
                    "month": rec.get("month"),
                    "species_matched": rec.get("species"),
                    "basis_of_record": rec.get("basisOfRecord"),
                })
            time.sleep(0.8)
        except Exception as e:
            print(f"  [ERROR] {sn}: {e}")

    df = pd.DataFrame(all_records)
    out = RAW_DIR / "plant_occurrences_gbif.csv"
    df.to_csv(out, index=False)
    print(f"  Saved {len(df)} plant occurrence records -> {out.name}")
    return df


# ─── Step 4: Fetch research paper metadata (OpenAlex) ─────────────────────────

def fetch_research_papers() -> pd.DataFrame:
    print("Fetching research paper metadata from OpenAlex...")
    queries = [
        "Adam Tofilski Apis mellifera wing morphometrics",
        "Tofilski honey bee wing shape geometric morphometrics",
        "Apis mellifera subspecies geographic variation",
        "honey bee plant pollination relationship foraging",
        "Apis mellifera Kazakhstan Caucasus Iran wing",
        "Apis mellifera Cyprus Turkey Anatoliaca subspecies",
        "honey bee forage plant phenology bloom season",
        "Apis mellifera meda jemenitica syriaca Middle East",
        "honey bee Serbia Black Locust Linden honey production",
        "Apis mellifera conservation genetic diversity Europe",
    ]

    all_records = []
    for q in queries:
        print(f"  Query: '{q[:60]}'...")
        papers = openalex_search_papers(q, per_page=20, pages=3)
        for p in papers:
            authors = [a.get("author", {}).get("display_name", "") for a in p.get("authorships", [])]
            all_records.append({
                "openalex_id": p.get("id"),
                "doi": p.get("doi"),
                "title": p.get("title"),
                "publication_year": p.get("publication_year"),
                "cited_by_count": p.get("cited_by_count"),
                "is_open_access": p.get("open_access", {}).get("is_oa"),
                "journal": p.get("primary_location", {}).get("source", {}).get("display_name"),
                "authors": " | ".join(authors[:5]),
                "abstract": (p.get("abstract_inverted_index") or {}) and "<available>",
                "query_used": q,
                "concepts": " | ".join(
                    [c.get("display_name", "") for c in p.get("concepts", [])[:5]]
                ),
            })
        time.sleep(1)

    df = pd.DataFrame(all_records).drop_duplicates(subset=["openalex_id"])
    out = RAW_DIR / "research_papers_metadata.csv"
    df.to_csv(out, index=False)
    print(f"  Saved {len(df)} unique papers -> {out.name}")
    return df


# ─── Step 5: Build flat region-plant table from seed ─────────────────────────

def build_region_plant_flat(seed: dict) -> pd.DataFrame:
    print("Building flat region-plant table from seed JSON...")
    rows = []
    for region in seed["regions"]:
        base = {
            "continent": region.get("continent"),
            "country": region.get("country"),
            "iso_country": region.get("iso_country"),
            "region_name": region.get("region", region.get("country")),
            "latitude_approx": region.get("latitude_approx"),
            "longitude_approx": region.get("longitude_approx"),
            "climate_zone": region.get("climate_zone"),
            "known_subspecies": region.get("known_subspecies"),
            "bee_species": seed["species"]["scientific_name"],
            "bee_common_name": seed["species"]["common_name"],
        }
        for plant in region.get("plants", []):
            row = {**base, **{
                "plant_common_name": plant["common_name"],
                "plant_scientific_name": plant["scientific_name"],
                "plant_type": plant["plant_type"],
                "pollination_type": plant["pollination_type"],
                "honey_type": plant["honey_type"],
            }}
            rows.append(row)

    df = pd.DataFrame(rows)
    out = RAW_DIR / "region_plant_flat.csv"
    df.to_csv(out, index=False)
    print(f"  Saved {len(df)} region-plant rows -> {out.name}")
    return df


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Honeybee Dataset - Pipeline 01: Data Acquisition")
    print("=" * 60)

    seed = load_seed()

    flat_df   = build_region_plant_flat(seed)
    gbif_df   = fetch_apis_mellifera_occurrences(seed)
    plant_df  = fetch_plant_occurrences(seed)
    papers_df = fetch_research_papers()

    print("\n── Summary ──────────────────────────────────────────────")
    print(f"  Region-plant rows         : {len(flat_df)}")
    print(f"  GBIF bee occurrence rows  : {len(gbif_df)}")
    print(f"  GBIF plant occurrence rows: {len(plant_df)}")
    print(f"  Research papers           : {len(papers_df)}")
    print("Pipeline 01 complete. Run pipeline_02_enrich.py next.")


if __name__ == "__main__":
    main()

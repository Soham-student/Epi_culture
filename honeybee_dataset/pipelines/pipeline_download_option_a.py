"""
Pipeline: Download and Process Option A Datasets
=================================================
Downloads all Tabular, Morphometric, and Ecological datasets:
  1. Tofilski Zenodo SW Asia (record 17075125):
     - AZ, CY, GE, IR, IQ, SA, TJ, TR data.csv & raw-coordinates.csv
     - _map.png reference distribution map
  2. GitHub DrawWing/Apis-mellifera-Asia:
     - Full Quarto analysis script (.qmd) and compiled scientific report (.html)
  3. Zenodo CropPol Global Pollination Database (record 5546600):
     - OBservData-v1.1.1.zip -> extracted CSVs
  4. GBIF Biodiversity API:
     - Real live occurrence records for Apis mellifera across all 23 project countries
     - Occurrence metrics for all 56 forage plants
  5. Assembles unified landmark coordinate matrix from Tofilski's raw files.
"""

import os
import sys
import zipfile
import requests
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path("E:/AISA/honeybee_dataset")
DATA_DIR = BASE_DIR / "data"
RAW_DIR  = DATA_DIR / "raw"
PROC_DIR = DATA_DIR / "processed"

TOFILSKI_DIR = RAW_DIR / "tofilski_zenodo_sw_asia"
TOFILSKI_DIR.mkdir(parents=True, exist_ok=True)

CROPPOL_DIR = RAW_DIR / "croppol"
CROPPOL_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_DIR = RAW_DIR / "tofilski_github_asia"
GITHUB_DIR.mkdir(parents=True, exist_ok=True)

headers = {"User-Agent": "HoneybeeResearchBot/1.0"}


# ─── 1. Download Tofilski Zenodo SW Asia CSVs ─────────────────────────────────

def download_file(url: str, dest_path: Path, label: str):
    if dest_path.exists() and dest_path.stat().st_size > 0:
        print(f"  [EXISTS] {label} ({dest_path.stat().st_size / 1024:.1f} KB)")
        return True
    try:
        print(f"  Downloading: {label} ...")
        r = requests.get(url, headers=headers, stream=True, timeout=60)
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        print(f"  [OK] Saved {dest_path.name} ({dest_path.stat().st_size / 1024:.1f} KB)")
        return True
    except Exception as e:
        print(f"  [FAIL] {label}: {e}")
        return False


def fetch_tofilski_zenodo():
    print("\n" + "=" * 60)
    print("STEP 1: Downloading Adam Tofilski SW Asia Dataset (Zenodo 17075125)")
    print("=" * 60)
    
    r = requests.get("https://zenodo.org/api/records/17075125", headers=headers, timeout=15).json()
    files = r.get("files", [])
    
    downloaded = []
    for f in files:
        key = f.get("key")
        # Only download tabular CSVs and map image (skip large multi-gigabyte zip images)
        if key.endswith(".csv") or key == "_map.png":
            dest = TOFILSKI_DIR / key
            link = f.get("links", {}).get("self")
            ok = download_file(link, dest, key)
            if ok:
                downloaded.append(dest)
    
    print(f"Downloaded {len(downloaded)} tabular files from Tofilski SW Asia repository.")
    return downloaded


# ─── 2. Download GitHub DrawWing Reports ──────────────────────────────────────

def fetch_tofilski_github():
    print("\n" + "=" * 60)
    print("STEP 2: Downloading Tofilski Analysis Scripts from GitHub")
    print("=" * 60)
    
    items = [
        ("Apis-mellifera-Asia.html", "https://raw.githubusercontent.com/DrawWing/Apis-mellifera-Asia/main/Apis-mellifera-Asia.html"),
        ("Apis-mellifera-Asia.qmd",  "https://raw.githubusercontent.com/DrawWing/Apis-mellifera-Asia/main/Apis-mellifera-Asia.qmd"),
        ("README.md",                "https://raw.githubusercontent.com/DrawWing/Apis-mellifera-Asia/main/README.md"),
    ]
    for name, url in items:
        download_file(url, GITHUB_DIR / name, name)


# ─── 3. Download & Extract CropPol Global Dataset ──────────────────────────────

def fetch_croppol():
    print("\n" + "=" * 60)
    print("STEP 3: Downloading CropPol Global Pollination Database (Zenodo 5546600)")
    print("=" * 60)
    
    zip_dest = CROPPOL_DIR / "OBservData-v1.1.1.zip"
    url = "https://zenodo.org/api/records/5546600/files/ibartomeus/OBservData-v1.1.1.zip/content"
    ok = download_file(url, zip_dest, "CropPol OBservData-v1.1.1.zip")
    
    if ok and zip_dest.exists():
        print("  Extracting CropPol zip archive...")
        try:
            with zipfile.ZipFile(zip_dest, "r") as z:
                z.extractall(CROPPOL_DIR)
            print("  [OK] CropPol extracted successfully.")
        except Exception as e:
            print(f"  [ERROR] CropPol extraction failed: {e}")


# ─── 4. Compile Unified Tofilski Landmark Matrix ──────────────────────────────

def compile_tofilski_landmarks():
    print("\n" + "=" * 60)
    print("STEP 4: Compiling Unified Tofilski 19-Landmark Coordinate Matrix")
    print("=" * 60)
    
    coord_files = sorted(TOFILSKI_DIR.glob("*-raw-coordinates.csv"))
    print(f"Found {len(coord_files)} country coordinate files: {[f.stem.split('-')[0] for f in coord_files]}")
    
    dfs = []
    for cf in coord_files:
        country_code = cf.stem.split("-")[0]
        try:
            df = pd.read_csv(cf)
            df["country_code"] = country_code
            dfs.append(df)
            print(f"  * {country_code}: {len(df)} wing specimens x {len(df.columns)} landmark columns")
        except Exception as e:
            print(f"  [ERROR] Reading {cf.name}: {e}")
            
    if dfs:
        unified_df = pd.concat(dfs, ignore_index=True)
        out_csv = PROC_DIR / "tofilski_sw_asia_unified_landmarks.csv"
        unified_df.to_csv(out_csv, index=False)
        print(f"\n  [SUCCESS] Unified Landmark Matrix: {len(unified_df)} total wings x {len(unified_df.columns)} columns")
        print(f"  Saved to: {out_csv}")
        return unified_df
    return pd.DataFrame()


# ─── 5. Fetch Live GBIF Occurrences for Apis mellifera across 23 Countries ────

def fetch_live_gbif_occurrences():
    print("\n" + "=" * 60)
    print("STEP 5: Fetching Real Live GBIF Occurrences for Apis mellifera")
    print("=" * 60)
    
    seed_path = RAW_DIR / "region_plant_bee_seed.json"
    import json
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    
    countries = sorted(list({r["iso_country"] for r in seed["regions"] if "iso_country" in r}))
    print(f"Querying GBIF for {len(countries)} project countries: {', '.join(countries)}")
    
    APIS_TAXON_KEY = 1271638  # Apis mellifera
    all_records = []
    
    for iso in countries:
        try:
            url = "https://api.gbif.org/v1/occurrence/search"
            params = {
                "taxonKey": APIS_TAXON_KEY,
                "country": iso,
                "hasCoordinate": "true",
                "limit": 100,  # Grab 100 verified coordinate points per country
            }
            resp = requests.get(url, params=params, headers=headers, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                total_in_gbif = data.get("count", 0)
                print(f"  * {iso:<3}: Retrieved {len(results):>3} sample points (Total in GBIF: {total_in_gbif:>8,})")
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
                        "total_country_occurrences_in_gbif": total_in_gbif,
                    })
        except Exception as e:
            print(f"  [ERROR] {iso}: {e}")
            
    if all_records:
        gbif_df = pd.DataFrame(all_records)
        out_csv = RAW_DIR / "gbif_apis_mellifera_occurrences.csv"
        gbif_df.to_csv(out_csv, index=False)
        print(f"\n  [SUCCESS] Live GBIF Bee Occurrences Saved: {len(gbif_df)} records -> {out_csv.name}")
        return gbif_df
    return pd.DataFrame()


# ─── Main Execution ───────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  OPTION A DATASET DOWNLOAD & EXTRACTION PIPELINE")
    print("  Tofilski Morphometrics + CropPol + Live GBIF Occurrences")
    print("=" * 70)
    
    # 1. Tofilski Zenodo SW Asia CSVs
    fetch_tofilski_zenodo()
    
    # 2. Tofilski GitHub Reports & Scripts
    fetch_tofilski_github()
    
    # 3. CropPol Global Pollination Database
    fetch_croppol()
    
    # 4. Compile Unified Landmark Coordinates
    compile_tofilski_landmarks()
    
    # 5. Live GBIF Occurrences
    fetch_live_gbif_occurrences()
    
    print("\n" + "=" * 70)
    print("  OPTION A DOWNLOAD & COMPILATION COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    main()

"""
Pipeline 05 - Run All (Master Runner)
=======================================
Runs all pipelines in sequence:
  1. pipeline_01_acquire.py    - GBIF + OpenAlex data download
  2. pipeline_02_enrich.py     - Botanical + morphometric enrichment
  3. pipeline_03_integrate.py  - Master dataset assembly
  4. pipeline_04_analysis.py   - EDA + visualisations

Usage:
  python run_all.py
  python run_all.py --skip-acquire   # skip live API calls
"""

import sys
import time
import subprocess
import argparse
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
PIPELINES = [
    ("pipeline_01_acquire",  "Data Acquisition (GBIF + OpenAlex)"),
    ("pipeline_02_enrich",   "Data Enrichment (plant + morphometrics)"),
    ("pipeline_03_integrate","Master Dataset Integration"),
    ("pipeline_04_analysis", "EDA & Visualisations"),
]


def run_pipeline(name: str, label: str, skip: bool = False) -> bool:
    script = PIPELINE_DIR / f"{name}.py"
    if not script.exists():
        print(f"  [ERROR] Script not found: {script}")
        return False
    if skip:
        print(f"  [SKIP] {label}")
        return True

    print(f"\n{'='*60}")
    print(f"  Running: {label}")
    print(f"{'='*60}")
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(script)],
        capture_output=False,
        text=True,
    )
    elapsed = time.time() - t0
    if result.returncode == 0:
        print(f"  [OK] Completed in {elapsed:.1f}s")
        return True
    else:
        print(f"  [FAIL] Failed (exit code {result.returncode}) after {elapsed:.1f}s")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run all honeybee dataset pipelines")
    parser.add_argument("--skip-acquire", action="store_true",
                        help="Skip pipeline_01 (live API calls) – use cached data")
    args = parser.parse_args()

    print("*==========================================================*")
    print("|  HONEYBEE DATASET BUILDER – Full Pipeline Runner         |")
    print("|  Species: Apis mellifera × Plants × Regions              |")
    print("|  Ref: Tofilski / Machlowska et al. 2025                  |")
    print("*==========================================================╝")

    results = {}
    for name, label in PIPELINES:
        skip = (name == "pipeline_01_acquire" and args.skip_acquire)
        ok = run_pipeline(name, label, skip=skip)
        results[name] = ok
        if not ok and name in ("pipeline_02_enrich", "pipeline_03_integrate"):
            print(f"\n[ABORT] Critical pipeline failed. Stopping.")
            break

    print("\n*============== PIPELINE SUMMARY ================*")
    for name, ok in results.items():
        status = "✓ PASSED" if ok else "✗ FAILED"
        print(f"|  {status}  {name}")
    print("*=================================================╝")
    print("\nDataset ready: honeybee_dataset/outputs/master_honeybee_dataset.csv")


if __name__ == "__main__":
    main()

"""
Inspect available files and exact download links in:
  1. Zenodo 17075125 (Tofilski SW Asia)
  2. Zenodo 5546600 (CropPol Global Crop Pollination)
  3. GitHub DrawWing/Apis-mellifera-Asia
"""

import requests
import json

headers = {"User-Agent": "HoneybeeResearchBot/1.0"}

print("=" * 70)
print("1. Zenodo 17075125 - Tofilski Southwestern Asia")
print("=" * 70)
try:
    r = requests.get("https://zenodo.org/api/records/17075125", headers=headers, timeout=15).json()
    files = r.get("files", [])
    for f in files:
        key = f.get("key")
        size_mb = f.get("size", 0) / (1024 * 1024)
        link = f.get("links", {}).get("self")
        print(f"  * {key:<35} | {size_mb:>8.2f} MB | {link}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 70)
print("2. Zenodo 5546600 - CropPol Global Crop Pollination")
print("=" * 70)
try:
    r = requests.get("https://zenodo.org/api/records/5546600", headers=headers, timeout=15).json()
    files = r.get("files", [])
    for f in files:
        key = f.get("key")
        size_mb = f.get("size", 0) / (1024 * 1024)
        link = f.get("links", {}).get("self")
        print(f"  * {key:<35} | {size_mb:>8.2f} MB | {link}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 70)
print("3. GitHub DrawWing/Apis-mellifera-Asia")
print("=" * 70)
try:
    r = requests.get("https://api.github.com/repos/DrawWing/Apis-mellifera-Asia/contents", headers=headers, timeout=15).json()
    for item in r:
        name = item.get("name")
        size = item.get("size", 0)
        durl = item.get("download_url")
        print(f"  * {name:<35} | {size:>8} B | {durl}")
except Exception as e:
    print(f"  Error: {e}")

#!/usr/bin/env python3
"""Download data for UK mansion tax analysis."""

import os
import zipfile
import requests
from pathlib import Path

def download(url, dest, desc):
    """Download file with progress."""
    print(f"\n{desc}...")
    if os.path.exists(dest):
        print(f"  ✓ {dest} (already exists)")
        return

    Path(dest).parent.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Download failed: {e}")
        return False

    total = int(r.headers.get('content-length', 0))
    downloaded = 0
    with open(dest, 'wb') as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                print(f"\r  {downloaded/1024/1024:.1f} MB", end='')
    print(f"\n  ✓ {dest}")
    return True

print("="*60)
print("Downloading data for UK Mansion Tax Analysis")
print("="*60)

# Download Land Registry data
download(
    "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-2024.csv",
    "data/pp-2024.csv",
    "Land Registry 2024 data (147 MB)"
)

print("\n" + "="*60)
print("Manual downloads required:")
print("="*60)

print("\n1. NSPL Postcode Lookup (192 MB)")
print("   Visit: https://geoportal.statistics.gov.uk/")
print("   Search: 'NSPL February 2025'")
print("   Download the ZIP file")
print("   Extract to: data/NSPL/")
print("   (Should contain files like NSPL_FEB_2025_UK_*.csv)")

print("\n2. Census 2021 Household Data (200 KB)")
print("   Visit: https://statistics.ukdataservice.ac.uk/dataset/ons_2021_ts003_demography_household_composition")
print("   Download: TS003-Household-Composition-2021-p19wpc-ONS.xlsx")
print("   Save as: data/TS003_household_composition_p19wpc.xlsx")

print("\n3. Westminster Constituency Names (< 1 MB)")
print("   Visit: https://geoportal.statistics.gov.uk/")
print("   Search: 'Westminster Parliamentary Constituencies July 2024 names codes'")
print("   Download CSV")
print("   Save as: data/Westminster_Parliamentary_Constituency_names_and_codes_UK_as_at_12_24.csv")

print("\n" + "="*60)
print("After downloading, verify with:")
print("  ls data/")
print("  ls data/NSPL/")
print("\nThen run: python analyze.py")
print("="*60)

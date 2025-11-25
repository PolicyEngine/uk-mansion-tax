#!/usr/bin/env python3
"""Download data for UK mansion tax analysis."""

import os
import requests
from pathlib import Path
from mysoc_dataset import get_dataset_df

def download(url, dest, desc):
    """Download file with progress."""
    print(f"\n{desc}...")
    if os.path.exists(dest):
        print(f"  ✓ {dest} (already exists)")
        return True

    Path(dest).parent.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(url, stream=True, timeout=60)
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
                pct = (downloaded / total * 100) if total else 0
                print(f"\r  {downloaded/1024/1024:.1f} MB / {total/1024/1024:.1f} MB ({pct:.0f}%)", end='', flush=True)
    print(f"\n  ✓ {dest}")
    return True

def download_mysoc_data():
    """Download postcode and constituency data from MySoc."""
    Path("data").mkdir(parents=True, exist_ok=True)
    success = True

    # Postcodes
    postcodes_dest = "data/postcodes_with_con.csv"
    if os.path.exists(postcodes_dest):
        print(f"\n✓ {postcodes_dest} (already exists)")
    else:
        print(f"\n2a. MySoc Postcode Lookup...")
        try:
            postcodes = get_dataset_df(
                repo_name="2025-constituencies",
                package_name="uk_parliament_2025_postcode_lookup",
                version_name="latest",
                file_name="postcodes_with_con.csv",
                done_survey=True,
            )
            postcodes.to_csv(postcodes_dest, index=False)
            print(f"  ✓ {postcodes_dest} ({len(postcodes):,} postcodes)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            success = False

    # Constituency names
    const_dest = "data/constituencies.csv"
    if os.path.exists(const_dest):
        print(f"\n✓ {const_dest} (already exists)")
    else:
        print(f"\n2b. MySoc Constituency Names...")
        try:
            constituencies = get_dataset_df(
                repo_name="2025-constituencies",
                package_name="parliament_con_2025",
                version_name="latest",
                file_name="parl_constituencies_2025.csv",
                done_survey=True,
            )
            constituencies.to_csv(const_dest, index=False)
            print(f"  ✓ {const_dest} ({len(constituencies)} constituencies)")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            success = False

    return success

print("="*60)
print("Downloading data for UK Mansion Tax Analysis")
print("="*60)

success = True

# 1. Land Registry 2024 data
if not download(
    "http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-2024.csv",
    "data/pp-2024.csv",
    "1. Land Registry 2024 data (147 MB)"
):
    success = False

# 2. MySoc Postcode Lookup + Constituency Names
if not download_mysoc_data():
    success = False

# 3. HexJSON for constituency map visualization
if not download(
    "https://constituencies.open-innovations.org/assets/hexjson/uk-constituencies-2024.hexjson",
    "data/uk-constituencies-2024.hexjson",
    "3. HexJSON constituency layout (30 KB)"
):
    success = False

print("\n" + "="*60)
if success:
    print("✓ All downloads complete!")
    print("\nNext step: python analyze.py")
else:
    print("⚠ Some downloads failed - check errors above")
print("="*60)

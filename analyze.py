#!/usr/bin/env python3
"""
UK Mansion Tax Analysis - 2024

Analyzes property sales above £1.5m and £2m thresholds by Westminster constituency.
Uses MySoc 2025 constituency data for postcode matching.
"""

import pandas as pd
import sys
from pathlib import Path

def check_file(path, description):
    """Check if required file exists."""
    if not Path(path).exists():
        print(f"ERROR: Missing {description}")
        print(f"  Expected: {path}")
        print("\nRun: python download_data.py")
        sys.exit(1)

def load_postcode_mapping():
    """Load MySoc postcode to constituency mapping."""
    path = "data/postcodes_with_con.csv"
    check_file(path, "MySoc postcode lookup")
    print("Loading postcode mapping...")
    df = pd.read_csv(path, usecols=['postcode', 'short_code'])
    # Normalize postcodes (remove spaces, uppercase)
    df['postcode_norm'] = df['postcode'].str.replace(' ', '').str.upper()
    return df

def load_constituency_names():
    """Load MySoc constituency short_code to name mapping."""
    path = "data/constituencies.csv"
    check_file(path, "MySoc constituency names")
    df = pd.read_csv(path, usecols=['short_code', 'name'])
    return dict(zip(df['short_code'], df['name']))

def analyze_threshold(threshold, postcode_lookup, const_names):
    """Analyze properties above threshold by constituency."""
    print(f"\nProcessing £{threshold:,} threshold...")

    # Load and filter property data
    pp_path = 'data/pp-2024.csv'
    check_file(pp_path, "Land Registry 2024 data")

    df = pd.read_csv(pp_path, header=None, names=[
        'transaction_id', 'price', 'date', 'postcode', 'property_type',
        'old_new', 'duration', 'paon', 'saon', 'street', 'locality',
        'town', 'district', 'county', 'ppd_category', 'record_status'
    ])

    # Filter by price threshold
    df = df[df['price'] >= threshold]
    print(f"  {len(df):,} properties above £{threshold:,}")

    # Normalize postcodes and match to constituencies
    df['postcode_norm'] = df['postcode'].str.replace(' ', '').str.upper()
    df = df.merge(postcode_lookup[['postcode_norm', 'short_code']], on='postcode_norm', how='left')

    # Get constituency names
    df['constituency'] = df['short_code'].map(const_names)

    matched = df['constituency'].notna().sum()
    print(f"  {matched:,} matched to constituencies ({matched/len(df)*100:.1f}%)")

    # Calculate constituency stats
    stats = df[df['constituency'].notna()].groupby('constituency').agg(
        properties=('price', 'count'),
        mean_price=('price', 'mean'),
        median_price=('price', 'median'),
        total_value=('price', 'sum')
    ).round(0)

    stats['revenue'] = (stats['properties'] * 2000).astype(int)
    stats = stats.sort_values('properties', ascending=False)

    return stats.reset_index()

if __name__ == '__main__':
    print("="*60)
    print("UK Mansion Tax Analysis")
    print("="*60)

    print("\nLoading reference data...")
    postcode_lookup = load_postcode_mapping()
    const_names = load_constituency_names()
    print(f"  {len(postcode_lookup):,} postcodes, {len(const_names)} constituencies")

    # Analyze both thresholds
    stats_1_5m = analyze_threshold(1_500_000, postcode_lookup, const_names)
    stats_2m = analyze_threshold(2_000_000, postcode_lookup, const_names)

    # Save individual threshold files
    stats_1_5m.to_csv('constituency_impact_1m.csv', index=False)
    stats_2m.to_csv('constituency_impact_2m.csv', index=False)

    # Create merged output (blog format)
    merged = stats_1_5m[['constituency', 'properties', 'revenue']].rename(
        columns={'properties': 'properties_1.5m', 'revenue': 'revenue_1.5m'}
    ).merge(
        stats_2m[['constituency', 'properties', 'revenue']].rename(
            columns={'properties': 'properties_2m', 'revenue': 'revenue_2m'}
        ),
        on='constituency',
        how='outer'
    ).fillna(0)

    # Convert to int
    for col in ['properties_1.5m', 'revenue_1.5m', 'properties_2m', 'revenue_2m']:
        merged[col] = merged[col].astype(int)

    merged = merged.sort_values('properties_1.5m', ascending=False)
    merged.to_csv('mansion_tax_constituency_data.csv', index=False)

    print("\n" + "="*60)
    print("Results:")
    print(f"  £1.5m threshold: {stats_1_5m['properties'].sum():,} properties in {len(stats_1_5m)} constituencies")
    print(f"  £2m threshold: {stats_2m['properties'].sum():,} properties in {len(stats_2m)} constituencies")
    print("\nGenerated:")
    print("  constituency_impact_1m.csv")
    print("  constituency_impact_2m.csv")
    print("  mansion_tax_constituency_data.csv (merged)")
    print("="*60)

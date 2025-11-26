#!/usr/bin/env python3
"""
UK High Value Council Tax Surcharge Analysis - Autumn Budget 2025

Analyzes property sales to estimate the constituency-level impact of the
new high value council tax surcharge announced in the November 2025 budget.

Policy details (from OBR EFO November 2025):
- From April 2028, properties valued over £2m (in 2026 prices) face surcharge
- Bands: £2m-£2.5m: £2,500/yr, £2.5m-£3m: £3,500/yr, £3m-£5m: £5,000/yr, £5m+: £7,500/yr
- OBR estimates £0.4bn revenue in 2029-30

Methodology:
1. Uprate 2024 Land Registry sales to 2026 prices using OBR HPI forecast
2. Apply surcharge bands (defined in 2026 prices) to determine each property's charge
3. Calculate each constituency's share of total implied revenue
4. Allocate OBR's £0.4bn estimate proportionally by constituency
"""

import pandas as pd
import sys
from pathlib import Path

# OBR House Price Index forecast from November 2025 EFO
# Source: Table A.1 and paragraph 2.59
# "house prices grow just under 3 per cent in 2025 and average 2½ per cent
#  annual growth from 2026"
# Average house price: £260,000 (2024) -> ~£305,000 (2030)

# Annual HPI growth rates (percentage change on previous year)
HPI_GROWTH = {
    2024: 0.0,     # Base year
    2025: 2.9,     # "just under 3 per cent"
    2026: 2.5,     # "average 2½ per cent annual growth from 2026"
    2027: 2.5,
    2028: 2.4,     # Slightly lower due to property tax impact (-0.1pp)
    2029: 2.4,
    2030: 2.4,
}


def calculate_uprating_factor(growth_dict, from_year, to_year):
    """Calculate cumulative growth factor."""
    factor = 1.0
    for year in range(from_year + 1, to_year + 1):
        factor *= (1 + growth_dict[year] / 100)
    return factor


# Policy uses 2026 prices for property valuation
# We uprate 2024 sale prices to 2026 to compare against the £2m threshold
UPRATING_2024_TO_2026 = calculate_uprating_factor(HPI_GROWTH, 2024, 2026)

# Surcharge bands (in 2026 prices, uprated by CPI annually)
# For simplicity, we use the 2028 rates as stated in the policy
BANDS = [
    (2_000_000, 2_500_000, 2_500),   # £2m-£2.5m: £2,500
    (2_500_000, 3_000_000, 3_500),   # £2.5m-£3m: £3,500 (interpolated)
    (3_000_000, 5_000_000, 5_000),   # £3m-£5m: £5,000 (interpolated)
    (5_000_000, float('inf'), 7_500), # £5m+: £7,500
]

# OBR's estimated revenue in 2029-30 (post-behavioural)
OBR_REVENUE_2029_30 = 400_000_000  # £0.4 billion


def get_surcharge(value):
    """Calculate annual surcharge for a property value (in 2026 prices)."""
    if value < 2_000_000:
        return 0
    for lower, upper, charge in BANDS:
        if lower <= value < upper:
            return charge
    return BANDS[-1][2]  # Highest band


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
    df['postcode_norm'] = df['postcode'].str.replace(' ', '').str.upper()
    return df


def load_constituency_names():
    """Load MySoc constituency short_code to name mapping."""
    path = "data/constituencies.csv"
    check_file(path, "MySoc constituency names")
    df = pd.read_csv(path, usecols=['short_code', 'name'])
    return dict(zip(df['short_code'], df['name']))


def analyze():
    """Main analysis: calculate surcharge impact by constituency."""
    print("=" * 70)
    print("UK High Value Council Tax Surcharge Analysis")
    print("Based on OBR November 2025 Economic and Fiscal Outlook")
    print("=" * 70)

    print(f"\nHouse Price Uprating (2024 -> 2026):")
    print(f"  Annual growth rates: {HPI_GROWTH}")
    print(f"  Cumulative factor: {UPRATING_2024_TO_2026:.4f} "
          f"(+{(UPRATING_2024_TO_2026-1)*100:.1f}%)")

    print(f"\nSurcharge bands (properties valued over £2m in 2026 prices):")
    for lower, upper, charge in BANDS:
        if upper == float('inf'):
            print(f"  £{lower/1e6:.1f}m+: £{charge:,}/year")
        else:
            print(f"  £{lower/1e6:.1f}m-£{upper/1e6:.1f}m: £{charge:,}/year")

    print(f"\nOBR revenue estimate for 2029-30: £{OBR_REVENUE_2029_30/1e9:.1f}bn")

    # Load reference data
    print("\nLoading reference data...")
    postcode_lookup = load_postcode_mapping()
    const_names = load_constituency_names()
    print(f"  {len(postcode_lookup):,} postcodes, {len(const_names)} constituencies")

    # Load property data
    pp_path = 'data/pp-2024.csv'
    check_file(pp_path, "Land Registry 2024 data")

    print("\nLoading 2024 property sales...")
    df = pd.read_csv(pp_path, header=None, names=[
        'transaction_id', 'price', 'date', 'postcode', 'property_type',
        'old_new', 'duration', 'paon', 'saon', 'street', 'locality',
        'town', 'district', 'county', 'ppd_category', 'record_status'
    ])
    total_sales = len(df)
    print(f"  {total_sales:,} total sales in 2024")

    # Uprate 2024 prices to 2026 prices using HPI
    # Policy threshold is £2m in 2026 prices
    df['price_2026'] = df['price'] * UPRATING_2024_TO_2026

    # Filter to properties valued over £2m in 2026 prices
    df_scope = df[df['price_2026'] >= 2_000_000].copy()
    print(f"  {len(df_scope):,} sales valued above £2m in 2026 prices "
          f"({len(df_scope)/total_sales*100:.2f}% of sales)")

    # Calculate implied surcharge for each property (using 2026 prices for bands)
    df_scope['surcharge'] = df_scope['price_2026'].apply(get_surcharge)

    # Match to constituencies
    df_scope['postcode_norm'] = df_scope['postcode'].str.replace(' ', '').str.upper()
    df_scope = df_scope.merge(
        postcode_lookup[['postcode_norm', 'short_code']],
        on='postcode_norm',
        how='left'
    )
    df_scope['constituency'] = df_scope['short_code'].map(const_names)

    matched = df_scope['constituency'].notna().sum()
    print(f"  {matched:,} matched to constituencies ({matched/len(df_scope)*100:.1f}%)")

    # Calculate constituency statistics
    df_matched = df_scope[df_scope['constituency'].notna()]

    stats = df_matched.groupby('constituency').agg(
        properties=('price_2026', 'count'),
        mean_price=('price_2026', 'mean'),
        median_price=('price_2026', 'median'),
        total_value=('price_2026', 'sum'),
        implied_surcharge=('surcharge', 'sum')
    ).round(0)

    # Calculate share of total implied surcharge
    total_implied = stats['implied_surcharge'].sum()
    stats['share'] = stats['implied_surcharge'] / total_implied

    # Allocate OBR's £0.4bn proportionally
    stats['allocated_revenue'] = (stats['share'] * OBR_REVENUE_2029_30).round(0)

    stats = stats.sort_values('properties', ascending=False)

    # Band breakdown
    print("\nProperties by surcharge band:")
    for lower, upper, charge in BANDS:
        if upper == float('inf'):
            count = (df_matched['price_2026'] >= lower).sum()
            label = f"£{lower/1e6:.0f}m+"
        else:
            count = ((df_matched['price_2026'] >= lower) &
                     (df_matched['price_2026'] < upper)).sum()
            label = f"£{lower/1e6:.1f}m-£{upper/1e6:.1f}m"
        print(f"  {label}: {count:,} properties (£{charge:,}/yr each)")

    print(f"\nTotal implied surcharge from sales data: £{total_implied/1e6:.1f}m")
    print(f"OBR estimate (based on housing stock): £{OBR_REVENUE_2029_30/1e6:.0f}m")
    print(f"Ratio (stock/sales): ~{OBR_REVENUE_2029_30/total_implied:.0f}x")

    return stats.reset_index()


if __name__ == '__main__':
    stats = analyze()

    # Save outputs
    stats.to_csv('constituency_surcharge_impact.csv', index=False)

    # Create summary version for blog
    summary = stats[['constituency', 'properties', 'median_price',
                     'implied_surcharge', 'share', 'allocated_revenue']].copy()
    summary['share_pct'] = (summary['share'] * 100).round(2)
    summary = summary.drop(columns=['share'])
    summary = summary.rename(columns={
        'implied_surcharge': 'implied_from_sales',
        'allocated_revenue': 'allocated_from_obr'
    })
    summary.to_csv('constituency_surcharge_summary.csv', index=False)

    print("\n" + "=" * 70)
    print("Results:")
    print(f"  {len(stats)} constituencies with properties above £2m")
    print(f"  {stats['properties'].sum():,} total properties in analysis")
    print(f"  £{stats['allocated_revenue'].sum()/1e6:.0f}m total allocated revenue")
    print("\nTop 10 constituencies by property count:")
    for _, row in stats.head(10).iterrows():
        print(f"  {row['constituency']}: {int(row['properties'])} properties, "
              f"£{row['allocated_revenue']/1e6:.2f}m allocated")
    print("\nGenerated:")
    print("  constituency_surcharge_impact.csv (full data)")
    print("  constituency_surcharge_summary.csv (for blog)")
    print("=" * 70)

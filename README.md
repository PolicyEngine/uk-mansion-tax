# UK Mansion Tax Analysis

Analysis of property sales above £1.5m and £2m by Westminster constituency using 2024 Land Registry data.

Based on [FT article (Nov 2025)](https://www.ft.com/content/8e375410-dde2-43bc-8cc3-c6ae37c1aef3): Labour considering council tax surcharge on high-value properties (bands F/G/H), estimated £600m annual revenue from 145k-300k homes.

## Quick Start

```bash
pip install -r requirements.txt
python download_data.py           # Downloads all data
python analyze.py                 # Generates CSVs
python create_mansion_tax_map.py  # Generates hex map visualizations
```

## Results Summary

| Threshold | Properties | % of 2024 Sales | Constituencies |
|-----------|------------|-----------------|----------------|
| £1.5m | 13,884 | 1.57% | 567 |
| £2m | 7,849 | 0.89% | 553 |

**Top constituency:** Cities of London and Westminster (929 properties above £1.5m)

**Match rate:** 95.2% of high-value properties matched to constituencies

## Output Files

**Analysis (CSV):**
- `constituency_impact_1m.csv` - Properties, prices, revenue by constituency (£1.5m threshold)
- `constituency_impact_2m.csv` - Properties, prices, revenue by constituency (£2m threshold)
- `mansion_tax_constituency_data.csv` - Merged data for both thresholds

**Visualizations:**
- `mansion_tax_map_1m.html` / `.png` - Hex cartogram (£1.5m threshold)
- `mansion_tax_map_2m.html` / `.png` - Hex cartogram (£2m threshold)

## Data Sources

- [UK Land Registry Price Paid Data 2024](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads) - 881,757 transactions
- [MySoc 2025 Constituencies](https://github.com/mysociety/2025-constituencies) - Postcode lookup (1.7M postcodes) and constituency names
- [Open Innovations UK Constituencies HexJSON](https://constituencies.open-innovations.org/) - Hex cartogram layout

## Note

This analysis uses 2024 **sales** data, not total housing stock. Actual policy impact would be ~10-20x larger (sales represent 5-10% of stock annually).

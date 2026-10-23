# UK High Value Council Tax Surcharge Analysis

Analysis of the High Value Council Tax Surcharge (the "mansion tax") by Westminster constituency.

## 2028-29 constituency estimates

[`constituency_estimates_2028_29.html`](https://policyengine.github.io/uk-mansion-tax/constituency_estimates_2028_29.html) is an embeddable map and table of the estimated static revenue from the surcharge in 2028-29, its first year, for each constituency in England. It has three tabs: a hex map, a map of the constituencies' own boundaries, and a table of all 543 constituencies. Like the 2025 map, it is made for an iframe in a PolicyEngine blog post, which carries the methodology and the analysis:

```html
<center><iframe src="https://policyengine.github.io/uk-mansion-tax/constituency_estimates_2028_29.html" width="100%" height="850" style="border:none;"></iframe></center>
```

The page fills the iframe's height, so it works at other heights too. It is also the site's landing page.

- **What it shows.** Owner-occupied main residences worth over £2m at April 2026 values, under the announced schedule: £2,500 a year for £2m–£2.5m, £3,500 for £2.5m–£3.5m, £5,000 for £3.5m–£5m and £7,500 above £5m. These are experimental modelled estimates from survey microdata, with wide uncertainty, not official statistics.
- **Data.** PolicyEngine's Microcosm UK 2024-25 local-area release, cut `microcosm-uk-2024-25-dense-20261019T000432Z-ee5c2dbe` (150,000 households), run with policyengine-uk 2.132.6. Household numbers grow from 2024-25 to 2028-29 with the ONS projection of UK population, as in policyengine-uk. The microdata are licensed from the UK Data Service and are not in this repository.
- **Privacy.** 110 of the 543 constituencies are reported; the other 433 are hatched grey, because fewer than 10 survey households above £2m sit behind their estimates. Every estimate carries keyed noise: each survey household's weight is multiplied by a fixed secret factor between 8% and 12% away from 1.
- **Files.** In `estimates_2028_29/`: `constituency_estimates_2028_29.csv` (every constituency), `estimates_2028_29_summary.json` (national revenue for 2028-29 to 2030-31, coverage, uncertainty, and the regional, income-decile and support-scheme figures the blog post cites), `constituencies_2024_hex.csv` (the hex layout) and `constituencies_2024_england_paths.json` (the 2024 boundaries of the English constituencies, simplified to about 250 m by `prepare_estimates_2028_29_boundaries.py` from the boundaries the 2025 map embeds; contains OS data © Crown copyright and database right 2024). The estimates come from PolicyEngine's disclosure-controlled analysis of the microdata, which is internal. Rebuild the page with `python create_estimates_2028_29_map.py`, which needs only the Python standard library.

The analysis below is the original November 2025 version. Its map, `surcharge_map_by_revenue.html`, is kept unchanged because PolicyEngine's article on the 2025 Budget embeds it.

## 2025 analysis: Land Registry sales

Analysis of the high value council tax surcharge announced in the November 2025 UK Budget, estimating revenue allocation by Westminster constituency.

## Policy Summary

From the [OBR Economic and Fiscal Outlook (November 2025)](https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/):

- **Effective date**: April 2028
- **Threshold**: Properties valued over £2 million (in 2026 prices)
- **Surcharge bands**:
  - £2m-£2.5m: £2,500/year
  - £2.5m-£3m: £3,500/year
  - £3m-£5m: £5,000/year
  - £5m+: £7,500/year
- **Revenue estimate**: £0.4 billion in 2029-30 (post-behavioural)
- Revenue flows to central government (not local authorities)

## Methodology

1. **Property data**: 2024 Land Registry Price Paid data (881,757 transactions)
2. **Price uprating**: Uprate 2024 sale prices to 2029-30 using OBR house price growth forecasts (~13.4% cumulative)
3. **Surcharge calculation**: Apply band structure to each property above £2m threshold
4. **Allocation**: Calculate each constituency's share of total implied surcharge from sales data, then allocate OBR's £400m estimate proportionally

### Key Limitation

This analysis uses **sales data**, not housing stock. Property sales represent ~5-10% of stock annually. The OBR's £400m estimate is based on the full housing stock (via Valuation Office data). Our analysis found:

- Implied surcharge from 2024 sales: £44.3m
- OBR estimate (housing stock): £400m
- Ratio: ~9x (consistent with stock/sales relationship)

We allocate the OBR total proportionally by constituency based on sales patterns.

## Quick Start

```bash
pip install -r requirements.txt
python download_data.py              # Downloads all data
python analyze_autumn_budget.py      # Generates constituency analysis
python create_surcharge_map.py       # Generates hex map visualizations
```

## Results Summary

| Metric | Value |
|--------|-------|
| Sales above £2m (2024, uprated to 2029) | 10,371 |
| % of 2024 sales | 1.18% |
| Constituencies with sales above £2m | 559 |
| Total OBR revenue estimate | £400m |

**Top 5 constituencies by allocated revenue:**

| Constituency | Sales | Allocated Revenue | Share |
|--------------|------------|-------------------|-------|
| Cities of London and Westminster | 811 | £39.8m | 9.9% |
| Kensington and Bayswater | 634 | £28.4m | 7.1% |
| Chelsea and Fulham | 440 | £17.7m | 4.4% |
| Hampstead and Highgate | 286 | £11.6m | 2.9% |
| Richmond Park | 186 | £7.0m | 1.8% |

## Output Files

**Analysis:**
- `constituency_surcharge_impact.csv` - Full data with all metrics
- `constituency_surcharge_summary.csv` - Summary for blog/visualization

**Visualizations:**
- `surcharge_map_by_properties.html/png` - Hex cartogram by property count
- `surcharge_map_by_revenue.html/png` - Hex cartogram by allocated revenue

**Legacy (pre-budget analysis):**
- `constituency_impact_1m.csv`, `constituency_impact_2m.csv` - Original threshold analysis
- `mansion_tax_map_*.html/png` - Original visualizations

## Data Sources

- [UK Land Registry Price Paid Data 2024](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads)
- [OBR Economic and Fiscal Outlook November 2025](https://obr.uk/efo/economic-and-fiscal-outlook-november-2025/)
- [MySoc 2025 Constituencies](https://github.com/mysociety/2025-constituencies)
- [Open Innovations UK Constituencies HexJSON](https://constituencies.open-innovations.org/)

## License

Code in this repository is released under the [MIT License](LICENSE). Original text and figures are released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) with attribution to PolicyEngine. Third-party data and materials keep their own terms.

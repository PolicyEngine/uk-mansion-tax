"""Build constituency_estimates_2028_29.html, the 2028-29 constituency map of the surcharge.

    python create_estimates_2028_29_map.py

Reads estimates_2028_29/constituency_estimates_2028_29.csv and
estimates_2028_29/estimates_2028_29_summary.json (exported from PolicyEngine's
disclosure-controlled analysis of Microcosm UK data),
estimates_2028_29/constituencies_2024_hex.csv (the ODI hex layout of the 2024
constituencies), estimates_2028_29/constituencies_2024_england_paths.json
(their simplified boundaries, from prepare_estimates_2028_29_boundaries.py)
and estimates_2028_29/policyengine_logo.svg. Needs only the Python standard
library.
"""

import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "estimates_2028_29"
OUT = HERE / "constituency_estimates_2028_29.html"


def hex_centres(rows):
    """Pointy-top hexes; odd rows are shifted right by half a hex; y grows northward."""
    cx = [(int(r["x"]) + (abs(int(r["y"])) % 2) * 0.5) * math.sqrt(3) for r in rows]
    cy = [-int(r["y"]) * 1.5 for r in rows]
    return [x - min(cx) + 1 for x in cx], [y - min(cy) + 1 for y in cy]


def pct(x):
    return f"{100 * x:.0f}%"


def about(shares):
    """The shares' mean to the nearest 5 points, if every share is within 5 points of it."""
    rounded = 5 * round(20 * sum(shares) / len(shares))
    assert all(abs(100 * s - rounded) <= 5 for s in shares), "the shares are too far apart for one 'about' figure"
    return f"{rounded}%"


def main():
    with open(DATA / "constituencies_2024_hex.csv", newline="") as f:
        hexes = list(csv.DictReader(f))
    with open(DATA / "constituency_estimates_2028_29.csv", newline="") as f:
        estimates = {r["code"]: r for r in csv.DictReader(f)}
    summary = json.loads((DATA / "estimates_2028_29_summary.json").read_text())
    assert summary["revenue_year"] == "2028-29"

    cx, cy = hex_centres(hexes)
    seats = []
    for r, x, y in zip(hexes, cx, cy):
        e = estimates[r["code"]]
        seats.append({"code": r["code"], "name": r["name"], "region": r["region"], "cx": round(x, 3), "cy": round(y, 3),
                      "v": float(e["revenue_m"]) if e["revenue_m"] else None})
    release = summary["release"]
    private = summary["share_of_private_sector_2m_homes_in_shown_seats"]
    owner = summary["share_of_owner_occupied_2m_homes_in_shown_seats"]
    low, high = summary["england_revenue_90pct_interval_m"]
    text = {
        "SEATS_SHOWN": str(summary["seats_shown"]),
        "SEATS_HIDDEN": str(summary["seats"] - summary["seats_shown"]),
        "SEATS": str(summary["seats"]),
        "COVER_ABOUT": about([private, owner]),
        "COVER_PRIVATE": pct(private),
        "COVER_OWNER": pct(owner),
        "TOP_20": str(summary["top_20_and_50_seats_by_2m_homes_shown"][0]),
        "REVENUE": f"£{summary['england_revenue_current_law_m']}m",
        "INTERVAL": f"£{low}m–£{high}m",
        "HOMES": f"{summary['england_homes_2m_plus_k']:,}",
        "CV": pct(summary["median_coefficient_of_variation_of_shown_seats"]),
        "TOP20_KEPT": str(summary["median_top20_seats_kept_in_a_resample"]),
        "RHO": f"{summary['rank_correlation_with_voa_band_h']:.2f}",
        "CUT": release["cut"],
        "SHA": release["sha256"][:12],
        "HOUSEHOLDS": f"{release['households']:,}",
        "PE": release["policyengine"],
        "PE_UK": release["policyengine_uk"],
        "LOGO": (DATA / "policyengine_logo.svg").read_text().strip().replace(
            'width="996" height="207"', 'class="logo" role="img" aria-label="PolicyEngine"', 1),
    }
    page = TEMPLATE
    for key, value in text.items():
        page = page.replace("{{" + key + "}}", value)
    boundaries = json.loads((DATA / "constituencies_2024_england_paths.json").read_text())
    assert set(boundaries["paths"]) == {s["code"] for s in seats}, "every constituency needs a boundary"
    payload = {"seats": seats, "width": round(max(cx) + 1, 3), "height": round(max(cy) + 1, 3),
               "geo": {k: boundaries[k] for k in ("width", "height", "paths")}}
    page = page.replace("/*DATA*/null", json.dumps(payload, separators=(",", ":")))
    assert "{{" not in page and 'class="logo"' in page, "unfilled placeholder"
    OUT.write_text(page)
    print(f"wrote {OUT}")


# Colours, type and radii follow PolicyEngine's design tokens (@policyengine/ui-kit):
# teal brand scale, Inter, gray-200 borders.
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mansion tax by constituency: 2028-29 estimates | PolicyEngine</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: light;
    --background:#ffffff; --foreground:#101828; --body:#344054; --muted:#475569; --subtle:#64748b;
    --border:#e2e8f0; --border-medium:#cbd5e1; --muted-bg:#f2f4f7; --tint:#f8fafc;
    --primary:#2c7a7b; --primary-dark:#285e61; --ring:#319795; --zero:#f2f4f7; --zero-line:#cbd5e1;
  }
  * { box-sizing:border-box; }
  [hidden] { display:none !important; }
  body { margin:0; background:var(--background); color:var(--foreground); font:16px/1.55 Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; -webkit-font-smoothing:antialiased; }
  a { color:var(--primary); text-decoration:none; }
  a:hover { color:var(--primary-dark); text-decoration:underline; }
  .bar { max-width:1080px; margin:0 auto; padding:0 20px; }
  header.site { border-bottom:1px solid var(--border); }
  header.site .bar { height:58px; display:flex; align-items:center; }
  header.site .logo { height:24px; width:auto; display:block; }
  main.bar { padding-top:32px; padding-bottom:40px; }
  h1 { font-size:32px; line-height:40px; font-weight:700; letter-spacing:-0.01em; margin:0 0 12px; }
  @media (max-width: 600px) { h1 { font-size:26px; line-height:32px; } .intro { font-size:16px; line-height:26px; } }
  .nowrap { white-space:nowrap; }
  .intro { font-size:17px; line-height:28px; color:var(--body); max-width:860px; margin:0 0 24px; }
  .facts { display:grid; grid-template-columns:repeat(auto-fit, minmax(230px, 1fr)); gap:12px; margin:0 0 24px; }
  .fact { border:1px solid var(--border); border-radius:8px; padding:16px; background:var(--background); }
  .fact b { display:block; font-size:24px; line-height:32px; font-weight:600; color:var(--primary-dark); }
  .fact span { display:block; margin-top:4px; font-size:14px; line-height:20px; color:var(--muted); }
  .panel { border:1px solid var(--border); border-radius:12px; padding:16px; background:var(--background); }
  .toolbar { display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; margin:0 0 12px; }
  .tabs { display:inline-flex; gap:2px; padding:4px; background:var(--muted-bg); border-radius:8px; }
  .tabs button { border:0; background:transparent; color:var(--muted); font:inherit; font-size:14px; font-weight:500; line-height:20px; padding:6px 14px; border-radius:6px; cursor:pointer; }
  .tabs button:hover { color:var(--foreground); }
  .tabs button[aria-selected="true"] { background:var(--background); color:var(--foreground); box-shadow:0 1px 2px rgba(16,24,40,.1); }
  .zoom { display:inline-flex; gap:6px; }
  .zoom button { border:1px solid var(--border); background:var(--background); color:var(--foreground); font:inherit; font-size:14px; line-height:20px; padding:5px 11px; border-radius:6px; cursor:pointer; }
  .zoom button:hover { background:var(--tint); }
  button:focus-visible, input:focus-visible, th button:focus-visible { outline:2px solid var(--ring); outline-offset:2px; }
  .mapview-wrap { display:grid; grid-template-columns:minmax(0, 1fr) 250px; gap:20px; align-items:start; }
  @media (max-width: 820px) { .mapview-wrap { grid-template-columns:1fr; } }
  svg.mapview { width:100%; height:auto; max-height:min(62vh, 540px); margin:8px 0; display:block; cursor:grab; touch-action:pan-y; }
  svg.mapview.dragging { cursor:grabbing; }
  .hex { stroke:var(--background); stroke-width:0.12; }
  .hex:hover { stroke:var(--foreground); stroke-width:0.25; }
  .geo { stroke:var(--background); stroke-width:0.5; vector-effect:non-scaling-stroke; }
  .geo:hover { stroke:var(--foreground); stroke-width:1.5; }
  .legend { font-size:13px; line-height:18px; color:var(--muted); }
  .legend h2 { font-size:14px; line-height:20px; font-weight:600; color:var(--foreground); margin:0 0 6px; }
  .ramp { height:10px; border-radius:2px; margin:4px 0; }
  .ticks { display:flex; justify-content:space-between; }
  .legend .key { display:flex; gap:8px; align-items:flex-start; margin:12px 0 0; }
  .legend .key svg { flex:none; margin-top:2px; }
  .legend .hint { margin:12px 0 0; }
  .note { font-size:13px; line-height:18px; color:var(--muted); margin:0 0 14px; }
  .table-tools { display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin:0 0 12px; }
  .table-tools input { flex:1 1 260px; max-width:380px; font:inherit; font-size:14px; padding:8px 12px; border:1px solid var(--border-medium); border-radius:6px; color:var(--foreground); }
  .table-tools span { font-size:13px; color:var(--muted); }
  .table-wrap { max-height:min(70vh, 640px); overflow:auto; border:1px solid var(--border); border-radius:8px; }
  table { width:100%; border-collapse:collapse; font-size:14px; line-height:20px; }
  th, td { text-align:left; padding:8px 12px; border-bottom:1px solid var(--border); }
  thead th { position:sticky; top:0; background:var(--tint); z-index:1; font-weight:600; color:var(--foreground); }
  th button { all:unset; cursor:pointer; }
  th button::after { content:""; margin-left:4px; color:var(--subtle); }
  th[aria-sort="ascending"] button::after { content:"▲"; font-size:10px; }
  th[aria-sort="descending"] button::after { content:"▼"; font-size:10px; }
  td.num, th.num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }
  td.rank { color:var(--subtle); width:3em; }
  td.na { color:var(--subtle); }
  tbody tr:hover { background:var(--tint); }
  .table-foot { font-size:13px; color:var(--muted); margin:10px 0 0; }
  .in-name, .short { display:none; }
  td .in-name { font-size:12px; line-height:16px; color:var(--subtle); }
  @media (max-width: 600px) { .col-region, .long { display:none; } .in-name { display:block; } .short { display:inline; } th, td { padding:8px; } }
  details { border:1px solid var(--border); border-radius:12px; margin-top:24px; }
  summary { list-style:none; cursor:pointer; padding:16px; font-weight:600; display:flex; justify-content:space-between; align-items:center; }
  summary::-webkit-details-marker { display:none; }
  summary::after { content:"+"; color:var(--primary); font-size:20px; font-weight:500; line-height:1; }
  details[open] summary::after { content:"−"; }
  details .body { padding:0 16px 6px; }
  details p { margin:0 0 12px; font-size:15px; line-height:24px; color:var(--body); }
  details b { color:var(--foreground); }
  code { font-family:"JetBrains Mono", "Fira Code", Consolas, monospace; font-size:12.5px; word-break:break-all; }
  footer.site { border-top:1px solid var(--border); }
  footer.site .bar { padding-top:16px; padding-bottom:24px; font-size:13px; color:var(--muted); }
  #tip { position:fixed; pointer-events:none; background:var(--background); color:var(--foreground); border:1px solid var(--border); border-radius:8px; padding:8px 12px; font-size:13px; line-height:18px; box-shadow:0 4px 16px rgba(16,24,40,.12); display:none; max-width:280px; z-index:10; }
  #tip .t { font-weight:600; }
  #tip .m { color:var(--muted); }
</style>
</head>
<body>
<header class="site"><div class="bar"><a href="https://policyengine.org/uk" aria-label="PolicyEngine home">{{LOGO}}</a></div></header>
<main class="bar">
<h1>Mansion tax by constituency: <span class="nowrap">2028-29</span> estimates</h1>
<p class="intro">Estimated static revenue from the High Value Council Tax Surcharge in 2028-29, its first year, for each Westminster constituency in England. These are experimental modelled estimates from PolicyEngine's Microcosm survey microdata, with wide uncertainty; they are not official statistics. The map reports the {{SEATS_SHOWN}} constituencies with enough survey data, which hold about {{COVER_ABOUT}} of England's homes worth over £2m ({{COVER_PRIVATE}} of privately owned ones and {{COVER_OWNER}} of owner-occupied ones, by Land Registry-based counts). The other {{SEATS_HIDDEN}}, hatched grey, have too few survey households above £2m to report; most have few such homes.</p>
<div class="facts">
  <div class="fact"><b>{{REVENUE}} a year</b><span>England, static, owner-occupied main residences (90% range {{INTERVAL}})</span></div>
  <div class="fact"><b>about {{HOMES}},000 homes</b><span>owner-occupied homes worth over £2m at April 2026 values</span></div>
  <div class="fact"><b>£605m static, £400m after behaviour</b><span>OBR costing, all liable properties</span></div>
</div>
<section class="panel" aria-label="Estimated revenue by constituency">
  <div class="toolbar">
    <div class="tabs" role="tablist" aria-label="View">
      <button role="tab" id="t-hex" aria-selected="true">Hex map</button>
      <button role="tab" id="t-geo" aria-selected="false">Geographic</button>
      <button role="tab" id="t-table" aria-selected="false">Table</button>
    </div>
    <div class="zoom" id="zoom"><button id="zin" aria-label="Zoom in">+</button><button id="zout" aria-label="Zoom out">−</button><button id="zreset">Reset</button></div>
  </div>
  <div class="mapview-wrap" id="p-map" role="tabpanel">
    <div>
      <svg class="mapview" id="hexmap" role="img" aria-label="Hex map of constituencies in England coloured by estimated surcharge revenue in 2028-29; constituencies not reported are hatched grey"></svg>
      <svg class="mapview" id="geomap" role="img" style="display:none" aria-label="Map of constituencies in England, with their boundaries, coloured by estimated surcharge revenue in 2028-29; constituencies not reported are hatched grey"></svg>
    </div>
    <div class="legend">
      <p class="note">Estimated static revenue in 2028-29. Experimental modelled estimates from survey microdata, with wide uncertainty; not official statistics. Source: PolicyEngine, Microcosm UK.</p>
      <h2>Estimated revenue a year</h2>
      <div class="ramp" id="ramp"></div>
      <div class="ticks"><span>£0</span><span id="tmid"></span><span id="tmax"></span></div>
      <div>Square-root scale</div>
      <div class="key"><svg width="16" height="16" aria-hidden="true"><rect width="16" height="16" rx="2" fill="url(#hatch-key)"></rect></svg><span>Not reported: fewer than 10 survey households above £2m</span></div>
      <p class="hint">Zoom with + and −, or hold Ctrl or ⌘ and scroll; drag to pan. Hover over or tap a constituency for its estimate.</p>
    </div>
  </div>
  <div id="p-table" role="tabpanel" hidden>
    <p class="note">Estimated static revenue in 2028-29. Experimental modelled estimates from survey microdata, with wide uncertainty; not official statistics. Source: PolicyEngine, Microcosm UK.</p>
    <div class="table-tools"><input type="search" id="q" placeholder="Search by constituency or region" aria-label="Search by constituency or region"><span id="count"></span></div>
    <div class="table-wrap">
      <table>
        <thead><tr><th class="num">#</th><th aria-sort="none"><button data-key="name">Constituency</button></th><th class="col-region" aria-sort="none"><button data-key="region">Region</button></th><th class="num" aria-sort="descending"><button data-key="v"><span class="long">Estimated revenue a year</span><span class="short">A year</span></button></th></tr></thead>
        <tbody id="rows"></tbody>
      </table>
    </div>
    <p class="table-foot">Download all {{SEATS}} constituencies: <a href="estimates_2028_29/constituency_estimates_2028_29.csv">constituency_estimates_2028_29.csv</a>.</p>
  </div>
</section>
<details>
<summary>How these estimates are made, and their limits</summary>
<div class="body">
<p><b>Modelled, not observed.</b> These are estimates from survey-based microdata, not counts of real homes or bills. Seat estimates are uncertain: for a typical constituency shown, the standard error is about {{CV}} of the estimate, and the ranking of the largest seats is steadier (a resample keeps {{TOP20_KEPT}} of the top 20). These measures, like the 90% range for England ({{INTERVAL}}), come from resampling the survey households only; they leave out calibration and modelling error, so the true uncertainty is larger. They follow the pattern of council tax band H homes closely (rank correlation {{RHO}}), and the {{SEATS_SHOWN}} seats shown include all of the {{TOP_20}} constituencies with the most homes over £2m.</p>
<p><b>Data.</b> Microcosm UK 2024-25 local-area release (cut <code>{{CUT}}</code>, {{HOUSEHOLDS}} households, SHA-256 <code>{{SHA}}…</code>), PolicyEngine's synthetic microdata built from the Family Resources Survey and other UK Data Service surveys and calibrated to official local statistics. Each owner's home takes its value from its constituency's Land Registry sale prices at the household's rank among owners in its region, and the release is calibrated to Land Registry counts of owner-occupied homes over £1m, £1.5m and £2m by region and local authority. policyengine {{PE}} loads this release for constituency results, with policyengine-uk {{PE_UK}}. Its certificate covers the national release built from the same data, not constituency results from this local-area release, so these seat figures are not certified. Revenue applies the surcharge as policyengine-uk {{PE_UK}} defines it to each household's modelled home value. The microdata are licensed and not public.</p>
<p><b>Year and values.</b> Revenue is for 2028-29, the surcharge's first year, at that year's charges. Homes are valued at April 2026 prices, as the surcharge values them until its first revaluation (revaluations are every five years). policyengine-uk uprates 2024 values to 2026 by GDP per capita (+7.4%); house prices (+5.3%) would put fewer homes over each threshold. Household numbers grow from 2024-25 to 2028-29 with the ONS population projection (+1.9%), as in policyengine-uk.</p>
<p><b>Policy.</b> England only, from April 2028, owners liable: £2,500 a year for homes worth £2m–£2.5m, £3,500 for £2.5m–£3.5m, £5,000 for £3.5m–£5m and £7,500 above £5m. Revenue is static: no behaviour, appeals, non-payment or deferral.</p>
<p><b>Coverage.</b> Only owner-occupied main residences are modelled, so second homes and let or company-owned homes are missing. Their share is uncertain: the OBR puts non-owner-occupied homes at about 40% of liable properties (from stamp duty data), while MHCLG's Market Value Survey, cited in the May 2026 consultation, found over 90% of homes worth £2m or more owner occupied in 2024.</p>
<p><b>Privacy.</b> The survey data are licensed from the UK Data Service. To protect respondents, a constituency is reported only if at least 10 survey households above £2m sit behind its estimate, and every estimate from the survey microdata carries keyed noise: each survey household's weight is multiplied by a fixed secret factor between 8% and 12% away from 1. That typically moves a constituency's estimate by a few per cent, more where one household carries much of it.</p>
<p><b>Maps and table.</b> The hex map gives every constituency the same size, so small urban seats stay visible; the geographic map shows the 2024 constituency boundaries (contains OS data © Crown copyright and database right 2024), simplified to about 250 m. The table lists all {{SEATS}} constituencies.</p>
<p><b>Earlier map.</b> The <a href="surcharge_map_by_revenue.html">November 2025 map</a> allocated the OBR's estimate by 2024 Land Registry sales; it is kept unchanged for the article that embeds it.</p>
</div>
</details>
</main>
<footer class="site"><div class="bar">PolicyEngine. Code and data: <a href="https://github.com/PolicyEngine/uk-mansion-tax">github.com/PolicyEngine/uk-mansion-tax</a>.</div></footer>
<div id="tip"></div>
<svg width="0" height="0" style="position:absolute" aria-hidden="true">
  <defs><pattern id="hatch" width="0.45" height="0.45" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="0.45" height="0.45" style="fill:var(--zero)"></rect><line x1="0" y1="0" x2="0" y2="0.45" style="stroke:var(--zero-line)" stroke-width="0.1"></line>
  </pattern>
  <pattern id="hatch-geo" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="16" height="16" style="fill:var(--zero)"></rect><line x1="0" y1="0" x2="0" y2="16" style="stroke:var(--zero-line)" stroke-width="4"></line>
  </pattern>
  <pattern id="hatch-key" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="5" height="5" style="fill:var(--zero)"></rect><line x1="0" y1="0" x2="0" y2="5" stroke="#94a3b8" stroke-width="1.4"></line>
  </pattern></defs>
</svg>
<script>
const DATA = /*DATA*/null;
// PolicyEngine's teal scale, teal-100 to teal-900.
const RAMP = ["#b2f5ea", "#81e6d9", "#4fd1c5", "#38b2ac", "#319795", "#2c7a7b", "#285e61", "#234e52", "#1d4044"];
const max = Math.max(...DATA.seats.map(s => s.v || 0));

function colour(t) {
  const x = Math.min(1, Math.max(0, t)) * (RAMP.length - 1), i = Math.floor(x), f = x - i;
  if (i >= RAMP.length - 1) return RAMP[RAMP.length - 1];
  const a = RAMP[i], b = RAMP[i + 1];
  const c = [1, 3, 5].map(j => Math.round(parseInt(a.slice(j, j + 2), 16) * (1 - f) + parseInt(b.slice(j, j + 2), 16) * f));
  return `rgb(${c[0]},${c[1]},${c[2]})`;
}
function hexPath(cx, cy) {
  const r = 0.98, pts = [];
  for (let k = 0; k < 6; k++) { const a = Math.PI / 180 * (60 * k - 30); pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
  return "M" + pts.map(p => p[0].toFixed(3) + "," + p[1].toFixed(3)).join("L") + "Z";
}
const money = v => "£" + v.toFixed(1) + "m";
const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const svgEl = (tag, attrs, parent) => { const n = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); parent.appendChild(n); return n; };

const tip = document.getElementById("tip");
function showTip(ev, s) {
  tip.innerHTML = `<div class="t">${esc(s.name)}</div><div class="m">${esc(s.region)}</div>` +
    (s.v === null ? '<div>Not reported: fewer than 10 survey households above £2m</div>' : `<div>Estimated revenue: <b>${money(s.v)}</b> a year</div><div class="m">includes keyed noise</div>`);
  tip.style.display = "block";
  const x = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8), y = Math.min(ev.clientY + 14, window.innerHeight - tip.offsetHeight - 8);
  tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px";
}

// Two maps of the same figures: the hex cartogram, where every constituency
// is the same size, and the constituencies' own boundaries.
const views = {
  hex: { svg: document.getElementById("hexmap"), width: DATA.width, height: DATA.height, hatch: "url(#hatch)", maxZoom: 12 },
  geo: { svg: document.getElementById("geomap"), width: DATA.geo.width, height: DATA.geo.height, hatch: "url(#hatch-geo)", maxZoom: 30 },
};
function apply(view) { view.g.setAttribute("transform", `translate(${view.state.tx},${view.state.ty}) scale(${view.state.k})`); }
function zoomAt(view, x, y, k) {
  const st = view.state;
  k = Math.min(view.maxZoom, Math.max(1, k));
  st.tx = x - (x - st.tx) * (k / st.k); st.ty = y - (y - st.ty) * (k / st.k); st.k = k;
  if (k === 1) { st.tx = 0; st.ty = 0; }
  apply(view);
}
function attachZoom(view) {
  const svg = view.svg;
  const toUser = ev => { const p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); };
  // A plain scroll scrolls the page; Ctrl/⌘ + scroll (or a trackpad pinch) zooms the map.
  svg.addEventListener("wheel", ev => { if (!ev.ctrlKey && !ev.metaKey) return; ev.preventDefault(); const p = toUser(ev); zoomAt(view, p.x, p.y, view.state.k * (ev.deltaY < 0 ? 1.2 : 1 / 1.2)); }, { passive: false });
  let drag = null;
  svg.addEventListener("pointerdown", ev => { drag = { p: toUser(ev), tx: view.state.tx, ty: view.state.ty }; svg.classList.add("dragging"); });
  svg.addEventListener("pointermove", ev => { if (!drag || !(ev.buttons & 1)) return; const p = toUser(ev); view.state.tx = drag.tx + (p.x - drag.p.x); view.state.ty = drag.ty + (p.y - drag.p.y); apply(view); });
  const end = () => { drag = null; svg.classList.remove("dragging"); };
  svg.addEventListener("pointerup", end); svg.addEventListener("pointercancel", end);
}
for (const [name, view] of Object.entries(views)) {
  view.svg.setAttribute("viewBox", `0 0 ${view.width} ${view.height}`);
  view.g = svgEl("g", {}, view.svg);
  view.state = { k: 1, tx: 0, ty: 0 };
  for (const s of DATA.seats) {
    const d = name === "hex" ? hexPath(s.cx, s.cy) : DATA.geo.paths[s.code];
    const shape = svgEl("path", { class: name, d }, view.g);
    shape.style.fill = s.v === null ? view.hatch : colour(Math.sqrt(s.v / max));
    shape.addEventListener("pointermove", ev => showTip(ev, s));
    shape.addEventListener("pointerleave", () => { tip.style.display = "none"; });
    shape.addEventListener("click", ev => showTip(ev, s));  // a tap on a touch screen
  }
  attachZoom(view);
}

// The table lists every constituency; reported ones are ranked by revenue.
const rows = DATA.seats.map(s => ({ ...s }));
rows.filter(s => s.v !== null).sort((a, b) => b.v - a.v).forEach((s, i) => { s.rank = i + 1; });
let sort = { key: "v", dir: -1 };
function renderTable() {
  const q = document.getElementById("q").value.trim().toLowerCase();
  const list = rows.filter(s => !q || s.name.toLowerCase().includes(q) || s.region.toLowerCase().includes(q));
  list.sort((a, b) => {
    if (sort.key === "v") {
      if (a.v === null || b.v === null) return (a.v === null) - (b.v === null) || a.name.localeCompare(b.name);
      return sort.dir * (a.v - b.v || b.rank - a.rank);
    }
    return sort.dir * a[sort.key].localeCompare(b[sort.key]) || (a.v === null) - (b.v === null) || (b.v || 0) - (a.v || 0);
  });
  document.getElementById("rows").innerHTML = list.map(s =>
    `<tr><td class="num rank">${s.rank || ""}</td><td>${esc(s.name)}<span class="in-name">${esc(s.region)}</span></td><td class="col-region">${esc(s.region)}</td>` +
    (s.v === null ? '<td class="num na">Not reported</td>' : `<td class="num">${money(s.v)}</td>`) + "</tr>").join("");
  const shown = list.filter(s => s.v !== null).length;
  document.getElementById("count").textContent = `${list.length} of ${rows.length} constituencies; ${shown} reported`;
  for (const th of document.querySelectorAll("thead th[aria-sort]")) {
    const key = th.querySelector("button").dataset.key;
    th.setAttribute("aria-sort", key === sort.key ? (sort.dir > 0 ? "ascending" : "descending") : "none");
  }
}
for (const button of document.querySelectorAll("thead th button")) {
  button.addEventListener("click", () => {
    const key = button.dataset.key;
    sort = { key, dir: sort.key === key ? -sort.dir : (key === "v" ? -1 : 1) };
    renderTable();
  });
}
document.getElementById("q").addEventListener("input", renderTable);
renderTable();

document.addEventListener("pointerdown", ev => { if (!ev.target.closest || !ev.target.closest("svg.mapview")) tip.style.display = "none"; });

let active = views.hex;
const TABS = ["hex", "geo", "table"];
function show(name) {
  const table = name === "table";
  document.getElementById("p-map").hidden = table;
  document.getElementById("p-table").hidden = !table;
  document.getElementById("zoom").hidden = table;
  if (!table) {
    for (const [n, v] of Object.entries(views)) v.svg.style.display = n === name ? "" : "none";
    active = views[name];
  }
  for (const t of TABS) document.getElementById("t-" + t).setAttribute("aria-selected", String(t === name));
  tip.style.display = "none";
}
for (const t of TABS) document.getElementById("t-" + t).onclick = () => show(t);
document.getElementById("zin").onclick = () => zoomAt(active, active.width / 2, active.height / 2, active.state.k * 1.5);
document.getElementById("zout").onclick = () => zoomAt(active, active.width / 2, active.height / 2, active.state.k / 1.5);
document.getElementById("zreset").onclick = () => { active.state = { k: 1, tx: 0, ty: 0 }; apply(active); };
document.getElementById("ramp").style.background = "linear-gradient(90deg," + Array.from({ length: 11 }, (_, i) => colour(i / 10)).join(",") + ")";
document.getElementById("tmid").textContent = money(max / 4);
document.getElementById("tmax").textContent = money(max);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

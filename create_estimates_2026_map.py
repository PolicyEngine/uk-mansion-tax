"""Build constituency_estimates_2026.html, the 2026 constituency map of the surcharge.

    python create_estimates_2026_map.py

Reads estimates_2026/constituency_estimates_2026.csv and
estimates_2026/estimates_2026_summary.json (exported from PolicyEngine's
disclosure-controlled analysis of Microcosm UK data),
estimates_2026/constituencies_2024_hex.csv (the ODI hex layout of the 2024
constituencies) and estimates_2026/constituencies_2024_england_paths.json
(their simplified boundaries, from prepare_boundaries_2026.py). Needs only
the Python standard library.
"""

import csv
import html
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "estimates_2026"
OUT = HERE / "constituency_estimates_2026.html"


def hex_centres(rows):
    """Pointy-top hexes; odd rows are shifted right by half a hex; y grows northward."""
    cx = [(int(r["x"]) + (abs(int(r["y"])) % 2) * 0.5) * math.sqrt(3) for r in rows]
    cy = [-int(r["y"]) * 1.5 for r in rows]
    return [x - min(cx) + 1 for x in cx], [y - min(cy) + 1 for y in cy]


def pct(x):
    return f"{100 * x:.0f}%"


def main():
    with open(DATA / "constituencies_2024_hex.csv", newline="") as f:
        hexes = list(csv.DictReader(f))
    with open(DATA / "constituency_estimates_2026.csv", newline="") as f:
        estimates = {r["code"]: r for r in csv.DictReader(f)}
    summary = json.loads((DATA / "estimates_2026_summary.json").read_text())

    cx, cy = hex_centres(hexes)
    seats = []
    for r, x, y in zip(hexes, cx, cy):
        e = estimates[r["code"]]
        seats.append({"code": r["code"], "name": r["name"], "region": r["region"], "cx": round(x, 3), "cy": round(y, 3),
                      "v": float(e["revenue_m"]) if e["revenue_m"] else None})
    shown = sorted((s for s in seats if s["v"] is not None), key=lambda s: -s["v"])
    release = summary["release"]
    top_rows = "".join(
        f"<tr><td>{i}</td><td>{html.escape(s['name'])}</td><td>{html.escape(s['region'])}</td><td class=\"num\">£{s['v']:.1f}m</td></tr>"
        for i, s in enumerate(shown[:15], start=1)
    )
    low, high = summary["england_revenue_90pct_interval_m"]
    text = {
        "SEATS_SHOWN": str(summary["seats_shown"]),
        "SEATS_HIDDEN": str(summary["seats"] - summary["seats_shown"]),
        "SEATS": str(summary["seats"]),
        "COVER_PRIVATE": pct(summary["share_of_private_sector_2m_homes_in_shown_seats"]),
        "COVER_OWNER": pct(summary["share_of_owner_occupied_2m_homes_in_shown_seats"]),
        "COVER_BAND_H": pct(summary["share_of_band_h_homes_in_shown_seats"]),
        "TOP_20": str(summary["top_20_and_50_seats_by_2m_homes_shown"][0]),
        "TOP_50": str(summary["top_20_and_50_seats_by_2m_homes_shown"][1]),
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
        "TOP_ROWS": top_rows,
    }
    page = TEMPLATE
    for key, value in text.items():
        page = page.replace("{{" + key + "}}", value)
    boundaries = json.loads((DATA / "constituencies_2024_england_paths.json").read_text())
    assert set(boundaries["paths"]) == {s["code"] for s in seats}, "every constituency needs a boundary"
    payload = {"seats": seats, "width": round(max(cx) + 1, 3), "height": round(max(cy) + 1, 3),
               "geo": {k: boundaries[k] for k in ("width", "height", "paths")}}
    page = page.replace("/*DATA*/null", json.dumps(payload, separators=(",", ":")))
    assert "{{" not in page, "unfilled placeholder"
    OUT.write_text(page)
    print(f"wrote {OUT}")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mansion tax by constituency: 2026 estimates</title>
<style>
  :root { color-scheme: light; --bg:#ffffff; --fg:#1f2937; --muted:#5f6b7a; --line:#e5e7eb; --card:#fbfbfc; --zero:#eceef1; --accent:#2c6e8f; }
  * { box-sizing: border-box; }
  body { margin:0; padding:16px 20px 28px; background:var(--bg); color:var(--fg); font:15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  main { max-width:1080px; margin:0 auto; }
  h1 { font-size:22px; margin:0 0 6px; }
  h2 { font-size:17px; margin:24px 0 8px; }
  .sub { color:var(--muted); margin:0 0 6px; }
  .label { color:#8a4b14; font-weight:600; font-size:14px; margin:0 0 14px; }
  .callout { background:#eef6f9; border:1px solid #c6e0ea; border-radius:8px; padding:10px 14px; margin:0 0 14px; }
  .facts { display:grid; grid-template-columns:repeat(auto-fit, minmax(210px, 1fr)); gap:10px; margin:0 0 14px; }
  .fact { border:1px solid var(--line); border-radius:8px; padding:10px 12px; background:var(--card); }
  .fact b { display:block; font-size:20px; }
  .fact span { color:var(--muted); font-size:13px; }
  .layout { display:grid; grid-template-columns:minmax(0, 3fr) minmax(0, 2fr); gap:18px; align-items:start; }
  @media (max-width: 860px) { .layout { grid-template-columns:1fr; } }
  .map { border:1px solid var(--line); border-radius:8px; padding:10px; background:var(--card); }
  .controls { display:flex; gap:6px; justify-content:flex-end; margin:0 0 6px; }
  button { font:inherit; font-size:14px; padding:3px 10px; border:1px solid var(--line); border-radius:6px; background:var(--bg); color:var(--fg); cursor:pointer; }
  svg.mapview { width:100%; height:auto; display:block; cursor:grab; touch-action:pan-y; }
  svg.mapview.dragging { cursor:grabbing; }
  .hex { stroke:var(--bg); stroke-width:0.12; }
  .hex:hover { stroke:var(--fg); stroke-width:0.25; }
  .geo { stroke:#ffffff; stroke-width:0.5; vector-effect:non-scaling-stroke; }
  .geo:hover { stroke:var(--fg); stroke-width:1.5; }
  .controls { justify-content:space-between; flex-wrap:wrap; }
  .controls span { display:inline-flex; gap:6px; }
  button[aria-pressed="true"] { background:#e6f1f6; border-color:#9cc3d6; font-weight:600; }
  .legend { margin-top:8px; font-size:13px; color:var(--muted); }
  .ramp { height:10px; border-radius:3px; margin:3px 0; }
  .ticks { display:flex; justify-content:space-between; }
  .key { display:flex; flex-wrap:wrap; gap:14px; margin-top:8px; align-items:center; }
  table { width:100%; border-collapse:collapse; font-size:14px; }
  th, td { text-align:left; padding:5px 6px; border-bottom:1px solid var(--line); }
  td.num, th.num { text-align:right; white-space:nowrap; }
  details { border:1px solid var(--line); border-radius:8px; background:var(--card); margin-top:18px; }
  summary { cursor:pointer; padding:10px 14px; font-weight:600; }
  details .body { padding:0 14px 8px; }
  details p { margin:0 0 10px; font-size:14px; }
  code { font-size:12.5px; word-break:break-all; }
  #tip { position:fixed; pointer-events:none; background:var(--bg); color:var(--fg); border:1px solid var(--line); border-radius:6px; padding:8px 10px; font-size:13px; box-shadow:0 4px 14px rgba(0,0,0,.15); display:none; max-width:280px; z-index:10; }
  #tip .t { font-weight:600; }
  #tip .m { color:var(--muted); }
  a { color:var(--accent); }
</style>
</head>
<body>
<main>
<h1>Mansion tax by constituency: 2026 estimates</h1>
<p class="sub">Estimated static revenue from the High Value Council Tax Surcharge in 2028-29, by Westminster constituency in England: owner-occupied main residences worth over £2m at April 2026 values, modelled from PolicyEngine's Microcosm data.</p>
<p class="label">Experimental modelled estimates from survey microdata, with wide uncertainty; not official statistics.</p>
<div class="callout">The map shows the {{SEATS_SHOWN}} constituencies with enough survey data to report. Together they hold about 90% of England's homes worth over £2m: {{COVER_PRIVATE}} of all privately owned ones and {{COVER_OWNER}} of owner-occupied ones, by Land Registry-based counts. The other {{SEATS_HIDDEN}} constituencies, hatched grey, have too few survey households above £2m to report; most have few such homes.</div>
<div class="facts">
  <div class="fact"><b>{{REVENUE}} a year</b><span>England, static, owner-occupied main residences (90% range {{INTERVAL}})</span></div>
  <div class="fact"><b>about {{HOMES}},000 homes</b><span>owner-occupied homes worth over £2m</span></div>
  <div class="fact"><b>£605m static, £400m after behaviour</b><span>OBR costing, all liable properties</span></div>
</div>
<div class="layout">
  <div class="map">
    <div class="controls"><span><button id="vhex" aria-pressed="true">Hex map</button><button id="vgeo" aria-pressed="false">Geographic</button></span><span><button id="zin" aria-label="Zoom in">+</button><button id="zout" aria-label="Zoom out">−</button><button id="zreset">Reset</button></span></div>
    <svg class="mapview" id="hexmap" role="img" aria-label="Hex map of constituencies in England coloured by estimated surcharge revenue; constituencies not reported are hatched grey"></svg>
    <svg class="mapview" id="geomap" role="img" style="display:none" aria-label="Map of constituencies in England, with their boundaries, coloured by estimated surcharge revenue; constituencies not reported are hatched grey"></svg>
    <div class="legend">
      <div>Estimated revenue a year, square-root scale</div>
      <div class="ramp" id="ramp"></div>
      <div class="ticks"><span>£0</span><span id="tmid"></span><span id="tmax"></span></div>
      <div class="key"><span><svg width="14" height="14" style="vertical-align:-3px;margin-right:5px"><rect width="14" height="14" fill="url(#hatch-key)"></rect></svg>not reported: fewer than 10 survey households above £2m</span><span>Scroll or use + and − to zoom; drag to pan.</span></div>
    </div>
  </div>
  <div>
    <h2 style="margin-top:0">Largest estimated revenue</h2>
    <table>
      <thead><tr><th>#</th><th>Constituency</th><th>Region</th><th class="num">A year</th></tr></thead>
      <tbody>{{TOP_ROWS}}</tbody>
    </table>
    <p style="font-size:13px;color:var(--muted)">All {{SEATS}} constituencies are in <a href="estimates_2026/constituency_estimates_2026.csv">constituency_estimates_2026.csv</a>.</p>
  </div>
</div>
<details>
<summary>How these estimates are made, and their limits</summary>
<div class="body">
<p><b>Modelled, not observed.</b> These are estimates from survey-based microdata, not counts of real homes or bills. Seat estimates are uncertain: for a typical constituency shown, the standard error is about {{CV}} of the estimate, and the ranking of the largest seats is steadier (a resample keeps {{TOP20_KEPT}} of the top 20). These measures, like the 90% range for England ({{INTERVAL}}), come from resampling the survey households only; they leave out calibration and modelling error, so the true uncertainty is larger. They follow the pattern of council tax band H homes closely (rank correlation {{RHO}}), and the {{SEATS_SHOWN}} seats shown include all of the {{TOP_20}} constituencies with the most homes over £2m.</p>
<p><b>Data.</b> Microcosm UK 2024-25 local-area release (cut <code>{{CUT}}</code>, {{HOUSEHOLDS}} households, SHA-256 <code>{{SHA}}…</code>), PolicyEngine's synthetic microdata built from the Family Resources Survey and other UK Data Service surveys and calibrated to official local statistics. Each owner's home takes its value from its constituency's Land Registry sale prices at the household's rank among owners in its region, and the release is calibrated to Land Registry counts of owner-occupied homes over £1m, £1.5m and £2m by region and local authority. policyengine {{PE}} loads this release for constituency results, with policyengine-uk {{PE_UK}}. Its certificate covers the national release built from the same data, not constituency results from this local-area release, so these seat figures are not certified. Revenue applies the surcharge as policyengine-uk {{PE_UK}} defines it to each household's modelled home value. The microdata are licensed and not public.</p>
<p><b>Policy.</b> England only, from April 2028, owners liable: £2,500 a year for homes worth £2m–£2.5m, £3,500 for £2.5m–£3.5m, £5,000 for £3.5m–£5m and £7,500 above £5m, at April 2026 values. policyengine-uk uprates 2024 values to 2026 by GDP per capita (+7.4%); house prices (+5.3%) would put fewer homes over each threshold. CPI uprating of the charges from 2029-30 is not modelled. Revenue is static: no behaviour, appeals, non-payment or deferral.</p>
<p><b>Coverage.</b> Only owner-occupied main residences are modelled, so second homes and let or company-owned homes are missing. Their share is uncertain: the OBR puts non-owner-occupied homes at about 40% of liable properties (from stamp duty data), while MHCLG's Market Value Survey, cited in the May 2026 consultation, found over 90% of homes worth £2m or more owner occupied in 2024.</p>
<p><b>Privacy.</b> The survey data are licensed from the UK Data Service. To protect respondents, a constituency is reported only if at least 10 survey households above £2m sit behind its estimate, and every estimate from the survey microdata carries keyed noise: each survey household's weight is multiplied by a fixed secret factor between 8% and 12% away from 1. That typically moves a constituency's estimate by a few per cent, more where one household carries much of it.</p>
<p><b>Maps.</b> The hex map gives every constituency the same size, so small urban seats stay visible; the geographic map shows the 2024 constituency boundaries (contains OS data © Crown copyright and database right 2024), simplified to about 250 m.</p>
<p><b>Earlier map.</b> The <a href="surcharge_map_by_revenue.html">November 2025 map</a> allocated the OBR's estimate by 2024 Land Registry sales; it is kept unchanged for the article that embeds it.</p>
</div>
</details>
</main>
<div id="tip"></div>
<svg width="0" height="0" style="position:absolute">
  <defs><pattern id="hatch" width="0.45" height="0.45" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="0.45" height="0.45" style="fill:var(--zero)"></rect><line x1="0" y1="0" x2="0" y2="0.45" stroke="#b3bac3" stroke-width="0.1"></line>
  </pattern>
  <pattern id="hatch-geo" width="16" height="16" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="16" height="16" style="fill:var(--zero)"></rect><line x1="0" y1="0" x2="0" y2="16" stroke="#b3bac3" stroke-width="4"></line>
  </pattern>
  <pattern id="hatch-key" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
    <rect width="5" height="5" style="fill:var(--zero)"></rect><line x1="0" y1="0" x2="0" y2="5" stroke="#9aa3ad" stroke-width="1.4"></line>
  </pattern></defs>
</svg>
<script>
const DATA = /*DATA*/null;
const RAMP = ["#d6ecf3", "#a6d3e3", "#6fb3cd", "#3f8fb2", "#2c6e8f", "#1d4a63"];
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
const svgEl = (tag, attrs, parent) => { const n = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v); parent.appendChild(n); return n; };

const tip = document.getElementById("tip");
function showTip(ev, s) {
  tip.innerHTML = `<div class="t">${s.name}</div><div class="m">${s.region}</div>` +
    (s.v === null ? '<div>Not reported: fewer than 10 survey households above £2m</div>' : `<div>Estimated revenue: <b>${money(s.v)}</b> a year</div><div class="m">includes keyed noise</div>`);
  tip.style.display = "block";
  const x = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8), y = Math.min(ev.clientY + 14, window.innerHeight - tip.offsetHeight - 8);
  tip.style.left = Math.max(8, x) + "px"; tip.style.top = Math.max(8, y) + "px";
}

// Two views of the same figures: the hex cartogram, where every constituency
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
  svg.addEventListener("wheel", ev => { ev.preventDefault(); const p = toUser(ev); zoomAt(view, p.x, p.y, view.state.k * (ev.deltaY < 0 ? 1.2 : 1 / 1.2)); }, { passive: false });
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
  }
  attachZoom(view);
}
let active = views.hex;
function show(name) {
  for (const [n, v] of Object.entries(views)) v.svg.style.display = n === name ? "" : "none";
  active = views[name];
  document.getElementById("vhex").setAttribute("aria-pressed", String(name === "hex"));
  document.getElementById("vgeo").setAttribute("aria-pressed", String(name === "geo"));
  tip.style.display = "none";
}
document.getElementById("vhex").onclick = () => show("hex");
document.getElementById("vgeo").onclick = () => show("geo");
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

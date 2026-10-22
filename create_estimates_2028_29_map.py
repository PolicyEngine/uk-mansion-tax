"""Build constituency_estimates_2028_29.html, an embeddable map and table of the surcharge in 2028-29.

    python create_estimates_2028_29_map.py

The page is meant for an iframe in a PolicyEngine blog post, like
surcharge_map_by_revenue.html in the November 2025 post: it fills the
iframe's height and never needs the iframe to scroll. Reads
estimates_2028_29/constituency_estimates_2028_29.csv and
estimates_2028_29/estimates_2028_29_summary.json (exported from PolicyEngine's
disclosure-controlled analysis of Microcosm UK data),
estimates_2028_29/constituencies_2024_hex.csv (the ODI hex layout of the 2024
constituencies) and estimates_2028_29/constituencies_2024_england_paths.json
(their simplified boundaries, from prepare_estimates_2028_29_boundaries.py).
Needs only the Python standard library.
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
    assert sum(s["v"] is not None for s in seats) == summary["seats_shown"]
    text = {
        "SEATS_HIDDEN": str(summary["seats"] - summary["seats_shown"]),
        "SEATS": str(summary["seats"]),
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


# Colours, type and radii follow PolicyEngine's design tokens (@policyengine/ui-kit):
# teal brand scale, Inter, gray-200 borders.
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>High value council tax surcharge by constituency, 2028-29</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    color-scheme: light;
    --background:#ffffff; --foreground:#101828; --muted:#475569; --subtle:#64748b;
    --border:#e2e8f0; --border-medium:#cbd5e1; --muted-bg:#f2f4f7; --tint:#f8fafc;
    --primary:#2c7a7b; --primary-dark:#285e61; --ring:#319795; --zero:#f2f4f7; --zero-line:#cbd5e1;
  }
  * { box-sizing:border-box; }
  [hidden] { display:none !important; }
  html, body { margin:0; background:var(--background); }
  body { color:var(--foreground); font:14px/1.5 Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; -webkit-font-smoothing:antialiased; }
  a { color:var(--primary); text-decoration:none; }
  a:hover { color:var(--primary-dark); text-decoration:underline; }
  /* The page fills the iframe's height: the map or the table takes whatever the
     title, toolbar, legend and source line leave. */
  .wrap { height:100vh; min-height:480px; max-width:900px; margin:0 auto; padding:16px; display:flex; flex-direction:column; gap:10px; }
  header { padding-bottom:10px; border-bottom:1px solid var(--border); }
  h1 { font-size:16px; line-height:24px; font-weight:600; margin:0 0 2px; }
  header p { margin:0; font-size:13px; line-height:18px; color:var(--muted); }
  .toolbar { display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap; }
  .tabs { display:inline-flex; gap:2px; padding:4px; background:var(--muted-bg); border-radius:8px; }
  .tabs button { border:0; background:transparent; color:var(--muted); font:inherit; font-size:14px; font-weight:500; line-height:20px; padding:5px 12px; border-radius:6px; cursor:pointer; }
  .tabs button:hover { color:var(--foreground); }
  .tabs button[aria-selected="true"] { background:var(--background); color:var(--foreground); box-shadow:0 1px 2px rgba(16,24,40,.1); }
  .zoom { display:inline-flex; gap:6px; }
  .zoom button { border:1px solid var(--border); background:var(--background); color:var(--foreground); font:inherit; font-size:14px; line-height:20px; padding:4px 10px; border-radius:6px; cursor:pointer; }
  .zoom button:hover { background:var(--tint); }
  button:focus-visible, input:focus-visible, th button:focus-visible { outline:2px solid var(--ring); outline-offset:2px; }
  .views { flex:1 1 auto; min-height:220px; position:relative; }
  #p-map, #p-table { position:absolute; inset:0; }
  svg.mapview { width:100%; height:100%; display:block; cursor:grab; touch-action:pan-y; }
  svg.mapview.dragging { cursor:grabbing; }
  .hex { stroke:var(--background); stroke-width:0.12; }
  .hex:hover { stroke:var(--foreground); stroke-width:0.25; }
  .geo { stroke:var(--background); stroke-width:0.5; vector-effect:non-scaling-stroke; }
  .geo:hover { stroke:var(--foreground); stroke-width:1.5; }
  .legend { display:flex; flex-wrap:wrap; align-items:center; gap:8px 24px; font-size:12px; line-height:16px; color:var(--muted); }
  .scale { width:260px; max-width:100%; }
  .scale b { font-weight:600; color:var(--foreground); }
  .ramp { height:8px; border-radius:2px; margin:3px 0; }
  .ticks { display:flex; justify-content:space-between; }
  .key { display:flex; gap:6px; align-items:center; max-width:280px; }
  .key svg { flex:none; }
  .hint { flex:1 1 200px; }
  #p-table { display:flex; flex-direction:column; gap:8px; }
  .table-tools { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
  .table-tools input { flex:1 1 220px; max-width:340px; font:inherit; font-size:14px; padding:6px 10px; border:1px solid var(--border-medium); border-radius:6px; color:var(--foreground); }
  .table-tools span { font-size:12px; color:var(--muted); }
  .table-wrap { flex:1 1 auto; min-height:0; overflow:auto; border:1px solid var(--border); border-radius:8px; }
  table { width:100%; border-collapse:collapse; font-size:13px; line-height:18px; }
  th, td { text-align:left; padding:7px 10px; border-bottom:1px solid var(--border); }
  thead th { position:sticky; top:0; background:var(--tint); z-index:1; font-weight:600; color:var(--foreground); }
  th button { all:unset; cursor:pointer; }
  th button::after { content:""; margin-left:4px; color:var(--subtle); }
  th[aria-sort="ascending"] button::after { content:"▲"; font-size:9px; }
  th[aria-sort="descending"] button::after { content:"▼"; font-size:9px; }
  td.num, th.num { text-align:right; white-space:nowrap; font-variant-numeric:tabular-nums; }
  td.rank { color:var(--subtle); width:3em; }
  td.na { color:var(--subtle); }
  tbody tr:hover { background:var(--tint); }
  .in-name, .short { display:none; }
  td .in-name { font-size:11px; line-height:14px; color:var(--subtle); }
  @media (max-width: 600px) { .col-region, .long { display:none; } .in-name { display:block; } .short { display:inline; } th, td { padding:7px 8px; } }
  .source { font-size:12px; line-height:16px; color:var(--muted); }
  #tip { position:fixed; pointer-events:none; background:var(--background); color:var(--foreground); border:1px solid var(--border); border-radius:8px; padding:8px 12px; font-size:13px; line-height:18px; box-shadow:0 4px 16px rgba(16,24,40,.12); display:none; max-width:260px; z-index:10; }
  #tip .t { font-weight:600; }
  #tip .m { color:var(--muted); }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>High value council tax surcharge by constituency, 2028-29</h1>
    <p>Estimated static revenue a year from owner-occupied homes worth over £2m. Experimental modelled estimates from survey microdata, with wide uncertainty; not official statistics.</p>
  </header>
  <div class="toolbar">
    <div class="tabs" role="tablist" aria-label="View">
      <button role="tab" id="t-hex" aria-selected="true">Hex map</button>
      <button role="tab" id="t-geo" aria-selected="false">Geographic</button>
      <button role="tab" id="t-table" aria-selected="false">Table</button>
    </div>
    <div class="zoom" id="zoom"><button id="zin" aria-label="Zoom in">+</button><button id="zout" aria-label="Zoom out">−</button><button id="zreset">Reset</button></div>
  </div>
  <div class="views">
    <div id="p-map" role="tabpanel">
      <svg class="mapview" id="hexmap" role="img" aria-label="Hex map of constituencies in England coloured by estimated surcharge revenue in 2028-29; constituencies not reported are hatched grey"></svg>
      <svg class="mapview" id="geomap" role="img" style="display:none" aria-label="Map of constituencies in England, with their boundaries, coloured by estimated surcharge revenue in 2028-29; constituencies not reported are hatched grey"></svg>
    </div>
    <div id="p-table" role="tabpanel" hidden>
      <div class="table-tools"><input type="search" id="q" placeholder="Search by constituency or region" aria-label="Search by constituency or region"><span id="count"></span></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th class="num">#</th><th aria-sort="none"><button data-key="name">Constituency</button></th><th class="col-region" aria-sort="none"><button data-key="region">Region</button></th><th class="num" aria-sort="descending"><button data-key="v"><span class="long">Estimated revenue a year</span><span class="short">A year</span></button></th></tr></thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="legend" id="legend">
    <div class="scale"><b>Estimated revenue a year</b> (square-root scale)<div class="ramp" id="ramp"></div><div class="ticks"><span>£0</span><span id="tmid"></span><span id="tmax"></span></div></div>
    <div class="key"><svg width="16" height="16" aria-hidden="true"><rect width="16" height="16" rx="2" fill="url(#hatch-key)"></rect></svg><span>Not reported ({{SEATS_HIDDEN}} of {{SEATS}}): fewer than 10 survey households above £2m</span></div>
    <div class="hint"><span class="long">Zoom with + and −, or hold Ctrl or ⌘ and scroll; drag to pan. Hover over or tap a constituency for its estimate.</span><span class="short">Tap a constituency for its estimate; zoom with + and −.</span></div>
  </div>
  <div class="source">Experimental modelled estimates from survey microdata, with wide uncertainty; not official statistics. Source: PolicyEngine analysis of Microcosm UK survey microdata (19 October 2026 release). Every estimate carries keyed noise to protect survey respondents. <a href="estimates_2028_29/constituency_estimates_2028_29.csv" target="_blank" rel="noopener">Download all {{SEATS}} constituencies (CSV)</a>.</div>
</div>
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
  document.getElementById("legend").hidden = table;
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

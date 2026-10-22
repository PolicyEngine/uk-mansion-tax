"""Write estimates_2028_29/constituencies_2024_england_paths.json for the geographic view.

    python prepare_estimates_2028_29_boundaries.py

Takes the 2024 Westminster constituency boundaries that the November 2025 map
embeds (surcharge_map_by_revenue.html, British National Grid), keeps the 543
English constituencies, simplifies them and writes one SVG path per
constituency code. Needs only the Python standard library.
"""

import csv
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "estimates_2028_29" / "constituencies_2024_england_paths.json"
METRES_PER_UNIT = 250  # one SVG unit; outlines are simplified to about one unit


def norm(name):
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("&", "and"))


def simplify(points, tolerance):
    """Douglas-Peucker on a list of (x, y)."""
    if len(points) < 3:
        return points
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        (x1, y1), (x2, y2) = points[first], points[last]
        dx, dy = x2 - x1, y2 - y1
        norm2 = dx * dx + dy * dy
        best, index = -1.0, None
        for i in range(first + 1, last):
            px, py = points[i]
            if norm2 == 0:
                d = (px - x1) ** 2 + (py - y1) ** 2
            else:
                t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / norm2))
                d = (px - x1 - t * dx) ** 2 + (py - y1 - t * dy) ** 2
            if d > best:
                best, index = d, i
        if index is not None and best > tolerance * tolerance:
            keep[index] = True
            stack += [(first, index), (index, last)]
    return [p for p, k in zip(points, keep) if k]


def main():
    page = (HERE / "surcharge_map_by_revenue.html").read_text()
    start = page.index("const geoData = ") + len("const geoData = ")
    geo, _ = json.JSONDecoder().raw_decode(page[start:])
    features = {norm(f["properties"]["Name"]): f for f in geo["features"]}
    with open(HERE / "estimates_2028_29" / "constituencies_2024_hex.csv", newline="") as f:
        seats = list(csv.DictReader(f))

    polygons = {}
    for seat in seats:
        geometry = features[norm(seat["name"])]["geometry"]
        parts = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        polygons[seat["code"]] = [ring for part in parts for ring in part]
    xs = [x for rings in polygons.values() for ring in rings for x, _ in ring]
    ys = [y for rings in polygons.values() for ring in rings for _, y in ring]
    x0, y1 = min(xs), max(ys)

    paths = {}
    for code, rings in polygons.items():
        out = []
        for ring in rings:
            projected = [((x - x0) / METRES_PER_UNIT, (y1 - y) / METRES_PER_UNIT) for x, y in ring]
            simple = simplify(projected, 1.0)
            if len(simple) < 4:
                continue  # a sliver or tiny island
            pts = [(round(x), round(y)) for x, y in simple]
            out.append("M" + "L".join(f"{x} {y}" for x, y in pts) + "Z")
        if not out:  # never drop a whole constituency
            ring = max(rings, key=len)
            out.append("M" + "L".join(f"{round((x - x0) / METRES_PER_UNIT)} {round((y1 - y) / METRES_PER_UNIT)}" for x, y in ring) + "Z")
        paths[code] = "".join(out)
    payload = {
        "source": "2024 Westminster constituency boundaries as embedded in surcharge_map_by_revenue.html (British National Grid)",
        "metres_per_unit": METRES_PER_UNIT,
        "width": round((max(xs) - x0) / METRES_PER_UNIT) + 1,
        "height": round((y1 - min(ys)) / METRES_PER_UNIT) + 1,
        "paths": paths,
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB, {len(paths)} constituencies)")


if __name__ == "__main__":
    main()

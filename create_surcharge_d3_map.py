#!/usr/bin/env python3
"""
Create D3 hexagonal map visualization of UK high value council tax surcharge impact.

Generates an interactive D3 map showing the estimated revenue share from
the new council tax surcharge on properties valued over £2m, based on the
November 2025 Budget announcement.

Style matches the previous mansion tax blog post map.
"""

import json
import pandas as pd
from pathlib import Path


def load_hex_coordinates():
    """Load constituency hex grid coordinates from HexJSON."""
    print("Loading hex grid coordinates...")
    with open('data/uk-constituencies-2024.hexjson') as f:
        hexjson = json.load(f)
    return hexjson


def load_geo_json():
    """Load constituency geographic boundaries."""
    print("Loading geographic boundaries...")
    with open('data/constituencies.geojson') as f:
        return json.load(f)


def load_impact_data():
    """Load surcharge impact data."""
    print("Loading surcharge impact data...")
    impact_file = 'constituency_surcharge_summary.csv'

    if not Path(impact_file).exists():
        print(f"ERROR: {impact_file} not found")
        print("Run: python analyze_autumn_budget.py")
        return None

    df = pd.read_csv(impact_file)
    print(f"Loaded data for {len(df)} constituencies")
    return df


def generate_d3_map_html(hexjson, geojson, impact_data):
    """Generate D3 HTML map with both geographic and hex views."""

    # Prepare impact data as JavaScript object
    impact_js = {}
    for _, row in impact_data.iterrows():
        impact_js[row['constituency']] = {
            'pct': row['share_pct'],
            'num': int(row['properties']),
            'rev': int(row['allocated_from_obr'])
        }

    # Get all constituency names for search
    all_constituencies = sorted(impact_data['constituency'].tolist())

    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>High Value Council Tax Surcharge by Constituency</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Roboto', sans-serif;
            background: white;
        }
        .map-wrapper {
            display: flex;
            flex-direction: column;
            gap: 12px;
            padding: 16px;
            max-width: 900px;
            margin: 0 auto;
        }
        .map-header {
            padding-bottom: 12px;
            border-bottom: 1px solid #e5e7eb;
        }
        .map-header h2 {
            margin: 0 0 6px 0;
            color: #374151;
            font-size: 1rem;
            font-weight: 600;
        }
        .map-header p {
            margin: 0;
            color: #6b7280;
            font-size: 0.875rem;
        }
        .map-top-bar {
            display: flex;
            gap: 24px;
            align-items: center;
            flex-wrap: wrap;
        }
        .map-search-section {
            flex: 1;
            min-width: 200px;
            max-width: 300px;
        }
        .map-search-section h3 {
            font-size: 0.875rem;
            font-weight: 600;
            color: #374151;
            margin: 0 0 8px 0;
        }
        .search-container {
            position: relative;
        }
        .constituency-search {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 0.875rem;
            font-family: 'Roboto', sans-serif;
        }
        .constituency-search:focus {
            outline: none;
            border-color: #39C6C0;
            box-shadow: 0 0 0 3px rgba(49, 151, 149, 0.1);
        }
        .search-results {
            position: absolute;
            z-index: 100;
            width: 100%;
            margin-top: 4px;
            background: white;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-height: 200px;
            overflow-y: auto;
            display: none;
        }
        .search-result-item {
            width: 100%;
            text-align: left;
            padding: 10px 12px;
            background: none;
            border: none;
            border-bottom: 1px solid #f3f4f6;
            cursor: pointer;
            font-family: 'Roboto', sans-serif;
        }
        .search-result-item:last-child {
            border-bottom: none;
        }
        .search-result-item:hover {
            background: #f9fafb;
        }
        .result-name {
            font-weight: 500;
            font-size: 0.875rem;
            color: #374151;
        }
        .result-value {
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 2px;
        }
        .view-toggle {
            display: flex;
            gap: 4px;
            background: #f3f4f6;
            padding: 4px;
            border-radius: 8px;
        }
        .view-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            font-family: 'Roboto', sans-serif;
            background: transparent;
            color: #6b7280;
        }
        .view-btn:hover {
            color: #39C6C0;
        }
        .view-btn.active {
            background: white;
            color: #39C6C0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .map-legend {
            display: flex;
            flex-direction: column;
            gap: 4px;
            margin-left: auto;
        }
        .legend-gradient {
            width: 180px;
            height: 12px;
            border-radius: 3px;
            background: linear-gradient(to right, #F7FDFC, #39C6C0, #2C6496);
        }
        .legend-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: #6b7280;
            width: 180px;
        }
        .map-canvas {
            position: relative;
            width: 100%;
            display: flex;
            justify-content: center;
        }
        .map-canvas svg {
            background: #ffffff;
            border-radius: 6px;
            width: 100%;
            height: auto;
            max-width: 800px;
        }
        .constituency-path {
            cursor: pointer;
            transition: opacity 0.1s ease;
        }
        .constituency-path:hover {
            opacity: 0.8;
        }
        .hex {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .hex:hover {
            opacity: 0.8;
        }
        .map-controls {
            position: absolute;
            top: 12px;
            right: 12px;
            display: flex;
            gap: 4px;
            background: white;
            padding: 4px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        .zoom-btn {
            width: 28px;
            height: 28px;
            background: transparent;
            border: none;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #6b7280;
            font-size: 18px;
            font-weight: bold;
        }
        .zoom-btn:hover {
            background: #f3f4f6;
            color: #39C6C0;
        }
        .tooltip {
            position: absolute;
            background: white;
            border: 2px solid #39C6C0;
            border-radius: 8px;
            padding: 12px 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            pointer-events: none;
            min-width: 200px;
            transform: translate(-50%, -100%);
            margin-top: -10px;
            z-index: 100;
            display: none;
        }
        .tooltip h4 {
            font-size: 0.9rem;
            font-weight: 600;
            color: #374151;
            margin: 0 0 8px 0;
        }
        .tooltip-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: #39C6C0;
            margin: 4px 0;
        }
        .tooltip-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #6b7280;
            margin: 4px 0;
        }
        .source {
            font-size: 0.75rem;
            color: #9ca3af;
            margin-top: 12px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="map-wrapper">
        <div class="map-header">
            <h2>High value council tax surcharge by constituency</h2>
            <p>Share of £400m estimated revenue (OBR November 2025)</p>
        </div>

        <div class="map-top-bar">
            <div class="map-search-section">
                <h3>Search constituency</h3>
                <div class="search-container">
                    <input type="text" class="constituency-search" placeholder="Type to search..." id="search-input">
                    <div class="search-results" id="search-results"></div>
                </div>
            </div>

            <div class="view-toggle">
                <button class="view-btn active" id="btn-geo">Geographic</button>
                <button class="view-btn" id="btn-hex">Hex</button>
            </div>

            <div class="map-legend">
                <div class="legend-gradient"></div>
                <div class="legend-labels">
                    <span>0%</span>
                    <span id="max-pct-label">10%</span>
                </div>
            </div>
        </div>

        <div class="map-canvas">
            <svg id="map" viewBox="0 0 800 900" preserveAspectRatio="xMidYMid meet"></svg>
            <div class="map-controls">
                <button class="zoom-btn" id="zoom-in" title="Zoom in">+</button>
                <button class="zoom-btn" id="zoom-out" title="Zoom out">−</button>
                <button class="zoom-btn" id="zoom-reset" title="Reset">↺</button>
            </div>
            <div class="tooltip" id="tooltip"></div>
        </div>

        <div class="source">
            Source: PolicyEngine analysis of Land Registry data (uprated to 2028 using OBR forecasts)
        </div>
    </div>

    <script>
        const impactData = ''' + json.dumps(impact_js) + ''';

        const hexjson = ''' + json.dumps(hexjson) + ''';

        const geoData = ''' + json.dumps(geojson) + ''';

        const allConstituencies = ''' + json.dumps(all_constituencies) + ''';

        const width = 800;
        const height = 900;

        const svg = d3.select('#map');
        const g = svg.append('g');
        const tooltip = document.getElementById('tooltip');

        // Calculate bounds of British National Grid coordinates
        let xMin = Infinity, xMax = -Infinity, yMin = Infinity, yMax = -Infinity;
        geoData.features.forEach(feature => {
            const traverse = (coords) => {
                if (typeof coords[0] === 'number') {
                    xMin = Math.min(xMin, coords[0]);
                    xMax = Math.max(xMax, coords[0]);
                    yMin = Math.min(yMin, coords[1]);
                    yMax = Math.max(yMax, coords[1]);
                } else {
                    coords.forEach(traverse);
                }
            };
            traverse(feature.geometry.coordinates);
        });

        // Create scale to fit British National Grid into SVG
        const padding = 80;
        const dataWidth = xMax - xMin;
        const dataHeight = yMax - yMin;
        const geoScale = Math.min((width - 2 * padding) / dataWidth, (height - 2 * padding) / dataHeight);
        const geoOffsetX = (width - dataWidth * geoScale) / 2;
        const geoOffsetY = (height - dataHeight * geoScale) / 2;

        const projection = d3.geoTransform({
            point: function(x, y) {
                this.stream.point(
                    (x - xMin) * geoScale + geoOffsetX,
                    height - ((y - yMin) * geoScale + geoOffsetY)
                );
            }
        });

        const pathGenerator = d3.geoPath().projection(projection);

        // Zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([1, 8])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        svg.call(zoom);

        // Zoom buttons
        document.getElementById('zoom-in').addEventListener('click', () => {
            svg.transition().call(zoom.scaleBy, 1.5);
        });
        document.getElementById('zoom-out').addEventListener('click', () => {
            svg.transition().call(zoom.scaleBy, 0.67);
        });
        document.getElementById('zoom-reset').addEventListener('click', () => {
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        });

        // Color scale - PolicyEngine teal/blue palette
        const maxPct = Math.max(...Object.values(impactData).map(d => d.pct));
        document.getElementById('max-pct-label').textContent = maxPct.toFixed(1) + '%';

        const colorScale = d3.scaleSequential()
            .domain([0, maxPct])
            .interpolator(t => {
                // Interpolate from light teal -> teal -> blue
                if (t < 0.5) {
                    return d3.interpolate('#F7FDFC', '#39C6C0')(t * 2);
                } else {
                    return d3.interpolate('#39C6C0', '#2C6496')((t - 0.5) * 2);
                }
            });

        // Draw geographic view
        const geoPaths = g.selectAll('path')
            .data(geoData.features)
            .join('path')
            .attr('class', 'constituency-path')
            .attr('d', pathGenerator)
            .attr('fill', d => {
                const data = impactData[d.properties.Name];
                return data ? colorScale(data.pct) : '#F7FDFC';
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 0.3)
            .on('mousemove', function(event, d) {
                const name = d.properties.Name;
                const data = impactData[name] || { pct: 0, num: 0, rev: 0 };
                showTooltip(name, data, event);
                // Highlight
                g.selectAll('.constituency-path, .hex')
                    .attr('stroke', '#fff')
                    .attr('stroke-width', function() {
                        return this.classList.contains('hex') ? 1 : 0.3;
                    });
                d3.select(this).attr('stroke', '#39C6C0').attr('stroke-width', 2);
            })
            .on('mouseout', hideTooltip);

        function showTooltip(name, data, event) {
            tooltip.innerHTML = `
                <h4>${name}</h4>
                <div class="tooltip-value">${data.pct.toFixed(2)}%</div>
                <div class="tooltip-row">
                    <span>Projected sales</span>
                    <span>${data.num.toLocaleString()}</span>
                </div>
                <div class="tooltip-row">
                    <span>Est. revenue</span>
                    <span>£${(data.rev / 1000000).toFixed(1)}m</span>
                </div>
            `;
            tooltip.style.display = 'block';

            const rect = document.querySelector('.map-canvas').getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            tooltip.style.left = x + 'px';
            tooltip.style.top = y + 'px';
        }

        function hideTooltip() {
            tooltip.style.display = 'none';
            g.selectAll('.constituency-path')
                .attr('stroke', '#fff')
                .attr('stroke-width', 0.3);
            g.selectAll('.hex')
                .attr('stroke', '#fff')
                .attr('stroke-width', 1);
        }

        // Build hex data
        const hexData = [];
        for (const [gss, hex] of Object.entries(hexjson.hexes)) {
            hexData.push({
                gss: gss,
                name: hex.n,
                q: hex.q,
                r: hex.r
            });
        }

        // Calculate hex bounds
        let hexQMin = Infinity, hexQMax = -Infinity, hexRMin = Infinity, hexRMax = -Infinity;
        hexData.forEach(h => {
            hexQMin = Math.min(hexQMin, h.q);
            hexQMax = Math.max(hexQMax, h.q);
            hexRMin = Math.min(hexRMin, h.r);
            hexRMax = Math.max(hexRMax, h.r);
        });

        // Calculate hex positions - centered in SVG
        const hexSize = 18;
        const hexWidth = hexSize * 2;
        const hexHeight = Math.sqrt(3) * hexSize;
        const hexRangeQ = hexQMax - hexQMin;
        const hexRangeR = hexRMax - hexRMin;
        const hexTotalWidth = hexRangeQ * hexWidth * 0.75 + hexWidth;
        const hexTotalHeight = hexRangeR * hexHeight + hexHeight;
        const hexOffsetX = (width - hexTotalWidth) / 2;
        const hexOffsetY = (height - hexTotalHeight) / 2;

        function getHexPosition(q, r) {
            const x = hexOffsetX + (q - hexQMin) * hexWidth * 0.75 + hexWidth / 2;
            // Flip y-axis so south (London) is at the bottom
            const y = hexOffsetY + (hexRMax - r) * hexHeight + (q % 2 !== 0 ? hexHeight / 2 : 0) + hexHeight / 2;
            return { x, y };
        }

        function hexPoints(cx, cy) {
            const points = [];
            for (let i = 0; i < 6; i++) {
                const angle = Math.PI / 3 * i - Math.PI / 6;
                points.push([
                    cx + hexSize * Math.cos(angle),
                    cy + hexSize * Math.sin(angle)
                ]);
            }
            return points.map(p => p.join(',')).join(' ');
        }

        // Draw hexagons (initially hidden)
        const hexes = g.selectAll('.hex')
            .data(hexData)
            .join('polygon')
            .attr('class', 'hex')
            .attr('points', d => {
                const pos = getHexPosition(d.q, d.r);
                return hexPoints(pos.x, pos.y);
            })
            .attr('fill', d => {
                const data = impactData[d.name];
                return data ? colorScale(data.pct) : '#F7FDFC';
            })
            .attr('stroke', '#fff')
            .attr('stroke-width', 1)
            .style('display', 'none')
            .on('mousemove', function(event, d) {
                const data = impactData[d.name] || { pct: 0, num: 0, rev: 0 };
                showTooltip(d.name, data, event);
                g.selectAll('.hex')
                    .attr('stroke', '#fff')
                    .attr('stroke-width', 1);
                d3.select(this).attr('stroke', '#39C6C0').attr('stroke-width', 2);
            })
            .on('mouseout', hideTooltip);

        // View toggle
        let currentView = 'geo';

        function switchView(view) {
            currentView = view;
            if (view === 'geo') {
                geoPaths.style('display', null)
                    .attr('fill', d => {
                        const data = impactData[d.properties.Name];
                        return data ? colorScale(data.pct) : '#F7FDFC';
                    });
                hexes.style('display', 'none');
                document.getElementById('btn-geo').classList.add('active');
                document.getElementById('btn-hex').classList.remove('active');
            } else {
                geoPaths.style('display', 'none');
                hexes.style('display', null);
                document.getElementById('btn-geo').classList.remove('active');
                document.getElementById('btn-hex').classList.add('active');
            }
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        }

        document.getElementById('btn-geo').addEventListener('click', () => switchView('geo'));
        document.getElementById('btn-hex').addEventListener('click', () => switchView('hex'));

        // Search functionality
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');

        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            if (query.length < 2) {
                searchResults.style.display = 'none';
                return;
            }

            const matches = allConstituencies.filter(name =>
                name.toLowerCase().includes(query)
            ).slice(0, 10);

            if (matches.length === 0) {
                searchResults.style.display = 'none';
                return;
            }

            searchResults.innerHTML = matches.map(name => {
                const data = impactData[name] || { pct: 0, num: 0, rev: 0 };
                return `
                    <button class="search-result-item" data-name="${name}">
                        <div class="result-name">${name}</div>
                        <div class="result-value">${data.num.toLocaleString()} sales · ${data.pct.toFixed(2)}%</div>
                    </button>
                `;
            }).join('');

            searchResults.style.display = 'block';

            searchResults.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', function() {
                    const name = this.dataset.name;
                    searchInput.value = name;
                    searchResults.style.display = 'none';

                    // Show tooltip for selected constituency
                    const data = impactData[name] || { pct: 0, num: 0, rev: 0 };
                    tooltip.innerHTML = `
                        <h4>${name}</h4>
                        <div class="tooltip-row"><span>Projected sales</span><span>${data.num.toLocaleString()}</span></div>
                        <div class="tooltip-row"><span>Share</span><span>${data.pct.toFixed(2)}%</span></div>
                        <div class="tooltip-row"><span>Est. revenue</span><span>£${(data.rev / 1000000).toFixed(1)}m</span></div>
                    `;
                    tooltip.style.display = 'block';
                    tooltip.style.left = '50%';
                    tooltip.style.top = '50%';

                    // Highlight constituency
                    if (currentView === 'geo') {
                        g.selectAll('.constituency-path')
                            .attr('stroke', d => d.properties.Name === name ? '#39C6C0' : '#fff')
                            .attr('stroke-width', d => d.properties.Name === name ? 2 : 0.3);

                        // Zoom to constituency
                        const feature = geoData.features.find(f => f.properties.Name === name);
                        if (feature) {
                            const bounds = pathGenerator.bounds(feature);
                            const dx = bounds[1][0] - bounds[0][0];
                            const dy = bounds[1][1] - bounds[0][1];
                            const x = (bounds[0][0] + bounds[1][0]) / 2;
                            const y = (bounds[0][1] + bounds[1][1]) / 2;
                            const scale = Math.max(1, Math.min(8, 0.9 / Math.max(dx / width, dy / height)));
                            svg.transition().duration(750).call(
                                zoom.transform,
                                d3.zoomIdentity.translate(width / 2, height / 2).scale(scale).translate(-x, -y)
                            );
                        }
                    } else {
                        g.selectAll('.hex')
                            .attr('stroke', d => d.name === name ? '#39C6C0' : '#fff')
                            .attr('stroke-width', d => d.name === name ? 2 : 1);
                    }
                });
            });
        });

        // Close search when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.style.display = 'none';
            }
        });
    </script>
</body>
</html>'''

    return html_template


def main():
    """Main execution."""
    print("=" * 70)
    print("High Value Council Tax Surcharge - D3 Map Visualization")
    print("=" * 70)

    hexjson = load_hex_coordinates()
    geojson = load_geo_json()
    impact_data = load_impact_data()

    if impact_data is None:
        return

    print("Generating D3 map...")
    html_content = generate_d3_map_html(hexjson, geojson, impact_data)

    output_file = 'surcharge_map_by_revenue.html'
    with open(output_file, 'w') as f:
        f.write(html_content)
    print(f"Saved {output_file}")

    print("\n" + "=" * 70)
    print("Visualization complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()

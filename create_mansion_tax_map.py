#!/usr/bin/env python3
"""
Create hexagonal map visualization of UK mansion tax impact by constituency.

Generates a Plotly hexagonal map showing which constituencies would be most
affected by a mansion tax policy (£2,000 annual charge on properties above
£1.5m or £2m thresholds).
"""

import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


def load_hex_coordinates():
    """Load constituency hex grid coordinates from HexJSON."""
    print("Loading hex grid coordinates...")
    with open('data/uk-constituencies-2024.hexjson') as f:
        hexjson = json.load(f)

    # Extract hex grid positions
    constituencies = []
    for gss_code, hex_data in hexjson['hexes'].items():
        constituencies.append({
            'gss_code': gss_code,
            'constituency': hex_data['n'],
            'q': hex_data['q'],  # column
            'r': hex_data['r'],  # row
        })

    df = pd.DataFrame(constituencies)
    df['grid_x'] = df['q']
    df['grid_y'] = df['r']

    print(f"Loaded {len(df)} constituencies")
    return df


def load_impact_data(threshold_label='1m'):
    """Load mansion tax impact data."""
    print(f"Loading mansion tax impact data (£{threshold_label} threshold)...")
    impact_file = f'constituency_impact_{threshold_label}.csv'

    if not Path(impact_file).exists():
        print(f"ERROR: {impact_file} not found")
        print("Run: python analyze.py")
        return None

    df = pd.read_csv(impact_file)
    print(f"Loaded data for {len(df)} constituencies")
    return df


def create_hex_map(hex_coords, impact_data, threshold_label='1m'):
    """Create hexagonal map visualization."""
    print("Creating hexagonal map...")

    # Merge hex coordinates with impact data
    merged = hex_coords.merge(
        impact_data[['constituency', 'properties', 'revenue']],
        on='constituency',
        how='left'
    )

    # Fill NaN values (constituencies with no sales above threshold)
    merged['properties'] = merged['properties'].fillna(0)
    merged['revenue'] = merged['revenue'].fillna(0)

    # Apply hexagonal positioning (offset odd rows by 0.5 for "odd-r" layout)
    merged['plot_x'] = merged.apply(
        lambda row: row['grid_x'] + 0.5 if row['grid_y'] % 2 != 0 else row['grid_x'],
        axis=1
    )
    merged['plot_y'] = merged['grid_y']

    # Create hover text
    threshold_amount = '£1.5m' if threshold_label == '1m' else '£2m'
    merged['hover_text'] = merged.apply(
        lambda row: f"{row['constituency']}<br>"
                   f"Properties above {threshold_amount}: {int(row['properties'])}<br>"
                   f"Est. annual revenue: £{int(row['revenue']):,}",
        axis=1
    )

    # Create Plotly figure
    fig = go.Figure()

    max_properties = merged['properties'].max()

    fig.add_trace(go.Scatter(
        x=merged['plot_x'],
        y=merged['plot_y'],
        mode='markers',
        marker=dict(
            size=12,
            color=merged['properties'],
            colorscale='Teal',
            cmin=0,
            cmax=max_properties,
            colorbar=dict(
                title='Properties',
                thickness=15,
                len=0.8,
                x=0.95,
            ),
            symbol='hexagon',
            line=dict(width=0.5, color='white')
        ),
        text=merged['hover_text'],
        hoverinfo='text',
        showlegend=False
    ))

    threshold_title = '£1.5m' if threshold_label == '1m' else '£2m'
    fig.update_layout(
        title=dict(
            text=f'UK Mansion Tax Impact by Constituency<br><sub>Properties above {threshold_title} threshold</sub>',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False,
            scaleanchor='y',
            scaleratio=1
        ),
        yaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False
        ),
        height=800,
        width=1000,
        plot_bgcolor='white',
        margin=dict(t=100, b=40, l=40, r=120),
        hovermode='closest'
    )

    return fig


def main():
    """Main execution."""
    print("="*60)
    print("UK Mansion Tax Impact - Hexagonal Map Visualization")
    print("="*60)

    hex_coords = load_hex_coordinates()

    for threshold in ['1m', '2m']:
        impact_data = load_impact_data(threshold)
        if impact_data is None:
            continue

        fig = create_hex_map(hex_coords, impact_data, threshold)

        output_file = f'mansion_tax_map_{threshold}.html'
        fig.write_html(output_file)
        print(f"✓ Saved {output_file}")

        try:
            png_file = f'mansion_tax_map_{threshold}.png'
            fig.write_image(png_file, width=1200, height=900)
            print(f"✓ Saved {png_file}")
        except Exception as e:
            print(f"⚠ Could not save PNG: {e}")

    print("\n" + "="*60)
    print("Visualization complete!")
    print("="*60)


if __name__ == '__main__':
    main()

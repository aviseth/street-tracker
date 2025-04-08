#!/usr/bin/env python3
"""
Export analyzed walking data for Kepler.gl visualization.
"""
import os
import geopandas as gpd
import pandas as pd

def add_style_properties(gdf, style_type):
    """Add style properties to the GeoDataFrame."""
    if style_type == 'covered_street':
        gdf['stroke'] = '#FFD700'  # Gold color
        gdf['stroke-width'] = 3
        gdf['stroke-opacity'] = 1
    elif style_type == 'uncovered_street':
        gdf['stroke'] = '#4A5568'  # Gray color
        gdf['stroke-width'] = 1
        gdf['stroke-opacity'] = 0.6
    elif style_type == 'walk':
        gdf['stroke'] = '#3182CE'  # Blue color
        gdf['stroke-width'] = 2
        gdf['stroke-opacity'] = 0.8
    return gdf

def export_for_kepler(city):
    """Export analyzed data for a specific city."""
    # Create output directory
    output_dir = f"kepler_data_{city}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load analyzed data
    analyzed_dir = f"data/{city}_analyzed"
    streets_file = f"{analyzed_dir}/streets.geojson"
    walks_file = f"{analyzed_dir}/valid_walks.geojson"
    
    if not os.path.exists(streets_file) or not os.path.exists(walks_file):
        print(f"Missing analyzed data files for {city}")
        return
    
    streets_gdf = gpd.read_file(streets_file)
    walks_gdf = gpd.read_file(walks_file)
    
    # Export streets
    if not streets_gdf.empty:
        # Split streets into covered and uncovered
        covered_streets = streets_gdf[streets_gdf['covered']].copy()
        uncovered_streets = streets_gdf[~streets_gdf['covered']].copy()
        
        # Export covered streets
        if not covered_streets.empty:
            covered_streets['data_type'] = 'covered_street'
            covered_streets['coverage_percent'] = covered_streets['coverage_percent'].fillna(0)
            covered_streets = add_style_properties(covered_streets, 'covered_street')
            covered_file = os.path.join(output_dir, f"{city}_covered_streets.geojson")
            covered_streets.to_file(covered_file, driver='GeoJSON')
            print(f"Covered streets exported to {covered_file}")
        
        # Export uncovered streets
        if not uncovered_streets.empty:
            uncovered_streets['data_type'] = 'uncovered_street'
            uncovered_streets['coverage_percent'] = 0
            uncovered_streets = add_style_properties(uncovered_streets, 'uncovered_street')
            uncovered_file = os.path.join(output_dir, f"{city}_uncovered_streets.geojson")
            uncovered_streets.to_file(uncovered_file, driver='GeoJSON')
            print(f"Uncovered streets exported to {uncovered_file}")
    
    # Export walks
    if not walks_gdf.empty:
        walks_gdf['data_type'] = 'walk'
        walks_gdf = add_style_properties(walks_gdf, 'walk')
        walks_file = os.path.join(output_dir, f"{city}_walks.geojson")
        walks_gdf.to_file(walks_file, driver='GeoJSON')
        print(f"Walks exported to {walks_file}")

if __name__ == "__main__":
    # Export data for each city
    cities = ['london', 'blacksburg', 'mumbai']
    
    for city in cities:
        print(f"\nExporting data for {city.capitalize()}...")
        export_for_kepler(city) 
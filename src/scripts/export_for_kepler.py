#!/usr/bin/env python3
"""
Export street and walk data in a format suitable for Kepler.gl visualization.
"""
import os
import geopandas as gpd
import pandas as pd
from analyze_walks import analyze_walks

def add_style_properties(gdf, style_type):
    """Add style properties to the GeoDataFrame."""
    if style_type == 'walk':
        gdf['stroke'] = '#3182CE'  # Blue color
        gdf['stroke-width'] = 2
        gdf['stroke-opacity'] = 0.8
        gdf['stroke-dasharray'] = ''  # Empty string for solid line
    elif style_type == 'covered_street':
        gdf['stroke'] = '#FFD700'  # Gold color
        gdf['stroke-width'] = 3
        gdf['stroke-opacity'] = 1
    elif style_type == 'uncovered_street':
        gdf['stroke'] = '#4A5568'  # Gray color
        gdf['stroke-width'] = 1
        gdf['stroke-opacity'] = 0.6
    return gdf

def export_for_kepler(walks_gdf, streets_gdf, output_dir):
    """
    Export the data in a format suitable for Kepler.gl.
    
    Parameters:
    -----------
    walks_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing walks as LineStrings
    streets_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing streets with coverage information
    output_dir : str
        Directory to save the exported files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Export walks
    if not walks_gdf.empty:
        # Export all walks (including transit) for comparison
        all_walks = walks_gdf.copy()
        all_walks['data_type'] = 'all_walks'
        all_walks = add_style_properties(all_walks, 'walk')
        all_walks_file = os.path.join(output_dir, "all_walks.geojson")
        all_walks.to_file(all_walks_file, driver='GeoJSON')
        print(f"All walks exported to {all_walks_file}")
        
        # Filter out transit trips
        print("\nFiltering out transit trips...")
        walks_filtered = analyze_walks(walks_gdf)
        
        # Export filtered walks
        walks_filtered['data_type'] = 'walk'
        walks_filtered = add_style_properties(walks_filtered, 'walk')
        walks_file = os.path.join(output_dir, "walks.geojson")
        walks_filtered.to_file(walks_file, driver='GeoJSON')
        print(f"Filtered walks exported to {walks_file}")
        
        # Update streets coverage using only filtered walks
        print("\nUpdating street coverage with filtered walks...")
        from match_walks_to_streets import match_walks_to_streets
        streets_gdf = match_walks_to_streets(walks_filtered, streets_gdf, buffer_distance=8)
    
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
            covered_file = os.path.join(output_dir, "covered_streets.geojson")
            covered_streets.to_file(covered_file, driver='GeoJSON')
            print(f"Covered streets exported to {covered_file}")
        
        # Export uncovered streets
        if not uncovered_streets.empty:
            uncovered_streets['data_type'] = 'uncovered_street'
            uncovered_streets['coverage_percent'] = 0
            uncovered_streets = add_style_properties(uncovered_streets, 'uncovered_street')
            uncovered_file = os.path.join(output_dir, "uncovered_streets.geojson")
            uncovered_streets.to_file(uncovered_file, driver='GeoJSON')
            print(f"Uncovered streets exported to {uncovered_file}")

if __name__ == "__main__":
    # Test exporting data
    from parse_walks import parse_walks
    from load_streets import load_streets
    
    print("Loading and processing walk data...")
    walks_gdf = parse_walks(
        os.path.join("/Users/avise/Downloads/Takeout", "Fit", "Activities"),
        os.path.join("data", "processed_walks.geojson")
    )
    
    print("Loading street network...")
    streets_gdf = load_streets()
    
    print("Exporting data for Kepler.gl...")
    export_for_kepler(walks_gdf, streets_gdf, "kepler_data") 
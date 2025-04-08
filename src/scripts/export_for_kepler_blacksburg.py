#!/usr/bin/env python3
"""
Export Blacksburg street network data in a format suitable for Kepler.gl visualization.
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
    return gdf

def export_for_kepler(streets_gdf, output_dir):
    """
    Export the Blacksburg street network data in a format suitable for Kepler.gl.
    
    Parameters:
    -----------
    streets_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing streets with coverage information
    output_dir : str
        Directory to save the exported files
    """
    os.makedirs(output_dir, exist_ok=True)
    
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
            covered_file = os.path.join(output_dir, "blacksburg_covered_streets.geojson")
            covered_streets.to_file(covered_file, driver='GeoJSON')
            print(f"Covered streets exported to {covered_file}")
        
        # Export uncovered streets
        if not uncovered_streets.empty:
            uncovered_streets['data_type'] = 'uncovered_street'
            uncovered_streets['coverage_percent'] = 0
            uncovered_streets = add_style_properties(uncovered_streets, 'uncovered_street')
            uncovered_file = os.path.join(output_dir, "blacksburg_uncovered_streets.geojson")
            uncovered_streets.to_file(uncovered_file, driver='GeoJSON')
            print(f"Uncovered streets exported to {uncovered_file}")

if __name__ == "__main__":
    # Load Blacksburg streets
    from load_streets_blacksburg import load_streets
    
    print("Loading Blacksburg street network...")
    streets_gdf = load_streets()
    
    print("\nExporting data for Kepler.gl...")
    export_for_kepler(streets_gdf, "kepler_data_blacksburg") 
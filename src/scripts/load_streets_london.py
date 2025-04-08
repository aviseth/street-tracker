#!/usr/bin/env python3
"""
Load street network data for Greater London, UK from OpenStreetMap.
"""
import os
import geopandas as gpd
import osmnx as ox
import networkx as nx
from shapely.geometry import LineString
import pandas as pd

def load_streets(use_cache=True):
    """
    Load the street network for Greater London.
    
    Parameters:
    -----------
    use_cache : bool
        Whether to use cached data if available
    
    Returns:
    --------
    geopandas.GeoDataFrame
        Street network with columns for geometry and street properties
    """
    cache_file = os.path.join("data", "London_streets.geojson")
    
    if use_cache and os.path.exists(cache_file):
        print(f"Loading streets from cache: {cache_file}")
        return gpd.read_file(cache_file)
    
    print("Downloading Greater London street network from OpenStreetMap...")
    
    try:
        # Get network for all of Greater London
        G = ox.graph_from_place(
            "Greater London, UK",
            network_type='drive',
            simplify=True
        )
        
        print("Converting network to GeoDataFrame...")
        # Convert to GeoDataFrame
        streets = ox.graph_to_gdfs(G, nodes=False)
        
        # Keep only necessary columns
        if 'name' in streets.columns:
            streets = streets[['name', 'highway', 'geometry']]
        else:
            streets = streets[['highway', 'geometry']]
            streets['name'] = 'Unknown'
        
        # Fill NaN values in name
        streets['name'] = streets['name'].fillna('Unknown')
        
        # Create a unique ID for each street
        streets['street_id'] = range(len(streets))
        
        # Initialize coverage columns
        streets['covered'] = False
        streets['coverage_percent'] = 0.0
        
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        # Save to cache
        print(f"Saving streets to cache: {cache_file}")
        streets.to_file(cache_file, driver='GeoJSON')
        
        return streets
        
    except Exception as e:
        print(f"Error loading Greater London network: {e}")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

if __name__ == "__main__":
    # Test loading streets
    streets = load_streets(use_cache=False)
    print(f"\nLoaded {len(streets)} streets")
    print("\nStreet types:")
    print(streets['highway'].value_counts()) 
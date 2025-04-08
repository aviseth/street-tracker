#!/usr/bin/env python3
"""
Load street network data for Blacksburg, VA using OSMnx.
"""
import os
import geopandas as gpd
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString

def load_streets(use_cache=True):
    """
    Load the street network for Blacksburg and surrounding areas.
    
    Parameters:
    -----------
    use_cache : bool
        Whether to use cached data if available
    
    Returns:
    --------
    geopandas.GeoDataFrame
        Street network with columns for geometry and street properties
    """
    cache_file = os.path.join("data", "Blacksburg_streets.geojson")
    
    if use_cache and os.path.exists(cache_file):
        print(f"Loading streets from cache: {cache_file}")
        return gpd.read_file(cache_file)
    
    print("Downloading Blacksburg street network from OpenStreetMap...")
    
    try:
        # Define areas to include
        areas = [
            "Blacksburg, Virginia, USA",
            "Virginia Tech, Blacksburg, Virginia, USA",
            "Christiansburg, Virginia, USA"  # Including nearby Christiansburg
        ]
        
        all_streets = []
        for area in areas:
            print(f"Loading streets for {area}...")
            try:
                # Get network from place name
                G = ox.graph_from_place(area, network_type='drive')
                
                # Convert to GeoDataFrame
                streets_gdf = ox.graph_to_gdfs(G, nodes=False)
                
                # Keep only necessary columns
                if 'name' in streets_gdf.columns:
                    streets_gdf = streets_gdf[['name', 'highway', 'geometry']]
                else:
                    streets_gdf = streets_gdf[['highway', 'geometry']]
                    streets_gdf['name'] = 'Unknown'
                
                # Fill NaN values in name
                streets_gdf['name'] = streets_gdf['name'].fillna('Unknown')
                streets_gdf['area'] = area
                
                all_streets.append(streets_gdf)
                
            except Exception as e:
                print(f"Error loading street network for {area}: {e}")
                continue
        
        if not all_streets:
            print("No street networks could be loaded")
            return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        
        # Combine all street networks
        streets = pd.concat(all_streets, ignore_index=True)
        
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
        print(f"Error loading Blacksburg network: {e}")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

if __name__ == "__main__":
    # Test loading streets
    streets = load_streets(use_cache=False)
    print(f"\nLoaded {len(streets)} streets")
    print("\nStreet types:")
    print(streets['highway'].value_counts()) 
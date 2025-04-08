#!/usr/bin/env python3
"""
Load street network data for a given city using OSMnx.
"""
import os
import geopandas as gpd
import osmnx as ox
import pandas as pd
from shapely.geometry import LineString

# OSMnx configuration 
# Now handled using individual settings rather than the config() function

def load_area_streets(area_name, custom_bbox=None, network_type='drive'):
    """
    Load street network for a single area.
    """
    try:
        if custom_bbox:
            # Get network from bounding box
            G = ox.graph_from_bbox(
                custom_bbox[0], custom_bbox[1], custom_bbox[2], custom_bbox[3],
                network_type=network_type
            )
        else:
            # Get network from place name
            G = ox.graph_from_place(area_name, network_type=network_type)
        
        # Convert to GeoDataFrame
        streets_gdf = ox.graph_to_gdfs(G, nodes=False, edges=True)
        
        # Clean up the dataframe
        # Keep only necessary columns
        if 'name' in streets_gdf.columns:
            streets_gdf = streets_gdf[['name', 'highway', 'length', 'geometry']]
        else:
            streets_gdf = streets_gdf[['highway', 'length', 'geometry']]
            streets_gdf['name'] = 'Unknown'
        
        # Fill NaN values in name
        streets_gdf['name'] = streets_gdf['name'].fillna('Unknown')
        streets_gdf['area'] = area_name  # Add area name for reference
        
        return streets_gdf
    
    except Exception as e:
        print(f"Error loading street network for {area_name}: {e}")
        return None

def load_streets(city_name=None, custom_bbox=None, network_type='drive'):
    """
    Load street networks for multiple areas.
    
    Parameters:
    -----------
    city_name : str, optional
        Name of the city (used for cache filename)
    custom_bbox : tuple, optional
        Custom bounding box (north, south, east, west)
    network_type : str, optional
        Type of street network to load ('drive', 'walk', 'bike', 'all')
        
    Returns:
    --------
    geopandas.GeoDataFrame
        GeoDataFrame containing street data
    """
    cache_filename = os.path.join("data", "NYC_metro_streets.geojson")
    
    # Check if we have a cached version
    if os.path.exists(cache_filename):
        print(f"Loading streets from cache: {cache_filename}")
        return gpd.read_file(cache_filename)
    
    # Define areas to load
    areas = [
        "Manhattan, New York, USA",
        "Brooklyn, New York, USA",
        "Queens, New York, USA",
        "Staten Island, New York, USA",
        "Bronx, New York, USA",
        "Jersey City, New Jersey, USA",
        "Hoboken, New Jersey, USA"
    ]
    
    print("Downloading street networks for NYC metro area...")
    all_streets = []
    
    for area in areas:
        print(f"Loading streets for {area}...")
        streets_gdf = load_area_streets(area, network_type=network_type)
        if streets_gdf is not None:
            all_streets.append(streets_gdf)
    
    if not all_streets:
        print("No street networks could be loaded")
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    
    # Combine all street networks
    streets_gdf = pd.concat(all_streets, ignore_index=True)
    
    # Create a unique ID for each street segment
    streets_gdf['street_id'] = streets_gdf.index
    
    # Initialize coverage columns
    streets_gdf['covered'] = False
    streets_gdf['coverage_percent'] = 0.0
    
    # Save to file
    os.makedirs(os.path.dirname(cache_filename), exist_ok=True)
    streets_gdf.to_file(cache_filename, driver="GeoJSON")
    print(f"Saved combined street network to {cache_filename}")
    
    return streets_gdf


if __name__ == "__main__":
    # Test loading streets for NYC metro area
    streets_gdf = load_streets()
    print(f"Loaded {len(streets_gdf)} street segments") 
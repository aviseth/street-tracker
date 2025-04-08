#!/usr/bin/env python3
"""
Match GPS walking tracks to streets to determine which streets
have been walked and the coverage percentage.
"""
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import LineString, MultiLineString
from shapely.ops import split, snap, nearest_points
import warnings

def match_walks_to_streets(walks_gdf, streets_gdf, buffer_distance=5):
    """
    Match walks to streets and calculate coverage.
    
    Parameters:
    -----------
    walks_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing walks as LineStrings
    streets_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing streets as LineStrings
    buffer_distance : float, optional
        Distance in meters to buffer walks for matching to streets
        Default is 5 meters to ensure more accurate street matching
        
    Returns:
    --------
    geopandas.GeoDataFrame
        Streets GeoDataFrame with updated coverage information
    """
    if walks_gdf.empty or streets_gdf.empty:
        print("No walks or streets data available.")
        return streets_gdf
    
    # Ensure both GeoDataFrames use the same CRS
    walks_crs = walks_gdf.crs
    streets_crs = streets_gdf.crs
    
    if walks_crs != streets_crs:
        print(f"Converting walks from {walks_crs} to {streets_crs}")
        walks_gdf = walks_gdf.to_crs(streets_crs)
    
    # Make a copy of the streets GeoDataFrame to avoid modifying the original
    streets_result = streets_gdf.copy()
    
    # Create a buffer around each walk
    print("Creating buffers around walks...")
    # Convert to a projected CRS for accurate buffer calculations
    walks_projected = walks_gdf.to_crs('EPSG:3857')  # Web Mercator projection
    walks_buffer = walks_projected.copy()
    walks_buffer.geometry = walks_projected.geometry.buffer(buffer_distance)
    walks_buffer = walks_buffer.to_crs(streets_crs)  # Convert back to original CRS
    
    # Find intersections between walks and streets
    print("Finding intersections between walks and streets...")
    
    # Initialize coverage columns
    streets_result['covered'] = False
    streets_result['coverage_percent'] = 0.0
    
    # Process each street segment
    total_streets = len(streets_result)
    for idx, street in streets_result.iterrows():
        if idx % 1000 == 0:
            print(f"Processing street {idx}/{total_streets}")
        
        street_geom = street.geometry
        
        # Check if any walk buffer intersects with this street
        intersecting_buffers = walks_buffer[walks_buffer.geometry.intersects(street_geom)]
        
        if not intersecting_buffers.empty:
            # This street is at least partially covered
            streets_result.at[idx, 'covered'] = True
            
            # Calculate coverage percentage
            # For each intersecting walk, get the portion of the street that's covered
            covered_length = 0
            
            for _, walk_buffer in intersecting_buffers.iterrows():
                # Find the part of the street that intersects with the walk buffer
                intersection = street_geom.intersection(walk_buffer.geometry)
                
                if not intersection.is_empty:
                    if isinstance(intersection, (LineString, MultiLineString)):
                        covered_length += intersection.length
            
            # Calculate coverage percentage (capped at 100%)
            coverage_percent = min(100, (covered_length / street_geom.length) * 100)
            streets_result.at[idx, 'coverage_percent'] = coverage_percent
    
    # Print summary
    covered_streets = streets_result[streets_result['covered']]
    coverage_percent = len(covered_streets) / len(streets_result) * 100
    
    print(f"Total streets: {len(streets_result)}")
    print(f"Covered streets: {len(covered_streets)} ({coverage_percent:.2f}%)")
    
    return streets_result


if __name__ == "__main__":
    # Test matching walks to streets
    import os
    from parse_walks import parse_walks
    from load_streets import load_streets
    
    data_dir = os.path.join("data", "raw_walk_data")
    processed_walks_file = os.path.join("data", "processed_walks.geojson")
    
    walks_gdf = parse_walks(data_dir, processed_walks_file)
    streets_gdf = load_streets("New York, USA")
    
    streets_with_coverage = match_walks_to_streets(walks_gdf, streets_gdf)
    print(f"Streets with some coverage: {len(streets_with_coverage[streets_with_coverage['covered']])}") 
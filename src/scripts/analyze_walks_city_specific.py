#!/usr/bin/env python3
"""
Analyze walking data with city-specific parameters.
"""
import os
import geopandas as gpd
import pandas as pd
from datetime import datetime
import numpy as np
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
import math

# City-specific parameters
CITY_PARAMS = {
    'london': {
        'buffer_distance': 8,  # meters
        'max_walking_speed': 2.5,  # m/s (about 9 km/h)
        'min_walking_speed': 0.2,  # m/s
        'max_sinuosity': 3.0,  # for longer trips
        'max_direct_distance': 8000,  # meters
    },
    'blacksburg': {
        'buffer_distance': 10,  # meters
        'max_walking_speed': 2.8,  # m/s
        'min_walking_speed': 0.2,  # m/s
        'max_sinuosity': 3.5,  # for longer trips
        'max_direct_distance': 5000,  # meters
    },
    'mumbai': {
        'buffer_distance': 6,  # meters
        'max_walking_speed': 2.2,  # m/s
        'min_walking_speed': 0.1,  # m/s
        'max_sinuosity': 3.2,  # for longer trips
        'max_direct_distance': 6000,  # meters
    }
}

def calculate_path_metrics(path, city):
    """Calculate metrics for a path with city-specific parameters."""
    params = CITY_PARAMS[city]
    
    # Parse timestamps
    try:
        start_time = pd.to_datetime(path['start_time'])
        end_time = pd.to_datetime(path['end_time'])
    except:
        print(f"Error parsing timestamps for path: {path.get('source_file', 'unknown')}")
        return None
    
    # Calculate duration in seconds
    duration = (end_time - start_time).total_seconds()
    
    # Get coordinates
    coords = list(path['geometry'].coords)
    if len(coords) < 2:
        return None
    
    # Calculate direct distance (straight line between start and end)
    start_point = Point(coords[0])
    end_point = Point(coords[-1])
    direct_distance = start_point.distance(end_point)
    
    # Calculate path distance (sum of distances between consecutive points)
    path_distance = 0
    for i in range(len(coords) - 1):
        p1 = Point(coords[i])
        p2 = Point(coords[i + 1])
        path_distance += p1.distance(p2)
    
    # Calculate average speed (m/s)
    if duration > 0:
        avg_speed = path_distance / duration
    else:
        avg_speed = 0
    
    # Calculate sinuosity (path length / direct distance)
    if direct_distance > 0:
        sinuosity = path_distance / direct_distance
    else:
        sinuosity = 1
    
    return {
        'direct_distance': direct_distance,
        'path_distance': path_distance,
        'duration': duration,
        'avg_speed': avg_speed,
        'sinuosity': sinuosity
    }

def is_probable_transit(path, city):
    """Determine if a path is likely a transit trip using city-specific parameters."""
    params = CITY_PARAMS[city]
    metrics = calculate_path_metrics(path, city)
    
    if not metrics:
        return False
    
    # Check if path is too long to be walking
    if metrics['direct_distance'] > params['max_direct_distance']:
        return True
    
    # Check speed - only filter out if significantly above max walking speed
    if metrics['avg_speed'] > params['max_walking_speed'] * 1.2:  # Allow 20% buffer
        return True
    
    # Check if path is too straight (likely a transit route) - only for longer trips
    if metrics['direct_distance'] > 2000 and metrics['sinuosity'] < 1.05:
        return True
    
    # Check if path is too slow (likely stopped) - more lenient minimum speed
    if metrics['avg_speed'] < params['min_walking_speed'] and metrics['direct_distance'] > 500:
        return True
    
    return False

def analyze_walks(walks_gdf, streets_gdf, city):
    """Analyze walks and update street coverage with city-specific parameters."""
    params = CITY_PARAMS[city]
    
    # Create a copy of streets to avoid modifying the original
    streets = streets_gdf.copy()
    
    # Initialize coverage columns if they don't exist
    if 'covered' not in streets.columns:
        streets['covered'] = False
    if 'coverage_percent' not in streets.columns:
        streets['coverage_percent'] = 0.0
    
    # Filter out probable transit trips
    valid_geometries = []
    valid_attributes = []
    for _, walk in walks_gdf.iterrows():
        if not is_probable_transit(walk, city):
            valid_geometries.append(walk.geometry)
            valid_attributes.append({
                'start_time': walk.start_time,
                'end_time': walk.end_time,
                'source_file': walk.source_file
            })
    
    # Create GeoDataFrame from valid walks
    valid_walks_gdf = gpd.GeoDataFrame(
        valid_attributes,
        geometry=valid_geometries,
        crs=walks_gdf.crs
    )
    
    print(f"Found {len(valid_walks_gdf)} valid walks out of {len(walks_gdf)} total walks")
    
    # Update street coverage
    for _, street in streets.iterrows():
        street_geom = street.geometry
        covered_length = 0
        
        for _, walk in valid_walks_gdf.iterrows():
            walk_geom = walk.geometry
            buffered_walk = walk_geom.buffer(params['buffer_distance'])
            
            # Calculate intersection length
            intersection = street_geom.intersection(buffered_walk)
            if not intersection.is_empty:
                covered_length += intersection.length
        
        # Calculate coverage percentage
        if street_geom.length > 0:
            coverage_percent = (covered_length / street_geom.length) * 100
            streets.loc[street.name, 'coverage_percent'] = min(coverage_percent, 100)
            streets.loc[street.name, 'covered'] = coverage_percent > 0
    
    return streets, valid_walks_gdf

if __name__ == "__main__":
    # Test the analysis for each city
    cities = ['london', 'blacksburg', 'mumbai']
    
    for city in cities:
        print(f"\nAnalyzing walks for {city.capitalize()}...")
        
        # Load walks and streets
        walks_file = f"data/{city}_walks.geojson"
        streets_file = f"data/{city}_streets.geojson"
        
        if not os.path.exists(walks_file) or not os.path.exists(streets_file):
            print(f"Missing data files for {city}")
            continue
        
        walks_gdf = gpd.read_file(walks_file)
        streets_gdf = gpd.read_file(streets_file)
        
        # Analyze walks
        updated_streets, valid_walks = analyze_walks(walks_gdf, streets_gdf, city)
        
        # Save results
        output_dir = f"data/{city}_analyzed"
        os.makedirs(output_dir, exist_ok=True)
        
        updated_streets.to_file(f"{output_dir}/streets.geojson", driver='GeoJSON')
        valid_walks.to_file(f"{output_dir}/valid_walks.geojson", driver='GeoJSON')
        
        print(f"Analysis complete for {city}")
        print(f"Total walks: {len(walks_gdf)}")
        print(f"Valid walks: {len(valid_walks)}")
        print(f"Covered streets: {updated_streets['covered'].sum()}") 
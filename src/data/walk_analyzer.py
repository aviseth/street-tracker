"""
Module for analyzing walks and detecting transit trips.
"""

import geopandas as gpd
from shapely.geometry import LineString
from typing import List, Dict, Optional
from ..utils.config import CITY_PARAMS
from ..utils.geo_utils import calculate_path_metrics, create_buffer, calculate_coverage

def is_probable_transit(path: gpd.GeoDataFrame, city: str) -> bool:
    """Determine if a path is likely a transit trip using city-specific parameters.
    
    Args:
        path: GeoDataFrame containing the path
        city: Name of the city for city-specific parameters
        
    Returns:
        True if the path is likely a transit trip, False otherwise
    """
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

def analyze_walks(walks_gdf: gpd.GeoDataFrame, streets_gdf: gpd.GeoDataFrame, city: str) -> Dict:
    """Analyze walks and calculate street coverage.
    
    Args:
        walks_gdf: GeoDataFrame containing walks
        streets_gdf: GeoDataFrame containing street network
        city: Name of the city for city-specific parameters
        
    Returns:
        Dictionary containing analysis results
    """
    # Filter out transit trips
    valid_walks = []
    for _, walk in walks_gdf.iterrows():
        walk_df = gpd.GeoDataFrame([walk], crs=walks_gdf.crs)
        if not is_probable_transit(walk_df, city):
            valid_walks.append(walk)
    
    valid_walks_gdf = gpd.GeoDataFrame(valid_walks, crs=walks_gdf.crs)
    print(f"Found {len(valid_walks_gdf)} valid walks out of {len(walks_gdf)} total walks")
    
    # Create buffers for valid walks
    buffer_distance = CITY_PARAMS[city]['buffer_distance']
    walk_buffers = [create_buffer(walk.geometry, buffer_distance, walks_gdf.crs) 
                   for walk in valid_walks]
    
    # Calculate street coverage
    streets_gdf = streets_gdf.copy()
    streets_gdf['covered'] = False
    streets_gdf['coverage_percent'] = 0.0
    
    for idx, street in streets_gdf.iterrows():
        coverage = calculate_coverage(street.geometry, walk_buffers)
        streets_gdf.loc[idx, 'coverage_percent'] = coverage
        streets_gdf.loc[idx, 'covered'] = coverage > 0
    
    # Calculate overall statistics
    total_length = streets_gdf.geometry.length.sum()
    covered_length = streets_gdf[streets_gdf.covered].geometry.length.sum()
    coverage_percent = (covered_length / total_length * 100) if total_length > 0 else 0
    
    stats = {
        'total_walks': len(walks_gdf),
        'valid_walks': len(valid_walks_gdf),
        'total_streets': len(streets_gdf),
        'covered_streets': len(streets_gdf[streets_gdf.covered]),
        'total_length_km': total_length / 1000,
        'covered_length_km': covered_length / 1000,
        'coverage_percent': coverage_percent
    }
    
    return {
        'valid_walks': valid_walks_gdf,
        'streets': streets_gdf,
        'stats': stats
    } 
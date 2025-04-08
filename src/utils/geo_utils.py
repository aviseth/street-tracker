"""
Utility functions for geographic data processing.
"""

import geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import transform
import pyproj
from datetime import datetime
import pandas as pd
from typing import List, Tuple, Dict, Optional
from .config import DEFAULT_CRS, METRIC_CRS

def calculate_path_metrics(path: gpd.GeoDataFrame, city: str) -> Optional[Dict]:
    """Calculate metrics for a walking path.
    
    Args:
        path: GeoDataFrame containing the path geometry and timestamps
        city: Name of the city for city-specific parameters
        
    Returns:
        Dictionary containing path metrics or None if calculation fails
    """
    try:
        # Get start and end times
        start_time = pd.to_datetime(path['start_time'].iloc[0])
        end_time = pd.to_datetime(path['end_time'].iloc[-1])
        duration = (end_time - start_time).total_seconds()
        
        # Get path geometry in metric projection
        path_geom = path.geometry.iloc[0]
        if path_geom.crs != METRIC_CRS:
            path_geom = path_geom.to_crs(METRIC_CRS)
            
        # Calculate distances
        path_distance = path_geom.length
        start_point = Point(path_geom.coords[0])
        end_point = Point(path_geom.coords[-1])
        direct_distance = start_point.distance(end_point)
        
        # Calculate metrics
        avg_speed = path_distance / duration if duration > 0 else 0
        sinuosity = path_distance / direct_distance if direct_distance > 0 else 1
        
        return {
            'duration': duration,
            'path_distance': path_distance,
            'direct_distance': direct_distance,
            'avg_speed': avg_speed,
            'sinuosity': sinuosity
        }
    except Exception as e:
        print(f"Error calculating path metrics: {e}")
        return None

def reproject_geometry(geom, source_crs: str, target_crs: str):
    """Reproject a geometry from one CRS to another.
    
    Args:
        geom: Shapely geometry
        source_crs: Source coordinate reference system
        target_crs: Target coordinate reference system
        
    Returns:
        Reprojected geometry
    """
    project = pyproj.Transformer.from_crs(
        source_crs,
        target_crs,
        always_xy=True
    ).transform
    return transform(project, geom)

def create_buffer(geom, distance: float, crs: str = DEFAULT_CRS) -> gpd.GeoSeries:
    """Create a buffer around a geometry in meters.
    
    Args:
        geom: Geometry to buffer
        distance: Buffer distance in meters
        crs: Coordinate reference system of the geometry
        
    Returns:
        Buffered geometry in the original CRS
    """
    # Convert to metric CRS for buffering
    if crs != METRIC_CRS:
        geom = reproject_geometry(geom, crs, METRIC_CRS)
    
    # Create buffer
    buffered = geom.buffer(distance)
    
    # Convert back to original CRS
    if crs != METRIC_CRS:
        buffered = reproject_geometry(buffered, METRIC_CRS, crs)
    
    return buffered

def calculate_coverage(street_geom: LineString, walk_buffers: List[gpd.GeoSeries]) -> float:
    """Calculate what percentage of a street is covered by walk buffers.
    
    Args:
        street_geom: Street geometry
        walk_buffers: List of buffered walk geometries
        
    Returns:
        Coverage percentage (0-100)
    """
    if not walk_buffers:
        return 0.0
        
    # Combine all buffers
    combined_buffer = walk_buffers[0]
    for buffer in walk_buffers[1:]:
        combined_buffer = combined_buffer.union(buffer)
    
    # Calculate intersection
    intersection = street_geom.intersection(combined_buffer)
    if intersection.is_empty:
        return 0.0
    
    # Calculate coverage percentage
    coverage = intersection.length / street_geom.length * 100
    return min(coverage, 100.0)  # Cap at 100% 
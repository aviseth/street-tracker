#!/usr/bin/env python3
"""
Analyze walking paths to detect and filter out probable transit segments while preserving walking segments.
"""
import os
import geopandas as gpd
import pandas as pd
from datetime import datetime, timedelta
from shapely.geometry import LineString, Point
import numpy as np
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers."""
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def split_path_into_segments(coords, timestamps, segment_size=5):
    """Split a path into segments of roughly equal size."""
    segments = []
    segment_timestamps = []
    current_segment = []
    current_timestamps = []
    
    for i, (coord, timestamp) in enumerate(zip(coords, timestamps)):
        current_segment.append(coord)
        current_timestamps.append(timestamp)
        
        if len(current_segment) >= segment_size:
            if len(current_segment) >= 2:  # Only keep segments with at least 2 points
                segments.append(current_segment)
                segment_timestamps.append(current_timestamps)
            current_segment = [coord]  # Start new segment with overlap
            current_timestamps = [timestamp]
    
    # Add remaining points if they form a valid segment
    if len(current_segment) >= 2:
        segments.append(current_segment)
        segment_timestamps.append(current_timestamps)
    
    return segments, segment_timestamps

def calculate_segment_metrics(coords, timestamps):
    """Calculate metrics for a path segment."""
    if len(coords) < 2:
        return None
    
    # Parse timestamps if they're strings
    if isinstance(timestamps[0], str):
        timestamps = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in timestamps]
    
    # Calculate direct distance (as the crow flies)
    start_point = coords[0]
    end_point = coords[-1]
    direct_distance = haversine_distance(
        start_point[1], start_point[0],  # lat, lon
        end_point[1], end_point[0]
    )
    
    # Calculate actual path distance
    path_distance = 0
    for i in range(len(coords)-1):
        path_distance += haversine_distance(
            coords[i][1], coords[i][0],
            coords[i+1][1], coords[i+1][0]
        )
    
    # Calculate duration in hours
    duration = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
    
    # Calculate average speed in km/h
    avg_speed = path_distance / duration if duration > 0 else 0
    
    # Calculate path sinuosity (ratio of path distance to direct distance)
    sinuosity = path_distance / direct_distance if direct_distance > 0 else 1
    
    # Calculate point density (points per kilometer)
    point_density = len(coords) / path_distance if path_distance > 0 else float('inf')
    
    return {
        'direct_distance': direct_distance,
        'path_distance': path_distance,
        'duration_hours': duration,
        'avg_speed_kmh': avg_speed,
        'sinuosity': sinuosity,
        'point_density': point_density
    }

def is_probable_transit_segment(metrics):
    """Determine if a path segment is likely a transit segment."""
    if metrics is None:
        return True
    
    # Typical walking metrics
    MAX_WALKING_SPEED = 7  # km/h
    MIN_POINT_DENSITY = 50  # points per km for walking segments
    MIN_SINUOSITY = 1.05  # Almost straight line indicates transit
    
    # Check various conditions that indicate transit
    is_transit = (
        metrics['avg_speed_kmh'] > MAX_WALKING_SPEED or
        (metrics['sinuosity'] < MIN_SINUOSITY and 
         metrics['path_distance'] > 0.5 and  # Only check sinuosity for longer segments
         metrics['point_density'] < MIN_POINT_DENSITY)  # Low point density suggests GPS interpolation
    )
    
    return is_transit

def analyze_walks(walks_gdf):
    """
    Analyze walks and identify transit segments while preserving walking segments.
    
    Parameters:
    -----------
    walks_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing walks
        
    Returns:
    --------
    geopandas.GeoDataFrame
        Walks with transit segments removed
    """
    # Create a copy to store results
    walks = walks_gdf.copy()
    
    # Lists to store processed walking segments
    walking_segments = []
    segment_properties = []
    
    print("\nAnalyzing paths for transit detection...")
    total_paths = len(walks)
    
    for idx, row in walks.iterrows():
        if idx % 100 == 0:
            print(f"Processing path {idx}/{total_paths}")
        
        # Get coordinates and timestamps
        coords = list(row.geometry.coords)
        timestamps = [row.start_time] * len(coords) if not hasattr(row, 'timestamps') else row.timestamps
        
        # Split path into segments
        segments, segment_timestamps = split_path_into_segments(coords, timestamps)
        
        # Analyze each segment
        for segment_coords, seg_timestamps in zip(segments, segment_timestamps):
            metrics = calculate_segment_metrics(segment_coords, seg_timestamps)
            
            if metrics and not is_probable_transit_segment(metrics):
                # Keep this segment as walking
                segment_geom = LineString(segment_coords)
                walking_segments.append(segment_geom)
                
                # Keep relevant properties
                props = row.to_dict()
                props.pop('geometry')  # Remove geometry as we'll add it back
                props['metrics'] = metrics
                props['is_segment'] = True
                segment_properties.append(props)
    
    # Create new GeoDataFrame with walking segments
    if walking_segments:
        walks_filtered = gpd.GeoDataFrame(
            segment_properties,
            geometry=walking_segments,
            crs=walks_gdf.crs
        )
    else:
        walks_filtered = gpd.GeoDataFrame([], geometry=[], crs=walks_gdf.crs)
    
    # Print summary
    total_segments = sum(len(list(geom.coords)) - 1 for geom in walks_gdf.geometry)
    kept_segments = sum(len(list(geom.coords)) - 1 for geom in walks_filtered.geometry)
    
    print("\nAnalysis Summary:")
    print(f"Total path segments: {total_segments}")
    print(f"Walking segments kept: {kept_segments} ({kept_segments/total_segments*100:.1f}%)")
    
    return walks_filtered

if __name__ == "__main__":
    # Test analyzing walks
    from parse_walks import parse_walks
    
    print("Loading walk data...")
    walks_gdf = parse_walks(
        os.path.join("/Users/avise/Downloads/Takeout", "Fit", "Activities"),
        os.path.join("data", "processed_walks.geojson")
    )
    
    # Analyze and filter walks
    walks_filtered = analyze_walks(walks_gdf)
    
    # Save filtered walks
    output_file = os.path.join("data", "filtered_walks.geojson")
    walks_filtered.to_file(output_file, driver='GeoJSON')
    print(f"\nSaved filtered walks to {output_file}") 
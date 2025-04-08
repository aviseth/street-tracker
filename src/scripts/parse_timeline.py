#!/usr/bin/env python3
"""
Parse Google Timeline data from JSON and convert to GeoJSON format.
"""
import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
from datetime import datetime

def parse_timeline_json(timeline_file):
    """
    Parse Google Timeline JSON file and extract location data.
    
    Parameters:
    -----------
    timeline_file : str
        Path to the Timeline JSON file
        
    Returns:
    --------
    list
        List of dictionaries containing location data
    """
    with open(timeline_file, 'r') as f:
        data = json.load(f)
    
    locations = []
    
    # Process timeline objects
    for item in data.get('timelineObjects', []):
        # Handle place visits
        if 'placeVisit' in item:
            visit = item['placeVisit']
            location = visit.get('location', {})
            
            if 'latitudeE7' in location and 'longitudeE7' in location:
                locations.append({
                    'lat': location['latitudeE7'] / 1e7,
                    'lon': location['longitudeE7'] / 1e7,
                    'timestamp': visit.get('duration', {}).get('startTimestamp'),
                    'end_timestamp': visit.get('duration', {}).get('endTimestamp'),
                    'name': location.get('name'),
                    'address': location.get('address'),
                    'type': 'place_visit'
                })
        
        # Handle activities (movements)
        if 'activitySegment' in item:
            segment = item['activitySegment']
            
            # Get path points if available
            points = []
            for point in segment.get('simplifiedRawPath', {}).get('points', []):
                if 'latE7' in point and 'lngE7' in point:
                    points.append({
                        'lat': point['latE7'] / 1e7,
                        'lon': point['lngE7'] / 1e7,
                        'timestamp': point.get('timestamp')
                    })
            
            if points:
                locations.append({
                    'points': points,
                    'timestamp': segment.get('duration', {}).get('startTimestamp'),
                    'end_timestamp': segment.get('duration', {}).get('endTimestamp'),
                    'activity_type': segment.get('activityType'),
                    'distance': segment.get('distance'),  # in meters
                    'type': 'activity'
                })
    
    return locations

def create_geojson_features(locations):
    """
    Convert location data to GeoJSON features.
    
    Parameters:
    -----------
    locations : list
        List of location dictionaries
        
    Returns:
    --------
    list
        List of GeoJSON feature dictionaries
    """
    features = []
    
    for loc in locations:
        if loc['type'] == 'place_visit':
            # Create point feature for place visits
            point = Point(loc['lon'], loc['lat'])
            feature = {
                'geometry': point,
                'type': 'place_visit',
                'timestamp': loc['timestamp'],
                'end_timestamp': loc['end_timestamp'],
                'name': loc.get('name'),
                'address': loc.get('address')
            }
            features.append(feature)
        
        elif loc['type'] == 'activity' and len(loc['points']) > 1:
            # Create line feature for activities
            line_coords = [(p['lon'], p['lat']) for p in loc['points']]
            line = LineString(line_coords)
            feature = {
                'geometry': line,
                'type': 'activity',
                'activity_type': loc['activity_type'],
                'timestamp': loc['timestamp'],
                'end_timestamp': loc['end_timestamp'],
                'distance': loc.get('distance')
            }
            features.append(feature)
    
    return features

def parse_timeline(timeline_file, output_file):
    """
    Parse Google Timeline data and save to GeoJSON.
    
    Parameters:
    -----------
    timeline_file : str
        Path to the Timeline JSON file
    output_file : str
        Output GeoJSON file path
        
    Returns:
    --------
    geopandas.GeoDataFrame
        GeoDataFrame containing the parsed timeline data
    """
    print(f"Parsing timeline data from {timeline_file}...")
    
    # Parse timeline data
    locations = parse_timeline_json(timeline_file)
    
    if not locations:
        print("No valid location data found in the timeline file.")
        return None
    
    # Convert to GeoJSON features
    features = create_geojson_features(locations)
    
    if not features:
        print("No valid features created from the location data.")
        return None
    
    # Create GeoDataFrame
    timeline_gdf = gpd.GeoDataFrame(features)
    timeline_gdf.set_crs(epsg=4326, inplace=True)
    
    # Save to GeoJSON
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    timeline_gdf.to_file(output_file, driver='GeoJSON')
    
    print(f"Saved {len(timeline_gdf)} features to {output_file}")
    return timeline_gdf

if __name__ == "__main__":
    # Test parsing timeline
    timeline_file = os.path.join("Takeout 2", "Timeline", "Timeline Edits.json")
    output_file = os.path.join("data", "processed_timeline.geojson")
    
    timeline_gdf = parse_timeline(timeline_file, output_file) 
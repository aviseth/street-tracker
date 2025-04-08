#!/usr/bin/env python3
"""
Process raw walk data and prepare it for each city.
"""
import os
import glob
import geopandas as gpd
import pandas as pd
from datetime import datetime
import xml.etree.ElementTree as ET
from shapely.geometry import LineString, Point

def parse_gpx_file(gpx_file):
    """Parse a GPX file and extract track points."""
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    
    # Define namespaces
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    # Extract track points
    points = []
    for trkpt in root.findall('.//gpx:trkpt', ns):
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        time = trkpt.find('gpx:time', ns).text
        points.append((lon, lat, time))
    
    if len(points) < 2:
        return None
    
    # Create LineString and get start/end times
    coords = [(p[0], p[1]) for p in points]
    geometry = LineString(coords)
    start_time = points[0][2]
    end_time = points[-1][2]
    
    return {
        'geometry': geometry,
        'start_time': start_time,
        'end_time': end_time,
        'source_file': os.path.basename(gpx_file)
    }

def process_walks_for_city(city):
    """Process walks for a specific city."""
    # Get all GPX files
    gpx_files = glob.glob('data/raw_walk_data/*.gpx')
    
    # Process each file
    walks = []
    for gpx_file in gpx_files:
        walk_data = parse_gpx_file(gpx_file)
        if walk_data:
            walks.append(walk_data)
    
    if not walks:
        print(f"No valid walks found for {city}")
        return
    
    # Create GeoDataFrame
    walks_gdf = gpd.GeoDataFrame(walks, crs='EPSG:4326')
    
    # Save to file
    output_file = f"data/{city}_walks.geojson"
    walks_gdf.to_file(output_file, driver='GeoJSON')
    print(f"Processed {len(walks)} walks for {city}")

if __name__ == "__main__":
    # Process walks for each city
    cities = ['london', 'blacksburg', 'mumbai']
    
    for city in cities:
        print(f"\nProcessing walks for {city.capitalize()}...")
        process_walks_for_city(city) 
#!/usr/bin/env python3
"""
Parse walking data from GPX and TCX files and convert to a GeoDataFrame for analysis.
"""
import os
import glob
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
import warnings
from datetime import datetime
import xml.etree.ElementTree as ET

# Try to import gpxpy for GPX parsing
try:
    import gpxpy
    import gpxpy.gpx
    GPXPY_AVAILABLE = True
except ImportError:
    GPXPY_AVAILABLE = False
    warnings.warn("gpxpy not installed. GPX parsing will be limited.")

# Try to import fitparse for FIT file parsing
try:
    from fitparse import FitFile
    FITPARSE_AVAILABLE = True
except ImportError:
    FITPARSE_AVAILABLE = False
    warnings.warn("fitparse not installed. FIT file parsing will not be available.")


def parse_gpx(gpx_file):
    """Parse a GPX file and return a list of points with timestamps."""
    points = []
    
    if GPXPY_AVAILABLE:
        with open(gpx_file, 'r') as f:
            gpx = gpxpy.parse(f)
            
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        points.append({
                            'lat': point.latitude,
                            'lon': point.longitude,
                            'timestamp': point.time,
                            'elevation': point.elevation,
                            'source_file': os.path.basename(gpx_file)
                        })
    else:
        # Basic parsing if gpxpy is not available
        tree = ET.parse(gpx_file)
        root = tree.getroot()
        
        for track in root.findall('.//default:trkpt', namespaces):
            lat = float(track.get('lat'))
            lon = float(track.get('lon'))
            
            time_elem = track.find('default:time', namespaces)
            timestamp = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00')) if time_elem is not None else None
            
            ele_elem = track.find('default:ele', namespaces)
            elevation = float(ele_elem.text) if ele_elem is not None else None
            
            points.append({
                'lat': lat,
                'lon': lon,
                'timestamp': timestamp,
                'elevation': elevation,
                'source_file': os.path.basename(gpx_file)
            })
    
    return points


def parse_fit(fit_file):
    """Parse a FIT file and return a list of points with timestamps."""
    if not FITPARSE_AVAILABLE:
        warnings.warn(f"Cannot parse FIT file {fit_file}. fitparse not installed.")
        return []
    
    points = []
    
    try:
        fitfile = FitFile(fit_file)
        
        for record in fitfile.get_messages('record'):
            point = {}
            
            # Get all data from this record
            for data in record:
                if data.name == 'position_lat' and data.value is not None:
                    point['lat'] = data.value * (180 / 2**31)
                elif data.name == 'position_long' and data.value is not None:
                    point['lon'] = data.value * (180 / 2**31)
                elif data.name == 'timestamp' and data.value is not None:
                    point['timestamp'] = data.value
                elif data.name == 'altitude' and data.value is not None:
                    point['elevation'] = data.value
            
            if 'lat' in point and 'lon' in point:
                point['source_file'] = os.path.basename(fit_file)
                points.append(point)
    except Exception as e:
        warnings.warn(f"Error parsing FIT file {fit_file}: {e}")
    
    return points


def parse_tcx_file(tcx_file):
    """
    Parse a TCX file and return a list of points with timestamps.
    """
    tree = ET.parse(tcx_file)
    root = tree.getroot()
    
    # TCX uses a namespace, so we need to handle that
    ns = {'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
    
    points = []
    
    # Find all trackpoints
    trackpoints = root.findall('.//ns:Trackpoint', ns)
    
    for trackpoint in trackpoints:
        position = trackpoint.find('.//ns:Position', ns)
        time_elem = trackpoint.find('ns:Time', ns)
        
        if position is not None and time_elem is not None:
            lat = float(position.find('ns:LatitudeDegrees', ns).text)
            lon = float(position.find('ns:LongitudeDegrees', ns).text)
            time = datetime.fromisoformat(time_elem.text.replace('Z', '+00:00'))
            
            points.append({
                'lat': lat,
                'lon': lon,
                'time': time
            })
    
    return points


def create_linestring_from_points(points, source_file):
    """
    Create a LineString from a list of points and return a GeoJSON feature.
    """
    if not points:
        return None
        
    # Sort points by timestamp if available
    if 'time' in points[0]:
        points = sorted(points, key=lambda x: x['time'])
    
    # Create line coordinates
    line_coords = [(p['lon'], p['lat']) for p in points]
    
    if len(line_coords) < 2:
        return None
    
    # Create LineString
    line = LineString(line_coords)
    
    # Get start and end times if available
    start_time = points[0]['time'].isoformat() if 'time' in points[0] else None
    end_time = points[-1]['time'].isoformat() if 'time' in points[-1] else None
    
    return {
        'geometry': line,
        'start_time': start_time,
        'end_time': end_time,
        'source_file': source_file
    }


def parse_walks(data_dir, output_file):
    """
    Parse walking data from GPX and TCX files and save to GeoJSON.
    
    Parameters:
    -----------
    data_dir : str
        Directory containing GPX and TCX files
    output_file : str
        Output GeoJSON file path
        
    Returns:
    --------
    geopandas.GeoDataFrame
        GeoDataFrame containing the parsed walks
    """
    # Find all GPX and TCX files
    gpx_files = glob.glob(os.path.join(data_dir, "**/*.gpx"), recursive=True)
    tcx_files = glob.glob(os.path.join(data_dir, "**/*.tcx"), recursive=True)
    fit_files = glob.glob(os.path.join(data_dir, "**/*.fit"), recursive=True)
    
    print(f"Found {len(gpx_files)} GPX files and {len(tcx_files)} TCX files")
    
    walks = []
    
    # Process GPX files
    for gpx_file in gpx_files:
        points = parse_gpx(gpx_file)
        walk = create_linestring_from_points(points, os.path.basename(gpx_file))
        if walk:
            walks.append(walk)
    
    # Process TCX files
    for tcx_file in tcx_files:
        points = parse_tcx_file(tcx_file)
        if points:  # Only process if we got valid points
            walk = create_linestring_from_points(points, os.path.basename(tcx_file))
            if walk:
                walks.append(walk)
    
    # Process FIT files
    for fit_file in fit_files:
        points = parse_fit(fit_file)
        walk = create_linestring_from_points(points, os.path.basename(fit_file))
        if walk:
            walks.append(walk)
    
    if not walks:
        print("No valid walks found in the data directory.")
        return None
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(walks)
    
    # Set CRS to WGS84
    gdf.set_crs(epsg=4326, inplace=True)
    
    # Save to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    gdf.to_file(output_file, driver='GeoJSON')
    
    print(f"Saved {len(walks)} walks to {output_file}")
    return gdf


if __name__ == "__main__":
    # Test parsing walks
    data_dir = os.path.join("data", "raw_walk_data")
    output_file = os.path.join("data", "processed_walks.geojson")
    
    walks_gdf = parse_walks(data_dir, output_file)
    print(f"Saved {len(walks_gdf)} walks to {output_file}") 
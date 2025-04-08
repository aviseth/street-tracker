"""
Module for processing TCX files from Google Fit.
"""

import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import LineString, Point
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pytz
from ..utils.config import DEFAULT_CRS, MIN_WALK_DURATION, MIN_WALK_DISTANCE

def parse_tcx_file(file_path: str) -> Optional[Dict]:
    """Parse a TCX file and extract walk data.
    
    Args:
        file_path: Path to the TCX file
        
    Returns:
        Dictionary containing walk data or None if parsing fails
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # TCX files use a namespace
        ns = {'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}
        
        # Get activity type
        activity = root.find('.//ns:Activity', ns)
        if activity is None:
            return None
            
        activity_type = activity.get('Sport')
        if activity_type != 'Walking':
            return None
            
        # Get trackpoints
        trackpoints = []
        for trackpoint in root.findall('.//ns:Trackpoint', ns):
            time = trackpoint.find('ns:Time', ns)
            position = trackpoint.find('ns:Position', ns)
            
            if time is not None and position is not None:
                lat = position.find('ns:LatitudeDegrees', ns)
                lon = position.find('ns:LongitudeDegrees', ns)
                
                if lat is not None and lon is not None:
                    trackpoints.append({
                        'time': datetime.fromisoformat(time.text.replace('Z', '+00:00')),
                        'lat': float(lat.text),
                        'lon': float(lon.text)
                    })
        
        if len(trackpoints) < 2:
            return None
            
        # Create walk data
        coords = [(tp['lon'], tp['lat']) for tp in trackpoints]
        times = [tp['time'] for tp in trackpoints]
        
        return {
            'geometry': LineString(coords),
            'start_time': times[0],
            'end_time': times[-1],
            'source_file': Path(file_path).name
        }
        
    except Exception as e:
        print(f"Error parsing TCX file {file_path}: {e}")
        return None

def process_tcx_files(directory: str) -> gpd.GeoDataFrame:
    """Process all TCX files in a directory.
    
    Args:
        directory: Directory containing TCX files
        
    Returns:
        GeoDataFrame containing all valid walks
    """
    walks = []
    tcx_files = list(Path(directory).glob('*.tcx'))
    
    print(f"Found {len(tcx_files)} TCX files")
    
    for file_path in tcx_files:
        walk_data = parse_tcx_file(str(file_path))
        if walk_data is not None:
            # Calculate duration and distance
            duration = (walk_data['end_time'] - walk_data['start_time']).total_seconds()
            distance = walk_data['geometry'].length
            
            # Filter out walks that are too short
            if duration >= MIN_WALK_DURATION and distance >= MIN_WALK_DISTANCE:
                walks.append(walk_data)
    
    if not walks:
        return gpd.GeoDataFrame()
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(walks, crs=DEFAULT_CRS)
    
    print(f"Processed {len(gdf)} valid walks")
    return gdf 
#!/usr/bin/env python3
"""
Generate fake GPX data for testing the Street Tracker application.
This script creates synthetic walking routes in a specified city area.
"""
import os
import random
import gpxpy
import gpxpy.gpx
from datetime import datetime, timedelta
import numpy as np
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, LineString
import argparse

def generate_random_walk(center_lat, center_lon, 
                        min_points=100, max_points=500,
                        max_distance=0.01, # ~1km at equator
                        start_time=None):
    """
    Generate a random walk starting from the center coordinates.
    
    Parameters:
    -----------
    center_lat, center_lon : float
        Center coordinates to start the walk
    min_points, max_points : int
        Minimum and maximum number of points in the walk
    max_distance : float
        Maximum distance (in degrees) to move from center
    start_time : datetime, optional
        Starting time for the track points
        
    Returns:
    --------
    points : list of dict
        List of points with lat, lon, time, and elevation
    """
    if start_time is None:
        start_time = datetime.now() - timedelta(days=random.randint(1, 30))
    
    num_points = random.randint(min_points, max_points)
    
    # Generate a random walk
    points = []
    current_lat = center_lat
    current_lon = center_lon
    current_time = start_time
    
    for i in range(num_points):
        # Add some noise to create a walking path
        # This creates a random walk with some directional persistence
        if i > 0 and i % 20 == 0:
            # Occasionally make bigger direction changes to simulate turns
            delta_lat = random.uniform(-0.0003, 0.0003)
            delta_lon = random.uniform(-0.0003, 0.0003)
        else:
            # Smaller changes for a more natural path
            delta_lat = random.uniform(-0.0001, 0.0001)
            delta_lon = random.uniform(-0.0001, 0.0001)
        
        # Keep within bounds
        if abs(current_lat - center_lat) > max_distance:
            delta_lat = -delta_lat * 1.5  # Reverse direction and move faster
        if abs(current_lon - center_lon) > max_distance:
            delta_lon = -delta_lon * 1.5  # Reverse direction and move faster
        
        current_lat += delta_lat
        current_lon += delta_lon
        
        # Human walking speed varies, but typically 4-5 km/h = ~1.1-1.4 m/s
        # Time increment should be consistent with distance moved
        # 0.0001 degrees is roughly 10m at the equator
        distance_moved = ((delta_lat**2 + delta_lon**2) ** 0.5) * 111000  # rough conversion to meters
        time_increment = timedelta(seconds=max(1, int(distance_moved / 1.2)))  # assuming 1.2 m/s walking speed
        current_time += time_increment
        
        # Random elevation between 0 and 100m, with some continuity
        if i == 0:
            elevation = random.uniform(0, 100)
        else:
            elevation = points[-1]['elevation'] + random.uniform(-2, 2)  # Small elevation changes
            elevation = max(0, min(200, elevation))  # Keep between 0 and 200m
        
        points.append({
            'lat': current_lat,
            'lon': current_lon,
            'timestamp': current_time,
            'elevation': elevation
        })
    
    return points

def generate_realistic_walk(city_name, 
                           length_km=5, 
                           starting_point=None,
                           start_time=None,
                           network_type='walk'):
    """
    Generate a realistic walk along the street network of a city.
    
    Parameters:
    -----------
    city_name : str
        Name of the city for the walk
    length_km : float
        Approximate length of the walk in kilometers
    starting_point : tuple, optional
        (lat, lon) of the starting point. If None, a random point is chosen.
    start_time : datetime, optional
        Starting time for the track. If None, a random recent time is chosen.
    network_type : str
        Type of street network to use ('walk', 'drive', etc.)
        
    Returns:
    --------
    points : list of dict
        List of points with lat, lon, time, and elevation
    """
    print(f"Generating a {length_km}km walk in {city_name}...")
    
    # Get the street network
    G = ox.graph_from_place(city_name, network_type=network_type)
    
    # Choose a random starting node if not provided
    if starting_point is None:
        # Pick a random node
        nodes = list(G.nodes)
        start_node = random.choice(nodes)
        start_y, start_x = G.nodes[start_node]['y'], G.nodes[start_node]['x']
    else:
        # Find the nearest node to the provided starting point
        start_y, start_x = starting_point
        start_node = ox.distance.nearest_nodes(G, start_x, start_y)
    
    # Calculate how many nodes we need to visit for the desired length
    # Average edge length in OSM is around 100-200 meters, so we estimate 
    # the number of edges we should traverse
    edges_to_traverse = int(length_km * 1000 / 150)  # 150m average edge length
    
    # Perform a random walk on the graph
    current_node = start_node
    path_nodes = [current_node]
    
    for _ in range(edges_to_traverse):
        # Get neighbors of current node
        neighbors = list(G.neighbors(current_node))
        if not neighbors:
            break  # No neighbors, we're stuck
        
        # Pick a random neighbor that hasn't been visited recently (if possible)
        recent_nodes = path_nodes[-10:] if len(path_nodes) > 10 else path_nodes
        new_neighbors = [n for n in neighbors if n not in recent_nodes]
        
        if new_neighbors:
            next_node = random.choice(new_neighbors)
        else:
            next_node = random.choice(neighbors)  # Fall back to any neighbor
        
        path_nodes.append(next_node)
        current_node = next_node
    
    # Get the coordinates for each node in the path
    path_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path_nodes]
    
    # Generate a more detailed path by adding points between nodes
    detailed_path = []
    
    if start_time is None:
        start_time = datetime.now() - timedelta(days=random.randint(1, 30))
    
    current_time = start_time
    current_elevation = random.uniform(0, 100)
    
    for i in range(len(path_coords) - 1):
        start_lat, start_lon = path_coords[i]
        end_lat, end_lon = path_coords[i + 1]
        
        # Calculate distance between nodes (simplified)
        dist = ((end_lat - start_lat)**2 + (end_lon - start_lon)**2) ** 0.5
        dist_meters = dist * 111000  # rough conversion to meters
        
        # Determine number of points to generate between nodes
        # More points for longer segments
        num_points = max(5, int(dist_meters / 5))  # A point every ~5 meters
        
        for j in range(num_points):
            # Interpolate between nodes
            fraction = j / num_points
            lat = start_lat + fraction * (end_lat - start_lat)
            lon = start_lon + fraction * (end_lon - start_lon)
            
            # Add some small random noise for realism
            lat += random.uniform(-0.00001, 0.00001)
            lon += random.uniform(-0.00001, 0.00001)
            
            # Increment time (walking at ~1.2 m/s on average)
            segment_dist = dist_meters / num_points
            time_increment = timedelta(seconds=int(segment_dist / 1.2))
            current_time += time_increment
            
            # Change elevation gradually
            current_elevation += random.uniform(-0.5, 0.5)
            current_elevation = max(0, min(200, current_elevation))
            
            detailed_path.append({
                'lat': lat,
                'lon': lon,
                'timestamp': current_time,
                'elevation': current_elevation
            })
    
    return detailed_path

def create_gpx_file(points, filename, track_name=None):
    """
    Create a GPX file from a list of points.
    
    Parameters:
    -----------
    points : list of dict
        Points with lat, lon, timestamp, and elevation
    filename : str
        Output GPX filename
    track_name : str, optional
        Name for the GPX track
    """
    gpx = gpxpy.gpx.GPX()
    
    # Create track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    
    if track_name:
        gpx_track.name = track_name
    
    # Create segment
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    # Add points
    for point in points:
        gpx_point = gpxpy.gpx.GPXTrackPoint(
            latitude=point['lat'],
            longitude=point['lon'],
            elevation=point['elevation'],
            time=point['timestamp']
        )
        gpx_segment.points.append(gpx_point)
    
    # Save to file
    with open(filename, 'w') as f:
        f.write(gpx.to_xml())
    
    print(f"Created GPX file with {len(points)} points: {filename}")

def generate_test_walks(city_name="New York, USA", 
                       output_dir="data/raw_walk_data", 
                       num_walks=5,
                       min_length_km=2, 
                       max_length_km=10):
    """
    Generate multiple test walks for a city.
    
    Parameters:
    -----------
    city_name : str
        Name of the city
    output_dir : str
        Directory to save the GPX files
    num_walks : int
        Number of walks to generate
    min_length_km, max_length_km : float
        Range of walk lengths in kilometers
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")
    
    print(f"Generating {num_walks} test walks for {city_name}...")
    
    # Generate a realistic starting point once and reuse it
    # This makes multiple walks start from somewhat the same area
    try:
        # Get an approximate center for the city
        gdf = ox.geocode_to_gdf(city_name)
        center_point = gdf.geometry.centroid.iloc[0]
        center_lat, center_lon = center_point.y, center_point.x
    except Exception:
        # Fallback to hardcoded coordinates for New York
        if "new york" in city_name.lower():
            center_lat, center_lon = 40.7128, -74.0060
        else:
            # Generic fallback
            center_lat, center_lon = 0, 0
            print(f"Could not geocode {city_name}, using default coordinates")
    
    for i in range(num_walks):
        # Random walk length
        length_km = random.uniform(min_length_km, max_length_km)
        
        # Random start time within the last 3 months
        days_ago = random.randint(1, 90)
        start_time = datetime.now() - timedelta(days=days_ago, 
                                               hours=random.randint(0, 23),
                                               minutes=random.randint(0, 59))
        
        # Slightly vary the starting point for each walk
        start_lat = center_lat + random.uniform(-0.005, 0.005)
        start_lon = center_lon + random.uniform(-0.005, 0.005)
        
        try:
            # Try to generate a realistic walk
            points = generate_realistic_walk(
                city_name=city_name,
                length_km=length_km,
                starting_point=(start_lat, start_lon),
                start_time=start_time
            )
        except Exception as e:
            print(f"Error generating realistic walk: {e}")
            print("Falling back to random walk generation...")
            
            # Fallback to simple random walk
            points = generate_random_walk(
                center_lat=start_lat,
                center_lon=start_lon,
                min_points=int(length_km * 100),  # ~100 points per km
                max_points=int(length_km * 200),  # ~200 points per km
                max_distance=length_km / 100,  # Rough conversion to degrees
                start_time=start_time
            )
        
        # Create a filename with date
        date_str = start_time.strftime("%Y-%m-%d")
        filename = os.path.join(output_dir, f"walk_{date_str}_{i+1}.gpx")
        
        # Create GPX file
        create_gpx_file(
            points=points,
            filename=filename,
            track_name=f"Walk {i+1} - {date_str} - {length_km:.1f}km"
        )
    
    print(f"Generated {num_walks} test walks in {output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate fake GPS data for testing")
    parser.add_argument("--city", type=str, default="New York, USA", 
                        help="City name for the walks")
    parser.add_argument("--num_walks", type=int, default=5, 
                        help="Number of walks to generate")
    parser.add_argument("--min_length", type=float, default=2, 
                        help="Minimum walk length in km")
    parser.add_argument("--max_length", type=float, default=8, 
                        help="Maximum walk length in km")
    parser.add_argument("--output_dir", type=str, default="data/raw_walk_data", 
                        help="Directory to save GPX files")
    
    args = parser.parse_args()
    
    generate_test_walks(
        city_name=args.city,
        output_dir=args.output_dir,
        num_walks=args.num_walks,
        min_length_km=args.min_length,
        max_length_km=args.max_length
    ) 
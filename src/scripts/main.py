#!/usr/bin/env python3
"""
Main script to process and visualize walking data from various sources.
"""
import os
import geopandas as gpd
from scripts.parse_walks import parse_walks
from scripts.parse_timeline import parse_timeline
from scripts.load_streets import load_streets
from scripts.match_walks_to_streets import match_walks_to_streets
from scripts.visualize_map import create_map

def main():
    # File paths using absolute paths
    fit_data_dir = os.path.join("/Users/avise/Downloads/Takeout", "Fit", "Activities")
    timeline_file = os.path.join("/Users/avise/Downloads/Takeout_2", "Timeline", "Timeline Edits.json")
    processed_walks_file = os.path.join("data", "processed_walks.geojson")
    processed_timeline_file = os.path.join("data", "processed_timeline.geojson")
    output_map_file = os.path.join("output", "walk_coverage_map.html")
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Step 1: Parse walk data from Google Fit
    print("Step 1: Parsing walk data...")
    walks_gdf = parse_walks(fit_data_dir, processed_walks_file)
    
    # Step 2: Parse timeline data
    print("\nStep 2: Parsing timeline data...")
    timeline_gdf = parse_timeline(timeline_file, processed_timeline_file)
    
    # Step 3: Load street network for New York
    print("\nStep 3: Loading street network for New York, USA...")
    streets_gdf = load_streets("New York, USA")
    
    # Step 4: Match walks to streets
    print("\nStep 4: Matching walks to streets...")
    if walks_gdf is not None:
        streets_with_coverage = match_walks_to_streets(walks_gdf, streets_gdf)
    else:
        print("No walk data available for matching.")
        streets_with_coverage = streets_gdf
    
    # Step 5: Create map visualization
    print("\nStep 5: Creating map visualization...")
    create_map(
        walks_gdf if walks_gdf is not None else gpd.GeoDataFrame(),
        streets_with_coverage,
        output_map_file,
        timeline_data=timeline_gdf
    )
    
    print(f"\nDone! Map saved to {output_map_file}")

if __name__ == "__main__":
    main()
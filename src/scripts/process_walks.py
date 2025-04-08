"""
Main script for processing walks from TCX files.
"""

import sys
from pathlib import Path
import geopandas as gpd
import osmnx as ox
from ..data.tcx_processor import process_tcx_files
from ..data.walk_analyzer import analyze_walks
from ..data.kepler_exporter import export_for_kepler
from ..utils.config import RAW_WALK_DATA_DIR, PROCESSED_DATA_DIR, CITY_PARAMS

def main():
    """Main function to process walks and analyze coverage."""
    # Create output directory
    Path(PROCESSED_DATA_DIR).mkdir(parents=True, exist_ok=True)
    
    # Process TCX files
    print("Processing TCX files...")
    walks_gdf = process_tcx_files(RAW_WALK_DATA_DIR)
    if walks_gdf.empty:
        print("No valid walks found.")
        sys.exit(1)
    
    # Save processed walks
    walks_file = Path(PROCESSED_DATA_DIR) / "processed_walks.geojson"
    walks_gdf.to_file(walks_file, driver='GeoJSON')
    print(f"Saved {len(walks_gdf)} walks to {walks_file}")
    
    # Process each city
    for city in CITY_PARAMS.keys():
        print(f"\nProcessing {city}...")
        
        # Load or download street network
        streets_file = Path(PROCESSED_DATA_DIR) / f"{city}_streets.geojson"
        if streets_file.exists():
            print(f"Loading street network from {streets_file}")
            streets_gdf = gpd.read_file(streets_file)
        else:
            print(f"Downloading street network for {city}")
            bbox = CITY_PARAMS[city]['bbox']
            streets_gdf = ox.graph_to_gdfs(
                ox.graph_from_bbox(
                    bbox[1], bbox[3], bbox[0], bbox[2],
                    network_type='drive'
                )
            )[1]
            streets_gdf.to_file(streets_file, driver='GeoJSON')
        
        # Filter walks for this city
        city_walks = walks_gdf[walks_gdf.geometry.intersects(streets_gdf.unary_union)]
        if city_walks.empty:
            print(f"No walks found in {city}")
            continue
        
        # Analyze walks and calculate coverage
        print(f"Analyzing {len(city_walks)} walks in {city}")
        results = analyze_walks(city_walks, streets_gdf, city)
        
        # Export results for Kepler.gl
        export_for_kepler(results, city)

if __name__ == '__main__':
    main() 
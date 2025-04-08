"""
Module for exporting data to Kepler.gl format.
"""

import geopandas as gpd
from pathlib import Path
from typing import Dict
from ..utils.config import KEPLER_DATA_DIR

def export_for_kepler(analysis_results: Dict, city: str) -> None:
    """Export analysis results to GeoJSON files for Kepler.gl visualization.
    
    Args:
        analysis_results: Dictionary containing analysis results
        city: Name of the city
    """
    # Create output directory
    output_dir = Path(f"{KEPLER_DATA_DIR}_{city.lower()}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Export walks
    walks_gdf = analysis_results['valid_walks']
    if not walks_gdf.empty:
        walks_file = output_dir / f"{city.lower()}_walks.geojson"
        walks_gdf.to_file(walks_file, driver='GeoJSON')
        print(f"Exported {len(walks_gdf)} walks to {walks_file}")
    
    # Export streets
    streets_gdf = analysis_results['streets']
    if not streets_gdf.empty:
        # Split into covered and uncovered streets
        covered_streets = streets_gdf[streets_gdf.covered].copy()
        uncovered_streets = streets_gdf[~streets_gdf.covered].copy()
        
        # Export covered streets
        if not covered_streets.empty:
            covered_file = output_dir / f"{city.lower()}_covered_streets.geojson"
            covered_streets.to_file(covered_file, driver='GeoJSON')
            print(f"Exported {len(covered_streets)} covered streets to {covered_file}")
        
        # Export uncovered streets
        if not uncovered_streets.empty:
            uncovered_file = output_dir / f"{city.lower()}_uncovered_streets.geojson"
            uncovered_streets.to_file(uncovered_file, driver='GeoJSON')
            print(f"Exported {len(uncovered_streets)} uncovered streets to {uncovered_file}")
    
    # Print statistics
    stats = analysis_results['stats']
    print("\nAnalysis Statistics:")
    print(f"Total walks: {stats['total_walks']}")
    print(f"Valid walks: {stats['valid_walks']}")
    print(f"Total streets: {stats['total_streets']}")
    print(f"Covered streets: {stats['covered_streets']}")
    print(f"Total length: {stats['total_length_km']:.2f} km")
    print(f"Covered length: {stats['covered_length_km']:.2f} km")
    print(f"Coverage: {stats['coverage_percent']:.2f}%") 
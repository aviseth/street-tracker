#!/usr/bin/env python3
"""
Create an interactive map visualization showing street coverage.
"""
import os
import folium
import geopandas as gpd
import pandas as pd
import matplotlib.colors as mcolors
from folium.plugins import MarkerCluster

def default_street_style(feature):
    """Default style function for streets based on coverage."""
    covered = feature['properties']['covered']
    coverage = feature['properties']['coverage_percent']
    
    if not covered:
        return {
            'color': '#000000',  # Black for uncovered streets
            'weight': 4,         # Thicker lines
            'opacity': 1.0       # Full opacity
        }
    else:
        # Use high contrast colors: purple to orange
        coverage_normalized = min(1.0, max(0.0, coverage / 100))
        color = mcolors.to_hex(
            mcolors.LinearSegmentedColormap.from_list(
                'coverage', ['#9932CC', '#FFA500']  # Purple to Orange
            )(coverage_normalized)
        )
        
        return {
            'color': color,
            'weight': 5,         # Even thicker lines for covered streets
            'opacity': 1.0       # Full opacity
        }

def create_map(walks_gdf, streets_gdf, output_file, timeline_data=None, style_function=None):
    """
    Create an interactive map showing walks, streets, and timeline data.
    
    Parameters:
    -----------
    walks_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing walks as LineStrings
    streets_gdf : geopandas.GeoDataFrame
        GeoDataFrame containing streets with coverage information
    output_file : str
        Path to save the HTML map
    timeline_data : geopandas.GeoDataFrame, optional
        GeoDataFrame containing timeline data (places and activities)
    style_function : function, optional
        Custom style function for streets
    """
    if walks_gdf.empty and streets_gdf.empty and (timeline_data is None or timeline_data.empty):
        print("No data available for visualization.")
        return None
    
    # Determine map center and bounds from all available data
    bounds = None
    
    if not streets_gdf.empty:
        bounds = streets_gdf.total_bounds
    elif not walks_gdf.empty:
        bounds = walks_gdf.total_bounds
    elif timeline_data is not None and not timeline_data.empty:
        bounds = timeline_data.total_bounds
    
    if bounds is not None:
        map_center = [
            (bounds[1] + bounds[3]) / 2,  # Average of min and max latitude
            (bounds[0] + bounds[2]) / 2   # Average of min and max longitude
        ]
        # Calculate appropriate zoom level based on bounds
        lat_diff = bounds[3] - bounds[1]
        lon_diff = bounds[2] - bounds[0]
        max_diff = max(lat_diff, lon_diff)
        if max_diff > 0.5:
            zoom_start = 11
        elif max_diff > 0.2:
            zoom_start = 13
        else:
            zoom_start = 15
    else:
        # Default to New York City if no data
        map_center = [40.7128, -74.0060]
        zoom_start = 14
    
    # Create map with dark theme for better visibility
    m = folium.Map(
        location=map_center,
        zoom_start=zoom_start,
        tiles="CartoDB dark_matter"
    )
    
    # Add streets to map
    if not streets_gdf.empty:
        print("Adding streets to map...")
        streets_layer = folium.GeoJson(
            streets_gdf.__geo_interface__,
            name="Streets",
            style_function=style_function or default_street_style,
            tooltip=folium.GeoJsonTooltip(
                fields=['street_id', 'coverage_percent'],
                aliases=['Street ID', 'Coverage (%)'],
                localize=True,
                sticky=False,
                labels=True,
                style="""
                    background-color: #F0EFEF;
                    border: 2px solid black;
                    border-radius: 3px;
                    box-shadow: 3px;
                """
            )
        )
        streets_layer.add_to(m)
    
    # Add walks to map
    if not walks_gdf.empty:
        print("Adding walks to map...")
        walks_layer = folium.GeoJson(
            walks_gdf.__geo_interface__,
            name="Walks",
            style_function=lambda x: {
                'color': '#3388ff',
                'weight': 3,
                'opacity': 0.7
            }
        )
        walks_layer.add_to(m)
    
    # Add timeline data to map
    if timeline_data is not None and not timeline_data.empty:
        print("Adding timeline data to map...")
        
        # Split timeline data into places and activities
        places = timeline_data[timeline_data['type'] == 'place_visit']
        activities = timeline_data[timeline_data['type'] == 'activity']
        
        # Add places as markers
        if not places.empty:
            places_group = folium.FeatureGroup(name="Places")
            for idx, place in places.iterrows():
                popup_text = f"""
                    <b>{place.get('name', 'Unknown Place')}</b><br>
                    {place.get('address', '')}<br>
                    From: {place.get('timestamp', '')}<br>
                    To: {place.get('end_timestamp', '')}
                """
                folium.CircleMarker(
                    location=[place.geometry.y, place.geometry.x],
                    radius=8,
                    color="#ff7800",
                    fill=True,
                    popup=popup_text,
                    weight=2
                ).add_to(places_group)
            places_group.add_to(m)
        
        # Add activities as lines
        if not activities.empty:
            activities_layer = folium.GeoJson(
                activities.__geo_interface__,
                name="Timeline Activities",
                style_function=lambda x: {
                    'color': '#ff0000',
                    'weight': 2,
                    'opacity': 0.5
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=['activity_type', 'distance'],
                    aliases=['Activity', 'Distance (m)'],
                    localize=True,
                    sticky=False,
                    labels=True
                )
            )
            activities_layer.add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Save map to file
    output_dir = os.path.dirname(output_file)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Saving map to {output_file}...")
    m.save(output_file)
    
    return m


if __name__ == "__main__":
    # Test creating a map
    import os
    from parse_walks import parse_walks
    from load_streets import load_streets
    from match_walks_to_streets import match_walks_to_streets
    
    data_dir = os.path.join("data", "raw_walk_data")
    processed_walks_file = os.path.join("data", "processed_walks.geojson")
    output_map_file = os.path.join("output", "walk_coverage_map.html")
    
    walks_gdf = parse_walks(data_dir, processed_walks_file)
    streets_gdf = load_streets("New York, USA")
    streets_with_coverage = match_walks_to_streets(walks_gdf, streets_gdf)
    
    create_map(walks_gdf, streets_with_coverage, output_map_file)
    print(f"Map saved to {output_map_file}") 
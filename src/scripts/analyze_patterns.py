#!/usr/bin/env python3
"""
Analyze walking patterns to generate insights about walking behavior and routes.
"""
import os
import geopandas as gpd
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

def extract_time_info(walks_gdf):
    """Extract temporal information from walks."""
    time_info = []
    
    for idx, row in walks_gdf.iterrows():
        if hasattr(row, 'timestamps') and len(row.timestamps) > 0:
            start_time = pd.to_datetime(row.timestamps[0])
            end_time = pd.to_datetime(row.timestamps[-1])
            
            # Extract time components
            time_info.append({
                'walk_id': idx,
                'start_time': start_time,
                'end_time': end_time,
                'duration': (end_time - start_time).total_seconds() / 3600,  # hours
                'day_of_week': start_time.day_name(),
                'hour_of_day': start_time.hour,
                'month': start_time.month,
                'is_weekend': start_time.weekday() >= 5,
                'metrics': row.metrics if hasattr(row, 'metrics') else None
            })
    
    return pd.DataFrame(time_info)

def analyze_temporal_patterns(time_df):
    """Analyze walking patterns across different time periods."""
    results = {
        'hourly_stats': time_df.groupby('hour_of_day').agg({
            'duration': ['count', 'mean', 'sum'],
            'metrics': lambda x: np.mean([m['avg_speed_kmh'] if m else 0 for m in x])
        }),
        'daily_stats': time_df.groupby('day_of_week').agg({
            'duration': ['count', 'mean', 'sum'],
            'metrics': lambda x: np.mean([m['path_distance'] if m else 0 for m in x])
        }),
        'weekend_vs_weekday': time_df.groupby('is_weekend').agg({
            'duration': ['count', 'mean', 'sum'],
            'metrics': lambda x: np.mean([m['path_distance'] if m else 0 for m in x])
        })
    }
    return results

def analyze_route_patterns(walks_gdf):
    """Analyze patterns in walking routes."""
    route_stats = {
        'total_distance': sum(row.metrics['path_distance'] for idx, row in walks_gdf.iterrows() if hasattr(row, 'metrics')),
        'avg_segment_length': np.mean([row.metrics['path_distance'] for idx, row in walks_gdf.iterrows() if hasattr(row, 'metrics')]),
        'avg_speed': np.mean([row.metrics['avg_speed_kmh'] for idx, row in walks_gdf.iterrows() if hasattr(row, 'metrics')]),
        'avg_sinuosity': np.mean([row.metrics['sinuosity'] for idx, row in walks_gdf.iterrows() if hasattr(row, 'metrics')])
    }
    return route_stats

def identify_common_areas(walks_gdf, grid_size=0.001):
    """Identify frequently visited areas using a grid-based approach."""
    # Create a grid of points
    bounds = walks_gdf.total_bounds
    x_grid = np.arange(bounds[0], bounds[2], grid_size)
    y_grid = np.arange(bounds[1], bounds[3], grid_size)
    
    # Count visits to each grid cell
    grid_counts = defaultdict(int)
    
    for idx, row in walks_gdf.iterrows():
        coords = list(row.geometry.coords)
        for x, y in coords:
            grid_x = int((x - bounds[0]) / grid_size)
            grid_y = int((y - bounds[1]) / grid_size)
            grid_counts[(grid_x, grid_y)] += 1
    
    return grid_counts

def plot_temporal_patterns(time_df, output_dir):
    """Generate plots for temporal patterns."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Hourly activity plot
    plt.figure(figsize=(12, 6))
    hourly_counts = time_df.groupby('hour_of_day')['duration'].count()
    sns.barplot(x=hourly_counts.index, y=hourly_counts.values)
    plt.title('Walking Activity by Hour of Day')
    plt.xlabel('Hour')
    plt.ylabel('Number of Walks')
    plt.savefig(os.path.join(output_dir, 'hourly_activity.png'))
    plt.close()
    
    # Daily pattern plot
    plt.figure(figsize=(12, 6))
    daily_counts = time_df.groupby('day_of_week')['duration'].count()
    daily_counts = daily_counts.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    sns.barplot(x=daily_counts.index, y=daily_counts.values)
    plt.title('Walking Activity by Day of Week')
    plt.xticks(rotation=45)
    plt.ylabel('Number of Walks')
    plt.savefig(os.path.join(output_dir, 'daily_activity.png'))
    plt.close()

def analyze_walking_patterns(walks_gdf, output_dir='analysis_output'):
    """Main function to analyze walking patterns and generate visualizations."""
    os.makedirs(output_dir, exist_ok=True)
    
    print("Extracting temporal information...")
    time_df = extract_time_info(walks_gdf)
    
    print("\nAnalyzing temporal patterns...")
    temporal_patterns = analyze_temporal_patterns(time_df)
    
    print("\nAnalyzing route patterns...")
    route_patterns = analyze_route_patterns(walks_gdf)
    
    print("\nIdentifying common areas...")
    common_areas = identify_common_areas(walks_gdf)
    
    print("\nGenerating visualizations...")
    plot_temporal_patterns(time_df, output_dir)
    
    # Save summary statistics
    summary = {
        'total_walks': len(walks_gdf),
        'total_distance_km': route_patterns['total_distance'],
        'avg_walk_distance_km': route_patterns['avg_segment_length'],
        'avg_speed_kmh': route_patterns['avg_speed'],
        'avg_sinuosity': route_patterns['avg_sinuosity'],
        'most_active_hour': temporal_patterns['hourly_stats']['duration']['count'].idxmax(),
        'most_active_day': temporal_patterns['daily_stats']['duration']['count'].idxmax(),
        'weekend_vs_weekday_ratio': (
            temporal_patterns['weekend_vs_weekday']['duration']['sum'][True] /
            temporal_patterns['weekend_vs_weekday']['duration']['sum'][False]
        )
    }
    
    # Save summary to file
    with open(os.path.join(output_dir, 'walking_summary.txt'), 'w') as f:
        f.write("Walking Pattern Analysis Summary\n")
        f.write("===============================\n\n")
        for key, value in summary.items():
            f.write(f"{key.replace('_', ' ').title()}: {value:.2f}\n")
    
    return summary

if __name__ == "__main__":
    # Load the filtered walks
    walks_gdf = gpd.read_file("data/processed_walks.geojson")
    
    # Run analysis
    summary = analyze_walking_patterns(walks_gdf)
    
    # Print key findings
    print("\nKey Findings:")
    print(f"Total distance walked: {summary['total_distance_km']:.1f} km")
    print(f"Average walk distance: {summary['avg_walk_distance_km']:.1f} km")
    print(f"Average walking speed: {summary['avg_speed_kmh']:.1f} km/h")
    print(f"Most active hour: {summary['most_active_hour']:02d}:00")
    print(f"Most active day: {summary['most_active_day']}")
    print(f"Weekend to weekday activity ratio: {summary['weekend_vs_weekday_ratio']:.2f}") 
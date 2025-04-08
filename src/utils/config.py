"""
Configuration settings for different cities.
"""

CITY_PARAMS = {
    'london': {
        'buffer_distance': 8,  # meters
        'max_walking_speed': 2.5,  # m/s (about 9 km/h)
        'min_walking_speed': 0.2,  # m/s
        'max_sinuosity': 3.0,  # for longer trips
        'max_direct_distance': 8000,  # meters
        'bbox': [-0.351, 51.38, 0.148, 51.669],  # [min_lon, min_lat, max_lon, max_lat]
    },
    'blacksburg': {
        'buffer_distance': 10,  # meters
        'max_walking_speed': 2.8,  # m/s
        'min_walking_speed': 0.2,  # m/s
        'max_sinuosity': 3.5,  # for longer trips
        'max_direct_distance': 5000,  # meters
        'bbox': [-80.5, 37.18, -80.38, 37.25],  # [min_lon, min_lat, max_lon, max_lat]
    },
    'mumbai': {
        'buffer_distance': 6,  # meters
        'max_walking_speed': 2.2,  # m/s
        'min_walking_speed': 0.1,  # m/s
        'max_sinuosity': 3.2,  # for longer trips
        'max_direct_distance': 6000,  # meters
        'bbox': [72.77, 18.89, 72.99, 19.28],  # [min_lon, min_lat, max_lon, max_lat]
    }
}

# File paths
DATA_DIR = 'data'
RAW_WALK_DATA_DIR = f'{DATA_DIR}/raw_walk_data'
PROCESSED_DATA_DIR = f'{DATA_DIR}/processed'
CACHE_DIR = 'cache'
KEPLER_DATA_DIR = 'kepler_data'

# CRS settings
DEFAULT_CRS = 'EPSG:4326'  # WGS84
METRIC_CRS = 'EPSG:3857'   # Web Mercator

# Analysis settings
MIN_WALK_DURATION = 60  # seconds
MIN_WALK_DISTANCE = 100  # meters
GPS_ACCURACY = 10  # meters 
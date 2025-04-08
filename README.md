# Street Tracker

A tool for tracking and visualizing walking routes using Google Fit data.

## Overview

Street Tracker processes walking activity data from Google Fit (TCX files) and visualizes it on a map, showing which streets have been walked. It can:
- Process Google Fit TCX files
- Analyze walking patterns
- Filter out transit trips
- Generate street coverage maps
- Export data for visualization in Kepler.gl

## Features

- Process Google Fit TCX files
- Analyze walking patterns and filter transit trips
- Generate street coverage maps
- Support for multiple cities (London, Blacksburg, Mumbai)
- Export data for visualization in Kepler.gl
- City-specific parameters for accurate analysis

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/street-tracker.git
cd street-tracker
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Export your Google Fit data:
   - Go to Google Takeout
   - Select Google Fit data
   - Download and extract the archive

2. Place your Google Fit data in the `data/raw_walk_data` directory

3. Run the analysis:
```bash
python src/scripts/process_walks.py
python src/scripts/analyze_walks.py
python src/scripts/export_for_kepler.py
```

4. View the results in Kepler.gl:
   - Import the generated GeoJSON files
   - Configure the visualization as needed

## Project Structure

```
street-tracker/
├── src/
│   ├── data/           # Data processing modules
│   ├── scripts/        # Main scripts
│   └── utils/          # Utility functions
├── tests/              # Test files
├── docs/               # Documentation
├── data/               # Data files
│   ├── raw_walk_data/  # Raw Google Fit data
│   └── processed/      # Processed data files
└── requirements.txt    # Project dependencies
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
"""
Test script for the TCX processor.
"""

import sys
import os
from pathlib import Path
import geopandas as gpd
from src.data.tcx_processor import parse_tcx_file, process_tcx_files

def test_parse_tcx():
    """Test parsing a single TCX file."""
    # Create a test TCX file
    test_tcx = """<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities>
    <Activity Sport="Walking">
      <Id>2024-04-08T12:00:00Z</Id>
      <Lap StartTime="2024-04-08T12:00:00Z">
        <Track>
          <Trackpoint>
            <Time>2024-04-08T12:00:00Z</Time>
            <Position>
              <LatitudeDegrees>51.5074</LatitudeDegrees>
              <LongitudeDegrees>-0.1278</LongitudeDegrees>
            </Position>
          </Trackpoint>
          <Trackpoint>
            <Time>2024-04-08T12:01:00Z</Time>
            <Position>
              <LatitudeDegrees>51.5075</LatitudeDegrees>
              <LongitudeDegrees>-0.1279</LongitudeDegrees>
            </Position>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>"""
    
    # Save test file
    test_dir = Path("tests/data")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_dir / "test_walk.tcx"
    with open(test_file, "w") as f:
        f.write(test_tcx)
    
    # Test parsing
    result = parse_tcx_file(str(test_file))
    assert result is not None
    assert result['geometry'].type == 'LineString'
    assert len(result['geometry'].coords) == 2
    assert result['start_time'].isoformat().startswith('2024-04-08T12:00:00')
    assert result['end_time'].isoformat().startswith('2024-04-08T12:01:00')
    
    # Clean up
    test_file.unlink()
    print("TCX parsing test passed!")

def test_process_tcx_files():
    """Test processing multiple TCX files."""
    # Create test directory with multiple files
    test_dir = Path("tests/data")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create multiple test files
    for i in range(3):
        test_tcx = f"""<?xml version="1.0" encoding="UTF-8"?>
<TrainingCenterDatabase xmlns="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2">
  <Activities>
    <Activity Sport="Walking">
      <Id>2024-04-08T12:00:00Z</Id>
      <Lap StartTime="2024-04-08T12:00:00Z">
        <Track>
          <Trackpoint>
            <Time>2024-04-08T12:00:00Z</Time>
            <Position>
              <LatitudeDegrees>51.5074</LatitudeDegrees>
              <LongitudeDegrees>-0.1278</LongitudeDegrees>
            </Position>
          </Trackpoint>
          <Trackpoint>
            <Time>2024-04-08T12:01:00Z</Time>
            <Position>
              <LatitudeDegrees>51.5075</LatitudeDegrees>
              <LongitudeDegrees>-0.1279</LongitudeDegrees>
            </Position>
          </Trackpoint>
        </Track>
      </Lap>
    </Activity>
  </Activities>
</TrainingCenterDatabase>"""
        
        test_file = test_dir / f"test_walk_{i}.tcx"
        with open(test_file, "w") as f:
            f.write(test_tcx)
    
    # Test processing
    result = process_tcx_files(str(test_dir))
    assert isinstance(result, gpd.GeoDataFrame)
    assert len(result) == 3
    assert all(result['geometry'].type == 'LineString')
    
    # Clean up
    for file in test_dir.glob("*.tcx"):
        file.unlink()
    print("TCX processing test passed!")

if __name__ == '__main__':
    print("Running TCX processor tests...")
    test_parse_tcx()
    test_process_tcx_files()
    print("All tests passed!") 
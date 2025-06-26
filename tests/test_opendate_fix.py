import pytest
import pandas as pd
from datetime import datetime, timezone
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.time_utils import format_datetime_for_api

class TestOpenDateFix:
    
    def test_format_datetime_for_api_with_timezone_offset(self):
        """Test format_datetime_for_api with a timezone offset."""
        # Create a datetime with Eastern timezone offset (-04:00)
        # This simulates the timestamp from the lambda function: "2025-06-25T12:06:27.229172-04:00"
        dt = pd.Timestamp('2025-06-25T12:06:27.229172-04:00')
        
        # Format the datetime (should convert to UTC)
        result = format_datetime_for_api(dt)
        
        # Check the result (preserve original time, just change timezone designation to Z)
        assert result == "2025-06-25T12:06:27.229Z"
    
    def test_format_datetime_for_api_with_timezone_name(self):
        """Test format_datetime_for_api with a named timezone."""
        import pytz
        
        # Create a datetime with Eastern timezone
        eastern = pytz.timezone('US/Eastern')
        dt = eastern.localize(datetime(2025, 6, 25, 12, 6, 27, 229172))
        
        # Format the datetime (should convert to UTC)
        result = format_datetime_for_api(dt)
        
        # Check the result (preserve original time, just change timezone designation to Z)
        assert result == "2025-06-25T12:06:27.229Z"
    
    def test_format_datetime_for_api_series_with_timezone(self):
        """Test format_datetime_for_api with a pandas Series of datetime objects with timezone."""
        # Create a Series with datetime objects with timezone offset
        dates = [
            pd.Timestamp('2025-06-25T12:06:27.229172-04:00'),
            pd.Timestamp('2025-06-25T15:30:00.000000-04:00'),
            pd.Timestamp('2025-06-25T18:15:45.123000-04:00')
        ]
        series = pd.Series(dates)
        
        # Format the Series
        result = format_datetime_for_api(series)
        
        # Check the results (preserve original time, just change timezone designation to Z)
        assert result[0] == "2025-06-25T12:06:27.229Z"
        assert result[1] == "2025-06-25T15:30:00.000Z"
        assert result[2] == "2025-06-25T18:15:45.123Z"

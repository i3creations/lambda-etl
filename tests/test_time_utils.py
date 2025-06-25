import pytest
import pandas as pd
from datetime import datetime, timezone
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.time_utils import format_datetime_for_api

class TestTimeUtils:
    
    def test_format_datetime_for_api_single_datetime(self):
        """Test format_datetime_for_api with a single datetime object."""
        # Test with UTC timezone
        dt = datetime(2025, 6, 25, 14, 58, 17, 424000, tzinfo=timezone.utc)
        result = format_datetime_for_api(dt)
        assert result == "2025-06-25T14:58:17.424Z"
        
        # Test with no timezone (should assume UTC)
        dt = datetime(2025, 6, 25, 14, 58, 17, 424000)
        result = format_datetime_for_api(dt)
        assert result == "2025-06-25T14:58:17.424Z"
        
        # Test with zero milliseconds
        dt = datetime(2025, 6, 25, 14, 58, 17, 0, tzinfo=timezone.utc)
        result = format_datetime_for_api(dt)
        assert result == "2025-06-25T14:58:17.000Z"
    
    def test_format_datetime_for_api_series(self):
        """Test format_datetime_for_api with a pandas Series of datetime objects."""
        # Create a Series with datetime objects
        dates = [
            datetime(2025, 6, 25, 14, 58, 17, 424000, tzinfo=timezone.utc),
            datetime(2025, 6, 26, 10, 30, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 6, 27, 8, 15, 45, 123000, tzinfo=timezone.utc)
        ]
        series = pd.Series(dates)
        
        # Format the Series
        result = format_datetime_for_api(series)
        
        # Check the results
        assert result[0] == "2025-06-25T14:58:17.424Z"
        assert result[1] == "2025-06-26T10:30:00.000Z"
        assert result[2] == "2025-06-27T08:15:45.123Z"
    
    def test_format_datetime_for_api_with_timezone_conversion(self):
        """Test format_datetime_for_api with timezone conversion."""
        # Create a datetime with a non-UTC timezone
        import pytz
        eastern = pytz.timezone('US/Eastern')
        dt = eastern.localize(datetime(2025, 6, 25, 10, 58, 17, 424000))
        
        # Format the datetime (should convert to UTC)
        result = format_datetime_for_api(dt)
        
        # Check the result (10:58 Eastern should be 14:58 UTC)
        assert result == "2025-06-25T14:58:17.424Z"
    
    def test_format_datetime_for_api_with_pandas_timestamp(self):
        """Test format_datetime_for_api with pandas Timestamp objects."""
        # Create a Series with pandas Timestamp objects
        dates = [
            pd.Timestamp('2025-06-25 14:58:17.424000+0000'),
            pd.Timestamp('2025-06-26 10:30:00.000000+0000'),
            pd.Timestamp('2025-06-27 08:15:45.123000+0000')
        ]
        series = pd.Series(dates)
        
        # Format the Series
        result = format_datetime_for_api(series)
        
        # Check the results
        assert result[0] == "2025-06-25T14:58:17.424Z"
        assert result[1] == "2025-06-26T10:30:00.000Z"
        assert result[2] == "2025-06-27T08:15:45.123Z"
    
    def test_format_datetime_for_api_with_none_values(self):
        """Test format_datetime_for_api with None values in a Series."""
        # Create a Series with some None values
        dates = [
            datetime(2025, 6, 25, 14, 58, 17, 424000, tzinfo=timezone.utc),
            None,
            datetime(2025, 6, 27, 8, 15, 45, 123000, tzinfo=timezone.utc)
        ]
        series = pd.Series(dates)
        
        # Format the Series
        result = format_datetime_for_api(series)
        
        # Check the results
        assert result[0] == "2025-06-25T14:58:17.424Z"
        assert pd.isna(result[1])
        assert result[2] == "2025-06-27T08:15:45.123Z"

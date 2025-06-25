"""
Test Date Handling with Exceptions

This script tests the date handling functionality to ensure dates in the future
properly raise exceptions.
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.time_utils import format_datetime_for_api




def test_format_datetime_for_api():
    """Test the format_datetime_for_api function."""
    print("Testing format_datetime_for_api function...")
    
    # Get current time in Eastern timezone
    eastern_tz = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern_tz)
    
    # Test with a datetime in the past
    past_time = current_time - timedelta(days=1)
    result = format_datetime_for_api(past_time, "past_date")
    print(f"Past date: {past_time.isoformat()}")
    print(f"Formatted: {result}")
    
    # Test with a datetime in the future - should raise exception
    future_time = current_time + timedelta(days=1)
    print(f"Future date: {future_time.isoformat()}")
    try:
        result = format_datetime_for_api(future_time, "future_date")
        print("ERROR: Future date did not raise exception!")
    except ValueError as e:
        print(f"SUCCESS: Future date correctly raised exception: {str(e)}")
    
    # Test with a pandas Series containing a future date - should raise exception
    dates = pd.Series([
        past_time,
        current_time,
        future_time
    ])
    print(f"Series with future date:")
    try:
        result = format_datetime_for_api(dates, "date_series")
        print("ERROR: Series with future date did not raise exception!")
    except ValueError as e:
        print(f"SUCCESS: Series with future date correctly raised exception: {str(e)}")
    
    print("format_datetime_for_api test complete.\n")


if __name__ == "__main__":
    print("Running date handling tests with exceptions...\n")
    
    test_format_datetime_for_api()
    
    print("All tests complete.")

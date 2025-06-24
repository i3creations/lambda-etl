"""
Test Date Handling

This script tests the date handling functionality to ensure dates are properly
formatted and not sent in the future.
"""

import sys
import os
import pandas as pd
from datetime import datetime, timedelta
import pytz

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.time_utils import format_datetime_for_api, ensure_valid_datetime
from src.processing.preprocess import preprocess


def test_ensure_valid_datetime():
    """Test the ensure_valid_datetime function."""
    print("Testing ensure_valid_datetime function...")
    
    # Get current time in Eastern timezone
    eastern_tz = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern_tz)
    
    # Test with a datetime in the past
    past_time = current_time - timedelta(days=1)
    result = ensure_valid_datetime(past_time, "past_date")
    print(f"Past date: {past_time.isoformat()}")
    print(f"Result: {result.isoformat()}")
    print(f"Unchanged: {result == past_time}")
    
    # Test with a datetime in the future
    future_time = current_time + timedelta(days=1)
    print(f"Future date: {future_time.isoformat()}")
    try:
        result = ensure_valid_datetime(future_time, "future_date")
        print("ERROR: Future date did not raise exception!")
    except ValueError as e:
        print(f"SUCCESS: Future date correctly raised exception: {str(e)}")
    
    # Test with a pandas Series
    dates = pd.Series([
        past_time,
        current_time,
        future_time
    ])
    print(f"Series with future date:")
    try:
        result = ensure_valid_datetime(dates, "date_series")
        print("ERROR: Series with future date did not raise exception!")
    except ValueError as e:
        print(f"SUCCESS: Series with future date correctly raised exception: {str(e)}")
    
    print("ensure_valid_datetime test complete.\n")


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
    
    # Test with a datetime in the future
    future_time = current_time + timedelta(days=1)
    print(f"Future date: {future_time.isoformat()}")
    try:
        result = format_datetime_for_api(future_time, "future_date")
        print("ERROR: Future date did not raise exception!")
    except ValueError as e:
        print(f"SUCCESS: Future date correctly raised exception: {str(e)}")
    
    # Test with a pandas Series
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


def test_preprocess_with_future_dates():
    """Test the preprocess function with future dates."""
    print("Testing preprocess function with future dates...")
    
    # Get current time in Eastern timezone
    eastern_tz = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern_tz)
    
    # Create a sample record with a future date
    future_time = current_time + timedelta(days=1)
    
    # Create test data
    test_data = [{
        'Incident_ID': 123456,
        'SIR_': 'TEST-123456',
        'Local_Date_Reported': future_time,
        'Facility_Address_HELPER': '123 Test St, Test City, TS 12345',
        'Facility_Latitude': '38.8977',
        'Facility_Longitude': '-77.0365',
        'Date_SIR_Processed__NT': current_time,
        'Details': 'Test incident details',
        'Section_5__Action_Taken': 'Test action taken',
        'Type_of_SIR': 'Test Type',
        'Category_Type': 'Test Category',
        'Sub_Category_Type': 'Test Subcategory'
    }]
    
    # Create a minimal config that doesn't require category mapping files
    config = {
        'filter_rejected': False,
        'filter_unprocessed': False,
        'filter_by_incident_id': False
    }
    
    try:
        # Process the data - should raise an exception due to future date
        print(f"Attempting to process data with future date: {future_time.isoformat()}")
        try:
            result = preprocess(test_data, 0, config)
            print("ERROR: Processing data with future date did not raise exception!")
        except ValueError as e:
            print(f"SUCCESS: Processing data with future date correctly raised exception: {str(e)}")
    except Exception as e:
        print(f"Error in preprocess test: {str(e)}")
    
    print("preprocess test complete.\n")


if __name__ == "__main__":
    print("Running date handling tests...\n")
    
    test_ensure_valid_datetime()
    test_format_datetime_for_api()
    
    # Comment out this test if category mapping files are not available
    # test_preprocess_with_future_dates()
    
    print("All tests complete.")

#!/usr/bin/env python3
"""
Test script to verify that the timezone fix is working correctly.
This script simulates the lambda handler logging to check if timestamps are in Eastern timezone.
"""

import os
import sys
import logging
import pytz
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the lambda handler module to test the timezone configuration
from lambda_handler import logger, setup_eastern_timezone_logging

def test_timezone_logging():
    """Test that logging uses Eastern timezone."""
    print("Testing timezone logging configuration...")
    
    # Test the logger
    logger.info("This is a test log message to verify Eastern timezone")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Also test with standard Python logging
    standard_logger = logging.getLogger('test')
    standard_logger.setLevel(logging.INFO)
    
    # Add a console handler if it doesn't exist
    if not standard_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        standard_logger.addHandler(handler)
    
    standard_logger.info("Standard logger test message")
    
    # Print current time in different timezones for comparison
    utc_time = datetime.now(pytz.UTC)
    eastern_time = utc_time.astimezone(pytz.timezone('US/Eastern'))
    
    print(f"\nCurrent UTC time: {utc_time}")
    print(f"Current Eastern time: {eastern_time}")
    print(f"Expected log timestamp format: {eastern_time.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3] + eastern_time.strftime('%z')}")

if __name__ == "__main__":
    test_timezone_logging()

"""
Test script to verify the fix for the datetime import issue.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the ArcherAuth class
from src.archer.auth import ArcherAuth

def test_parse_datetime():
    """Test the _parse_datetime method of ArcherAuth."""
    print("Testing _parse_datetime method...")
    
    # Create an instance of ArcherAuth
    auth = ArcherAuth('test_instance', 'test_user', 'test_pass', 'https://test.com')
    
    # Test with various datetime formats
    test_cases = [
        ('2023-01-01T12:00:00Z', True),
        ('2023-01-01T12:00:00+00:00', True),
        ('2023-01-01T12:00:00-04:00', True),
        ('2023-01-01T12:00:00.1-04:00', True),  # Malformed microseconds
        ('2023-01-01 12:00:00', True),
        ('invalid_datetime', False),
        (None, False),
        (datetime.now(), True)
    ]
    
    for date_str, should_parse in test_cases:
        result = auth._parse_datetime(date_str)
        success = (result is not None) == should_parse
        status = "SUCCESS" if success else "FAILURE"
        print(f"{status}: _parse_datetime({repr(date_str)}) -> {result}")
    
    print("Test completed.")

if __name__ == "__main__":
    test_parse_datetime()

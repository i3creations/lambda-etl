import pytest
import pandas as pd
from datetime import datetime, timezone
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.time_utils import format_datetime_for_api

class TestSpecificOpenDateFix:
    
    def test_specific_opendate_case(self):
        """Test the specific case mentioned in the task."""
        # Create a datetime with Eastern timezone offset (-04:00)
        # This simulates the timestamp from the lambda function: "2025-06-25T12:06:27.229172-04:00"
        dt = pd.Timestamp('2025-06-25T12:06:27.229172-04:00')
        
        # Format the datetime
        result = format_datetime_for_api(dt, field_name="openDate")
        
        # Check the result - should preserve original time (12:06:27) and just change timezone to Z
        assert result == "2025-06-25T12:06:27.229Z"
        
        # This should NOT be converted to UTC (which would be 16:06:27)
        assert "16:06:27" not in result
        
        # This should NOT be converted to the incorrect time mentioned in the task (19:57:00)
        assert "19:57:00" not in result

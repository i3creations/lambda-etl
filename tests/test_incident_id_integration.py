#!/usr/bin/env python3
"""
Integration Test for Incident ID Fix

This module tests that the Incident_ID column is properly preserved in the lambda_handler function.
"""

import os
import sys
import unittest
import pandas as pd
import json
from unittest.mock import patch, MagicMock

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_handler import lambda_handler


class TestIncidentIDIntegration(unittest.TestCase):
    """
    Integration test case for the Incident ID fix.
    """
    
    @patch('lambda_handler.update_last_incident_id_in_ssm')
    @patch('lambda_handler.get_last_incident_id_from_ssm')
    @patch('lambda_handler.load_config_from_secrets')
    @patch('lambda_handler.update_last_run_time_in_ssm')
    @patch('lambda_handler.get_last_run_time_from_ssm')
    @patch('lambda_handler.get_current_time')
    def test_incident_id_preserved_in_lambda_handler(self, mock_current_time, mock_get_time, mock_update_time, mock_load_config, mock_get_id, mock_update_id):
        """
        Test that the Incident_ID column is properly preserved in the lambda_handler function.
        """
        # Set up mocks
        mock_current_time.return_value = "2025-06-18T14:55:00.000Z"
        mock_get_time.return_value = "2025-06-18T14:00:00.000Z"
        
        # Set up more mocks
        mock_load_config.return_value = {
            'archer': {
                'username': 'test',
                'password': 'test',
                'instance': 'test'
            },
            'ops_portal': {
                'auth_url': 'https://test.com/auth',
                'item_url': 'https://test.com/item',
                'client_id': 'test',
                'client_secret': 'test',
                'verify_ssl': False
            }
        }
        mock_get_id.return_value = 1000
        
        # Create test event with test data
        test_event = {
            "dry_run": True,  # Use dry run to avoid actually sending data
            "test_data": [
                {
                    "Incident_ID": 1001,
                    "SIR_": "SIR-1001",
                    "Local_Date_Reported": "2025-06-18T13:30:00Z",
                    "Facility_Address_HELPER": "123 Test St, Test City, TS 12345",
                    "Facility_Latitude": "38.8977",
                    "Facility_Longitude": "-77.0365",
                    "Date_SIR_Processed__NT": "2025-06-18T13:35:00Z",
                    "Details": "Test incident details",
                    "Section_5__Action_Taken": "Test action taken",
                    "Type_of_SIR": "Facilitated Apprehension and Law Enforcement",
                    "Category_Type": "Immigration",
                    "Sub_Category_Type": "Deportation Order"
                },
                {
                    "Incident_ID": 1002,
                    "SIR_": "SIR-1002",
                    "Local_Date_Reported": "2025-06-18T14:30:00Z",
                    "Facility_Address_HELPER": "456 Test Ave, Test City, TS 12345",
                    "Facility_Latitude": "38.8978",
                    "Facility_Longitude": "-77.0366",
                    "Date_SIR_Processed__NT": "2025-06-18T14:35:00Z",
                    "Details": "Another test incident details",
                    "Section_5__Action_Taken": "Another test action taken",
                    "Type_of_SIR": "Facilitated Apprehension and Law Enforcement",
                    "Category_Type": "Immigration",
                    "Sub_Category_Type": "Deportation Order"
                }
            ]
        }
        
        # Create a mock context
        mock_context = MagicMock()
        mock_context.function_name = "test_function"
        mock_context.memory_limit_in_mb = 128
        mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_function"
        mock_context.aws_request_id = "test_request_id"
        
        # Mock the category mapping file
        with patch('os.path.exists', return_value=True), \
             patch('pandas.read_csv', return_value=pd.DataFrame({
                "Type_of_SIR": ["Facilitated Apprehension and Law Enforcement", "Facilitated Apprehension and Law Enforcement"],
                "Category_Type": ["Immigration", "Immigration"],
                "Sub_Category_Type": ["Deportation Order", "Deportation Order"],
                "type": ["Law Enforcement", "Law Enforcement"],
                "subtype": ["Immigration Enforcement", "Immigration Enforcement"],
                "sharing": ["USG", "USG"],
                "category": ["Law Enforcement", "Law Enforcement"]
            })):
            
            # Call the lambda handler
            response = lambda_handler(test_event, mock_context)
            
            # Check that the response is successful
            self.assertEqual(response['statusCode'], 200, "Lambda handler did not return status code 200")
            
            # Check that update_last_incident_id_in_ssm was called with the correct ID
            mock_update_id.assert_called_once_with(1002)


if __name__ == '__main__':
    unittest.main()

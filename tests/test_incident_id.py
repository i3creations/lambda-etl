#!/usr/bin/env python3
"""
Test Incident ID

This module tests that the incident ID is being properly saved to SSM.
It performs the following steps:
1. Get the current incident ID from SSM
2. Invoke the Lambda function with test data
3. Get the updated incident ID from SSM
4. Verify that the incident ID was updated correctly
"""

import os
import json
import boto3
import unittest
import requests
from datetime import datetime

# Import from parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_handler import lambda_handler

def get_incident_id_from_ssm(endpoint_url=None):
    """
    Get the incident ID from SSM.
    
    Args:
        endpoint_url (str, optional): LocalStack endpoint URL. If None, uses http://localhost:4566.
        
    Returns:
        int: Incident ID from SSM
    """
    # Set default endpoint URL if not provided
    if endpoint_url is None:
        endpoint_url = "http://localhost:4566"
    
    print(f"Getting incident ID from SSM at {endpoint_url}")
    
    # Create an SSM client
    ssm = boto3.client(
        'ssm',
        endpoint_url=endpoint_url,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    try:
        # Get the incident ID parameter
        response = ssm.get_parameter(Name='/ops-api/last-incident-id')
        incident_id_str = response['Parameter']['Value']
        
        # Parse the incident ID
        incident_id = int(incident_id_str.strip())
        
        print(f"Current incident ID: {incident_id}")
        return incident_id
        
    except ssm.exceptions.ParameterNotFound:
        print("No incident ID parameter found in SSM")
        return 0
    except Exception as e:
        print(f"Error getting incident ID from SSM: {str(e)}")
        raise

def invoke_lambda_with_test_data(lambda_url=None, test_incident_id=None):
    """
    Invoke the Lambda function with test data.
    
    Args:
        lambda_url (str, optional): Lambda function URL. If None, uses http://localhost:9000.
        test_incident_id (int, optional): Test incident ID to use. If None, uses a random ID.
        
    Returns:
        dict: Lambda function response
    """
    # Set default Lambda URL if not provided
    if lambda_url is None:
        lambda_url = "http://localhost:9000/2015-03-31/functions/function/invocations"
    
    # Set default test incident ID if not provided
    if test_incident_id is None:
        # Use current timestamp as test incident ID
        test_incident_id = int(datetime.now().timestamp())
    
    print(f"Invoking Lambda function at {lambda_url} with test incident ID: {test_incident_id}")
    
    # Create test data with a mock Archer response containing the test incident ID
    test_data = {
        "dry_run": False,
        "test_data": [
            {
                "Incident_ID": test_incident_id,
                "SIR_": f"SIR-{test_incident_id}",
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
            }
        ]
    }
    
    # Convert test data to JSON
    test_data_json = json.dumps(test_data)
    
    try:
        # Invoke the Lambda function
        response = requests.post(lambda_url, data=test_data_json)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("Lambda function invoked successfully")
            return response.json()
        else:
            print(f"Error invoking Lambda function: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error invoking Lambda function: {str(e)}")
        raise

class TestIncidentID(unittest.TestCase):
    """
    Test case for incident ID saving to SSM.
    """
    
    def setUp(self):
        """
        Set up the test case.
        """
        # Set up environment variables for testing
        os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['AWS_ACCESS_KEY_ID'] = 'test'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
        
        # Get the current incident ID from SSM
        self.endpoint_url = os.environ['AWS_ENDPOINT_URL']
        self.lambda_url = "http://localhost:9000/2015-03-31/functions/function/invocations"
        
        # Get the current incident ID from SSM
        self.current_incident_id = get_incident_id_from_ssm(self.endpoint_url)
        
        # Use a test incident ID that is higher than the current one
        self.test_incident_id = self.current_incident_id + 100
    
    def test_incident_id_saving(self):
        """
        Test that the incident ID is being properly saved to SSM.
        """
        # Invoke the Lambda function with test data
        lambda_response = invoke_lambda_with_test_data(self.lambda_url, self.test_incident_id)
        
        # Check if the Lambda function was invoked successfully
        self.assertIsNotNone(lambda_response, "Lambda function invocation failed")
        
        # Get the updated incident ID from SSM
        updated_incident_id = get_incident_id_from_ssm(self.endpoint_url)
        
        # Verify that the incident ID was updated correctly
        self.assertEqual(updated_incident_id, self.test_incident_id, 
                         f"Incident ID was not updated correctly. Expected {self.test_incident_id}, got {updated_incident_id}")
    
    def test_direct_lambda_invocation(self):
        """
        Test direct invocation of the lambda_handler function.
        """
        # Create test data with a mock Archer response containing the test incident ID
        test_incident_id = self.current_incident_id + 200
        test_event = {
            "dry_run": False,
            "test_data": [
                {
                    "Incident_ID": test_incident_id,
                    "SIR_": f"SIR-{test_incident_id}",
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
                }
            ]
        }
        
        # Create a mock context object
        class MockContext:
            def __init__(self):
                self.function_name = "test_function"
                self.memory_limit_in_mb = 128
                self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test_function"
                self.aws_request_id = "test_request_id"
        
        # Invoke the Lambda handler directly
        try:
            response = lambda_handler(test_event, MockContext())
            
            # Check if the Lambda function was invoked successfully
            self.assertEqual(response['statusCode'], 200, "Lambda handler did not return status code 200")
            
            # Get the updated incident ID from SSM
            updated_incident_id = get_incident_id_from_ssm(self.endpoint_url)
            
            # Verify that the incident ID was updated correctly
            self.assertEqual(updated_incident_id, test_incident_id, 
                            f"Incident ID was not updated correctly. Expected {test_incident_id}, got {updated_incident_id}")
        except Exception as e:
            self.fail(f"Lambda handler raised an exception: {str(e)}")


if __name__ == '__main__':
    unittest.main()

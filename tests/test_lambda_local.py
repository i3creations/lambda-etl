#!/usr/bin/env python3
"""
Test Lambda Function Locally

This script tests the OPS API Lambda function locally by invoking it directly.
It simulates the AWS Lambda environment by providing an event and context object.

Usage:
    python test_lambda_local.py
"""

import json
import os
import datetime
from typing import Dict, Any

# Set environment variables for local testing
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Set environment variables for OPS API configuration
os.environ['OPSAPI_ARCHER_USERNAME'] = 'archer_test_username'
os.environ['OPSAPI_ARCHER_PASSWORD'] = 'archer_test_password'
os.environ['OPSAPI_ARCHER_INSTANCE'] = 'archer_test_instance'
os.environ['OPSAPI_OPS_PORTAL_AUTH_URL'] = 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token'
os.environ['OPSAPI_OPS_PORTAL_ITEM_URL'] = 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item'
os.environ['OPSAPI_OPS_PORTAL_CLIENT_ID'] = 'test_client_id'
os.environ['OPSAPI_OPS_PORTAL_CLIENT_SECRET'] = 'test_client_secret'
os.environ['OPSAPI_OPS_PORTAL_VERIFY_SSL'] = 'false'
os.environ['OPSAPI_TIME_LOG'] = datetime.datetime.now().isoformat()

# Import the handler after setting environment variables
from lambda_handler import handler


class MockLambdaContext:
    """
    Mock AWS Lambda context object.
    """
    
    def __init__(self):
        self.function_name = 'ops-api-lambda'
        self.function_version = '$LATEST'
        self.invoked_function_arn = 'arn:aws:lambda:us-east-1:000000000000:function:ops-api-lambda'
        self.memory_limit_in_mb = 512
        self.aws_request_id = '00000000-0000-0000-0000-000000000000'
        self.log_group_name = '/aws/lambda/ops-api-lambda'
        self.log_stream_name = '2025/04/22/[$LATEST]00000000000000000000000000000000'
        self.identity = None
        self.client_context = None
        self.remaining_time_in_millis = 300000  # 5 minutes
    
    def get_remaining_time_in_millis(self):
        """
        Get the remaining time in milliseconds.
        
        Returns:
            int: Remaining time in milliseconds
        """
        return self.remaining_time_in_millis


def create_event(dry_run=False) -> Dict[str, Any]:
    """
    Create a mock AWS Lambda event.
    
    Args:
        dry_run (bool, optional): Whether to run in dry-run mode. Defaults to False.
        
    Returns:
        Dict[str, Any]: Mock event
    """
    return {
        'dry_run': dry_run,
        'time': datetime.datetime.now().isoformat()
    }


def main():
    """
    Main function to test the Lambda function locally.
    """
    print("Testing OPS API Lambda function locally...")
    
    # Create a mock event and context
    event = create_event(dry_run=True)  # Use dry_run=True to avoid sending data to OPS Portal
    context = MockLambdaContext()
    
    print(f"Event: {json.dumps(event, indent=2)}")
    print("Using environment variables for configuration:")
    for key, value in os.environ.items():
        if key.startswith('OPSAPI_'):
            if 'PASSWORD' in key or 'SECRET' in key:
                print(f"  {key}: ******")
            else:
                print(f"  {key}: {value}")
    
    # Invoke the Lambda function
    try:
        response = handler(event, context)
        print(f"Response: {json.dumps(response, indent=2)}")
        print("Lambda function executed successfully!")
    except Exception as e:
        print(f"Error executing Lambda function: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

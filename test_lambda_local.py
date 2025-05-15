#!/usr/bin/env python3
"""
Test Lambda Function Locally

This script tests the OPS API Lambda function locally by invoking it directly.
It simulates the AWS Lambda environment by providing an event and context object.

Usage:
    python test_lambda_local.py
"""

import json
import datetime
from typing import Dict, Any

from ops_api.lambda_handler import handler


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

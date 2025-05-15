#!/usr/bin/env python3
"""
Test Lambda Function in LocalStack

This script tests the OPS API Lambda function deployed in the LocalStack environment
by invoking it using the AWS SDK.

Usage:
    python test_lambda_localstack.py
"""

import json
import boto3
import datetime
from typing import Dict, Any


# LocalStack endpoint URL
ENDPOINT_URL = 'http://localhost:4566'

# AWS region
REGION = 'us-east-1'

# Lambda function name
LAMBDA_FUNCTION_NAME = 'ops-api-lambda'


def create_event(dry_run=False) -> Dict[str, Any]:
    """
    Create an event for the Lambda function.
    
    Args:
        dry_run (bool, optional): Whether to run in dry-run mode. Defaults to False.
        
    Returns:
        Dict[str, Any]: Event
    """
    return {
        'dry_run': dry_run,
        'time': datetime.datetime.now().isoformat()
    }


def invoke_lambda(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke the Lambda function in LocalStack.
    
    Args:
        event (Dict[str, Any]): Event to pass to the Lambda function
        
    Returns:
        Dict[str, Any]: Lambda function response
    """
    lambda_client = boto3.client('lambda', endpoint_url=ENDPOINT_URL, region_name=REGION,
                               aws_access_key_id='test', aws_secret_access_key='test')
    
    response = lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType='RequestResponse',
        Payload=json.dumps(event)
    )
    
    payload = response['Payload'].read().decode('utf-8')
    return json.loads(payload)


def main():
    """
    Main function to test the Lambda function in LocalStack.
    """
    print("Testing OPS API Lambda function in LocalStack...")
    
    # Create an event
    event = create_event(dry_run=True)  # Use dry_run=True to avoid sending data to OPS Portal
    print(f"Event: {json.dumps(event, indent=2)}")
    
    # Invoke the Lambda function
    try:
        response = invoke_lambda(event)
        print(f"Response: {json.dumps(response, indent=2)}")
        print("Lambda function executed successfully!")
    except Exception as e:
        print(f"Error invoking Lambda function: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

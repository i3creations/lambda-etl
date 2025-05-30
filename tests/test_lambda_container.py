#!/usr/bin/env python3
"""
Test Lambda Function in Docker Container

This script tests the OPS API Lambda function in the Docker container by invoking it using the AWS Lambda Runtime API.
It simulates the AWS Lambda environment by providing an event and context object.

Usage:
    python test_lambda_container.py
"""

import json
import os
import sys
import time
import datetime
import requests
from typing import Dict, Any, Optional


def check_container_running() -> bool:
    """
    Check if the Lambda container is running.
    
    Returns:
        bool: True if the container is running, False otherwise
    """
    try:
        response = requests.get("http://localhost:9000/2015-03-31/functions/function/invocations", timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        return False


def create_event(dry_run=True) -> Dict[str, Any]:
    """
    Create a mock AWS Lambda event.
    
    Args:
        dry_run (bool, optional): Whether to run in dry-run mode. Defaults to True.
        
    Returns:
        Dict[str, Any]: Mock event
    """
    return {
        'dry_run': dry_run,
        'time': datetime.datetime.now().isoformat()
    }


def invoke_lambda(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Invoke the Lambda function in the Docker container.
    
    Args:
        event (Dict[str, Any]): The event to send to the Lambda function
        
    Returns:
        Optional[Dict[str, Any]]: The response from the Lambda function, or None if there was an error
    """
    try:
        response = requests.post(
            "http://localhost:9000/2015-03-31/functions/function/invocations",
            data=json.dumps(event),
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                print(f"Error decoding JSON response: {response.text}")
                return None
        else:
            print(f"Error invoking Lambda function: {response.status_code} {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Lambda container: {str(e)}")
        return None


def main():
    """
    Main function to test the Lambda function in the Docker container.
    """
    print("Testing OPS API Lambda function in Docker container...")
    
    # Check if the container is running
    if not check_container_running():
        print("Lambda container is not running. Please start it with:")
        print("docker-compose up -d")
        return 1
    
    # Create a mock event
    event = create_event(dry_run=True)  # Use dry_run=True to avoid sending data to OPS Portal
    
    print(f"Event: {json.dumps(event, indent=2)}")
    
    # Invoke the Lambda function
    print("Invoking Lambda function...")
    response = invoke_lambda(event)
    
    if response:
        print(f"Response: {json.dumps(response, indent=2)}")
        print("Lambda function executed successfully!")
        return 0
    else:
        print("Failed to execute Lambda function.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

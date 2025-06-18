#!/usr/bin/env python3
"""
Setup Secrets for LocalStack

This script sets up the secrets in LocalStack for local development and testing.
It creates the necessary secrets in AWS Secrets Manager in the LocalStack environment.
"""

import os
import json
import boto3
import argparse
from datetime import datetime

def setup_secrets(endpoint_url=None):
    """
    Set up secrets in LocalStack.
    
    Args:
        endpoint_url (str, optional): LocalStack endpoint URL. If None, uses http://localhost:4566.
    """
    # Set default endpoint URL if not provided
    if endpoint_url is None:
        endpoint_url = "http://localhost:4566"
    
    print(f"Setting up secrets in LocalStack at {endpoint_url}")
    
    # Create a Secrets Manager client
    secretsmanager = boto3.client(
        'secretsmanager',
        endpoint_url=endpoint_url,
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )
    
    # Create the development secret
    secret_name = 'opts-dev-secret'
    
    # Define the secret data
    secret_data = {
        'OPSAPI_ARCHER_USERNAME': 'test_username',
        'OPSAPI_ARCHER_PASSWORD': 'test_password',
        'OPSAPI_ARCHER_INSTANCE': 'Test',
        'OPSAPI_ARCHER_URL': 'https://optstest.uscis.dhs.gov/',
        'OPSAPI_ARCHER_VERIFY_SSL': 'false',
        
        'OPSAPI_OPS_PORTAL_AUTH_URL': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token',
        'OPSAPI_OPS_PORTAL_ITEM_URL': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item',
        'OPSAPI_OPS_PORTAL_CLIENT_ID': 'test_client_id',
        'OPSAPI_OPS_PORTAL_CLIENT_SECRET': 'test_client_secret',
        'OPSAPI_OPS_PORTAL_VERIFY_SSL': 'false',
        
        'OPSAPI_LOGGING_LEVEL': 'DEBUG'
    }
    
    # Convert the secret data to a JSON string
    secret_string = json.dumps(secret_data)
    
    try:
        # Check if the secret already exists
        try:
            secretsmanager.describe_secret(SecretId=secret_name)
            print(f"Secret {secret_name} already exists, updating it")
            
            # Update the secret
            secretsmanager.update_secret(
                SecretId=secret_name,
                SecretString=secret_string
            )
        except secretsmanager.exceptions.ResourceNotFoundException:
            print(f"Secret {secret_name} does not exist, creating it")
            
            # Create the secret
            secretsmanager.create_secret(
                Name=secret_name,
                SecretString=secret_string,
                Description=f'Development secret for OPS API (created {datetime.now().isoformat()})'
            )
        
        print(f"Secret {secret_name} created/updated successfully")
        
    except Exception as e:
        print(f"Error creating/updating secret {secret_name}: {str(e)}")
        raise

def main():
    """
    Main function.
    """
    parser = argparse.ArgumentParser(description='Set up secrets in LocalStack')
    parser.add_argument('--endpoint-url', help='LocalStack endpoint URL')
    args = parser.parse_args()
    
    setup_secrets(args.endpoint_url)
    
    print("Secrets setup complete!")

if __name__ == '__main__':
    main()

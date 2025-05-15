#!/usr/bin/env python3
"""
LocalStack Setup Script

This script sets up the LocalStack environment for local development and testing
of the OPS API Lambda function. It creates the necessary AWS resources in the
LocalStack environment, including:

1. S3 bucket for storing time logs
2. SSM parameters for configuration
3. Lambda function
4. CloudWatch Events rule for scheduled execution

Usage:
    python setup_localstack.py
"""

import os
import json
import time
import zipfile
import tempfile
import subprocess
from pathlib import Path

import boto3


# LocalStack endpoint URL
ENDPOINT_URL = 'http://localhost:4566'

# AWS region
REGION = 'us-east-1'

# S3 bucket for time logs
TIME_LOG_BUCKET = 'ops-api-time-logs'
TIME_LOG_KEY = 'time_log.txt'

# Lambda function name
LAMBDA_FUNCTION_NAME = 'ops-api-lambda'

# CloudWatch Events rule name
EVENT_RULE_NAME = 'ops-api-schedule'

# SSM parameter names
SSM_PARAMETERS = {
    '/ops-api/archer/username': 'your_username',
    '/ops-api/archer/password': 'your_password',
    '/ops-api/archer/instance': 'your_instance',
    '/ops-api/ops-portal/auth-url': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token',
    '/ops-api/ops-portal/item-url': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item',
    '/ops-api/ops-portal/client-id': 'your_client_id',
    '/ops-api/ops-portal/client-secret': 'your_client_secret',
    '/ops-api/ops-portal/verify-ssl': 'false'
}


def create_zip_package():
    """
    Create a ZIP package of the OPS API code for Lambda deployment.
    
    Returns:
        str: Path to the ZIP file
    """
    print("Creating ZIP package for Lambda deployment...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the ZIP file
        zip_path = os.path.join(temp_dir, 'ops_api_lambda.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add the ops_api package
            for root, _, files in os.walk('ops_api'):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = file_path
                        zipf.write(file_path, arcname)
            
            # Add the config directory
            for root, _, files in os.walk('config'):
                for file in files:
                    if file.endswith('.csv') or file.endswith('.ini'):
                        file_path = os.path.join(root, file)
                        arcname = file_path
                        zipf.write(file_path, arcname)
        
        # Return the path to the ZIP file
        return zip_path


def wait_for_localstack():
    """
    Wait for LocalStack to be ready.
    """
    print("Waiting for LocalStack to be ready...")
    
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            # Try to list S3 buckets to check if LocalStack is ready
            s3 = boto3.client('s3', endpoint_url=ENDPOINT_URL, region_name=REGION,
                             aws_access_key_id='test', aws_secret_access_key='test')
            s3.list_buckets()
            print("LocalStack is ready!")
            return
        except Exception as e:
            print(f"LocalStack not ready yet (attempt {i+1}/{max_retries}): {str(e)}")
            time.sleep(retry_interval)
    
    raise Exception("LocalStack failed to start within the expected time")


def create_s3_bucket():
    """
    Create an S3 bucket for storing time logs.
    """
    print(f"Creating S3 bucket: {TIME_LOG_BUCKET}")
    
    s3 = boto3.client('s3', endpoint_url=ENDPOINT_URL, region_name=REGION,
                     aws_access_key_id='test', aws_secret_access_key='test')
    
    try:
        s3.create_bucket(Bucket=TIME_LOG_BUCKET)
        print(f"S3 bucket created: {TIME_LOG_BUCKET}")
    except s3.exceptions.BucketAlreadyExists:
        print(f"S3 bucket already exists: {TIME_LOG_BUCKET}")
    except Exception as e:
        print(f"Error creating S3 bucket: {str(e)}")
        raise


def create_ssm_parameters():
    """
    Create SSM parameters for configuration.
    """
    print("Creating SSM parameters...")
    
    ssm = boto3.client('ssm', endpoint_url=ENDPOINT_URL, region_name=REGION,
                      aws_access_key_id='test', aws_secret_access_key='test')
    
    for name, value in SSM_PARAMETERS.items():
        try:
            ssm.put_parameter(
                Name=name,
                Value=value,
                Type='SecureString' if 'password' in name or 'secret' in name else 'String',
                Overwrite=True
            )
            print(f"SSM parameter created: {name}")
        except Exception as e:
            print(f"Error creating SSM parameter {name}: {str(e)}")
            raise


def create_lambda_function(zip_path):
    """
    Create the Lambda function.
    
    Args:
        zip_path (str): Path to the ZIP package
    """
    print(f"Creating Lambda function: {LAMBDA_FUNCTION_NAME}")
    
    lambda_client = boto3.client('lambda', endpoint_url=ENDPOINT_URL, region_name=REGION,
                               aws_access_key_id='test', aws_secret_access_key='test')
    
    with open(zip_path, 'rb') as zip_file:
        zip_bytes = zip_file.read()
    
    try:
        # Check if the function already exists
        try:
            lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
            # Function exists, update it
            lambda_client.update_function_code(
                FunctionName=LAMBDA_FUNCTION_NAME,
                ZipFile=zip_bytes
            )
            print(f"Lambda function updated: {LAMBDA_FUNCTION_NAME}")
        except lambda_client.exceptions.ResourceNotFoundException:
            # Function doesn't exist, create it
            lambda_client.create_function(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Runtime='python3.9',
                Role='arn:aws:iam::000000000000:role/lambda-role',  # Dummy role for LocalStack
                Handler='ops_api.lambda_handler.handler',
                Code={'ZipFile': zip_bytes},
                Timeout=300,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'TIME_LOG_BUCKET': TIME_LOG_BUCKET,
                        'TIME_LOG_KEY': TIME_LOG_KEY
                    }
                }
            )
            print(f"Lambda function created: {LAMBDA_FUNCTION_NAME}")
    except Exception as e:
        print(f"Error creating Lambda function: {str(e)}")
        raise


def create_cloudwatch_event_rule():
    """
    Create a CloudWatch Events rule for scheduled execution of the Lambda function.
    """
    print(f"Creating CloudWatch Events rule: {EVENT_RULE_NAME}")
    
    events = boto3.client('events', endpoint_url=ENDPOINT_URL, region_name=REGION,
                        aws_access_key_id='test', aws_secret_access_key='test')
    
    lambda_client = boto3.client('lambda', endpoint_url=ENDPOINT_URL, region_name=REGION,
                               aws_access_key_id='test', aws_secret_access_key='test')
    
    try:
        # Create the rule
        events.put_rule(
            Name=EVENT_RULE_NAME,
            ScheduleExpression='rate(1 day)',  # Run once a day
            State='ENABLED'
        )
        print(f"CloudWatch Events rule created: {EVENT_RULE_NAME}")
        
        # Add the Lambda function as a target
        events.put_targets(
            Rule=EVENT_RULE_NAME,
            Targets=[
                {
                    'Id': '1',
                    'Arn': f'arn:aws:lambda:{REGION}:000000000000:function:{LAMBDA_FUNCTION_NAME}'
                }
            ]
        )
        print(f"Added Lambda function as target for CloudWatch Events rule: {EVENT_RULE_NAME}")
        
        # Add permission for CloudWatch Events to invoke the Lambda function
        try:
            lambda_client.add_permission(
                FunctionName=LAMBDA_FUNCTION_NAME,
                StatementId=f'{EVENT_RULE_NAME}-Permission',
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=f'arn:aws:events:{REGION}:000000000000:rule/{EVENT_RULE_NAME}'
            )
            print(f"Added permission for CloudWatch Events to invoke Lambda function: {LAMBDA_FUNCTION_NAME}")
        except lambda_client.exceptions.ResourceConflictException:
            print(f"Permission already exists for CloudWatch Events to invoke Lambda function: {LAMBDA_FUNCTION_NAME}")
    except Exception as e:
        print(f"Error creating CloudWatch Events rule: {str(e)}")
        raise


def main():
    """
    Main function to set up the LocalStack environment.
    """
    print("Setting up LocalStack environment for OPS API Lambda function...")
    
    # Check if LocalStack is running
    try:
        # Wait for LocalStack to be ready
        wait_for_localstack()
        
        # Create the S3 bucket
        create_s3_bucket()
        
        # Create SSM parameters
        create_ssm_parameters()
        
        # Create the Lambda function
        zip_path = create_zip_package()
        create_lambda_function(zip_path)
        
        # Create the CloudWatch Events rule
        create_cloudwatch_event_rule()
        
        print("LocalStack environment setup complete!")
        print("\nYou can now test the Lambda function with:")
        print(f"aws --endpoint-url={ENDPOINT_URL} lambda invoke --function-name {LAMBDA_FUNCTION_NAME} --payload '{{}}' response.json")
        
    except Exception as e:
        print(f"Error setting up LocalStack environment: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

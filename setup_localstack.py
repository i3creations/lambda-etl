#!/usr/bin/env python3
"""
LocalStack Setup Script

This script sets up the LocalStack environment for local development and testing
of the OPS API Lambda function. It creates the necessary AWS resources in the
LocalStack environment, including:

1. SSM parameters for configuration (including time log)
2. Lambda function
3. CloudWatch Events rule for scheduled execution

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

# Lambda function name
LAMBDA_FUNCTION_NAME = 'ops-api-lambda'

# CloudWatch Events rule name
EVENT_RULE_NAME = 'ops-api-schedule'

# Import datetime for time log initialization
from datetime import datetime

# SSM parameter names
SSM_PARAMETERS = {
    '/ops-api/archer/username': 'your_username',
    '/ops-api/archer/password': 'your_password',
    '/ops-api/archer/instance': 'your_instance',
    '/ops-api/ops-portal/auth-url': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token',
    '/ops-api/ops-portal/item-url': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item',
    '/ops-api/ops-portal/client-id': 'your_client_id',
    '/ops-api/ops-portal/client-secret': 'your_client_secret',
    '/ops-api/ops-portal/verify-ssl': 'false',
    '/ops-api/time-log': datetime.now().isoformat()  # Initialize with current time
}


def ensure_build_directory():
    """
    Ensure the build directory exists.
    
    Returns:
        str: Path to the build directory
    """
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    os.makedirs(build_dir, exist_ok=True)
    return build_dir

def create_zip_package():
    """
    Create a ZIP package of the OPS API code for Lambda deployment.
    The package will only include the core business logic, as dependencies
    will be provided by Lambda layers.
    
    Returns:
        str: Path to the ZIP file
    """
    print("Creating ZIP package for Lambda deployment...")
    
    # Ensure build directory exists
    build_dir = ensure_build_directory()
    
    # Create a temporary directory for the package
    temp_dir = os.path.join(build_dir, 'lambda_package')
    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Copy only the ops_api package to the temporary directory
    # (excluding Archer_API which will be in a layer)
    print("Copying ops_api package (excluding Archer_API)...")
    import shutil
    
    # Create ops_api directory structure
    os.makedirs(os.path.join(temp_dir, 'ops_api'))
    
    # Copy Python files from ops_api directory
    for item in os.listdir('ops_api'):
        if item == 'Archer_API':
            # Skip Archer_API as it will be in a layer
            continue
        
        src_path = os.path.join('ops_api', item)
        dst_path = os.path.join(temp_dir, 'ops_api', item)
        
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        elif item.endswith('.py') or item == '__init__.py':
            shutil.copy2(src_path, dst_path)
    
    # Copy the config directory to the temporary directory
    print("Copying config files...")
    shutil.copytree('config', os.path.join(temp_dir, 'config'))
    
    # Create an empty __init__.py file in the root directory
    with open(os.path.join(temp_dir, '__init__.py'), 'w') as f:
        pass
    
    print("Dependencies will be provided by Lambda layers...")
    
    # Create the ZIP file
    zip_path = os.path.join(build_dir, 'ops_api_lambda.zip')
    
    # Create the ZIP file from the temporary directory
    print("Creating ZIP file...")
    current_dir = os.getcwd()
    os.chdir(temp_dir)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Skip __pycache__ directories and other unnecessary files
            dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]
            
            for file in files:
                # Skip unnecessary files
                if file.endswith('.pyc') or file.endswith('.pyo') or file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                arcname = file_path
                zipf.write(file_path, arcname)
    
    # Return to the original directory
    os.chdir(current_dir)
    
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)
    
    print(f"ZIP package created: {zip_path}")
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
            # Check LocalStack health endpoint directly
            import requests
            response = requests.get("http://localhost:4566/_localstack/health")
            if response.status_code == 200:
                health_data = response.json()
                services = health_data.get('services', {})
                
                # Check if required services are running or available
                required_services = ['lambda', 'ssm', 's3']
                services_ready = True
                not_ready = []
                
                for service in required_services:
                    status = services.get(service)
                    if status not in ['running', 'available']:
                        services_ready = False
                        not_ready.append(service)
                
                if services_ready:
                    print("LocalStack is ready!")
                    print("LocalStack health status:")
                    print(json.dumps(health_data, indent=2))
                    return
                else:
                    print(f"Waiting for services to be ready: {', '.join(not_ready)}")
                    print(f"Current service states: " + 
                          ", ".join([f"{s}: {services.get(s)}" for s in required_services]))
        except Exception as e:
            print(f"Error checking LocalStack health: {str(e)}")
        
        print(f"LocalStack not ready yet (attempt {i+1}/{max_retries})")
        time.sleep(retry_interval)
    
    raise Exception("LocalStack failed to start within the expected time")



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
    
    # Create S3 client
    s3 = boto3.client('s3', endpoint_url=ENDPOINT_URL, region_name=REGION,
                    aws_access_key_id='test', aws_secret_access_key='test')
    
    # Create Lambda client
    lambda_client = boto3.client('lambda', endpoint_url=ENDPOINT_URL, region_name=REGION,
                               aws_access_key_id='test', aws_secret_access_key='test')
    
    # Create S3 bucket if it doesn't exist
    bucket_name = 'lambda-code-bucket'
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"S3 bucket exists: {bucket_name}")
    except:
        print(f"Creating S3 bucket: {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)
    
    # Upload ZIP file to S3
    key = f'{LAMBDA_FUNCTION_NAME}.zip'
    print(f"Uploading ZIP file to S3: s3://{bucket_name}/{key}")
    s3.upload_file(zip_path, bucket_name, key)
    
    try:
        # Check if the function already exists
        try:
            lambda_client.get_function(FunctionName=LAMBDA_FUNCTION_NAME)
            # Function exists, update it
            print(f"Updating existing Lambda function: {LAMBDA_FUNCTION_NAME}")
            lambda_client.update_function_code(
                FunctionName=LAMBDA_FUNCTION_NAME,
                S3Bucket=bucket_name,
                S3Key=key
            )
            print(f"Lambda function updated: {LAMBDA_FUNCTION_NAME}")
        except lambda_client.exceptions.ResourceNotFoundException:
            # Function doesn't exist, create it
            print(f"Creating new Lambda function: {LAMBDA_FUNCTION_NAME}")
            
            # Read the ZIP file content
            with open(zip_path, 'rb') as zip_file:
                zip_bytes = zip_file.read()
            
            # Create the function using S3 reference instead of direct ZIP file content
            lambda_client.create_function(
                FunctionName=LAMBDA_FUNCTION_NAME,
                Runtime='python3.9',
                Role='arn:aws:iam::000000000000:role/lambda-role',
                Handler='ops_api.lambda_handler.handler',
                Code={'S3Bucket': bucket_name, 'S3Key': key},  # Use S3 reference instead of direct ZIP
                Timeout=300,
                MemorySize=512
            )
            print(f"Lambda function created: {LAMBDA_FUNCTION_NAME}")
    except Exception as e:
        print(f"Error creating/updating Lambda function: {str(e)}")
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

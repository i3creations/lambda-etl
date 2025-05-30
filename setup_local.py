#!/usr/bin/env python3
"""
AWS Lambda Local Setup Script

This script sets up the AWS Lambda local environment for development and testing
of the OPS API Lambda function. It creates a Docker container with the Lambda function
and sets up the necessary environment variables.

Usage:
    python setup_lambda_local.py
"""

import os
import json
import time
import zipfile
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

# Import datetime for time log initialization
from datetime import datetime

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
    print("Copying ops_api package...")
    import shutil
    
    # Create ops_api directory structure
    os.makedirs(os.path.join(temp_dir, 'ops_api'))
    
    # Copy Python files from ops_api directory
    for item in os.listdir('ops_api'):
        src_path = os.path.join('ops_api', item)
        dst_path = os.path.join(temp_dir, 'ops_api', item)
        
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        elif item.endswith('.py') or item == '__init__.py':
            shutil.copy2(src_path, dst_path)
    
    # Install the Archer API package directly into the package
    print("Installing Archer API package...")
    archer_api_path = os.path.join('ops_api', 'Archer_API')
    subprocess.check_call([
        'pip', 'install',
        '--target', os.path.join(temp_dir),
        '--upgrade',
        archer_api_path
    ])
    
    # Install dependencies directly in the package
    print("Installing dependencies...")
    subprocess.check_call([
        'pip', 'install',
        '--target', os.path.join(temp_dir),
        '--upgrade',
        '--no-deps',
        'aws-lambda-powertools', 'python-dotenv', 'pandas', 'numpy', 'pytz', 'python-dateutil', 'six', 'typing-extensions', 'jmespath'
    ])
    
    # Copy the config directory to the temporary directory
    print("Copying config files...")
    shutil.copytree('config', os.path.join(temp_dir, 'config'))
    
    # Create an empty __init__.py file in the root directory
    with open(os.path.join(temp_dir, '__init__.py'), 'w') as f:
        pass
    
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


def start_lambda_container():
    """
    Start the AWS Lambda container using Docker Compose.
    """
    print("Starting AWS Lambda container...")
    
    # Check if Docker is running
    try:
        subprocess.check_call(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("Docker is not running. Please start Docker and try again.")
        return False
    
    # Stop any existing containers
    subprocess.call(['docker-compose', 'down'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Start the container
    subprocess.check_call(['docker-compose', 'up', '-d'])
    
    # Wait for the container to be ready
    print("Waiting for the Lambda container to be ready...")
    time.sleep(5)
    
    print("AWS Lambda container started.")
    return True


def main():
    """
    Main function to set up the AWS Lambda local environment.
    """
    print("Setting up AWS Lambda local environment for OPS API Lambda function...")
    
    try:
        # Create the Lambda function package
        zip_path = create_zip_package()
        
        # Start the Lambda container
        if not start_lambda_container():
            print("Failed to start the Lambda container.")
            return 1
        
        print("AWS Lambda local environment setup complete!")
        print("\nYou can now test the Lambda function with:")
        print("curl -XPOST \"http://localhost:9000/2015-03-31/functions/function/invocations\" -d '{\"dry_run\": true}'")
        
    except Exception as e:
        print(f"Error setting up AWS Lambda local environment: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

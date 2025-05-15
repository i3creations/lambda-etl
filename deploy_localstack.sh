#!/bin/bash
# Deploy to LocalStack
# This script deploys the OPS API Lambda function to the LocalStack environment.
# It handles the entire deployment process, including:
# 1. Building the package
# 2. Starting LocalStack
# 3. Setting up the LocalStack environment
# 4. Testing the Lambda function

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print a message with a colored prefix
function log() {
    local prefix=$1
    local message=$2
    local color=$3
    echo -e "${color}[${prefix}]${NC} ${message}"
}

function info() {
    log "INFO" "$1" "${GREEN}"
}

function warn() {
    log "WARN" "$1" "${YELLOW}"
}

function error() {
    log "ERROR" "$1" "${RED}"
}

# Check if Docker is running
function check_docker() {
    info "Checking if Docker is running..."
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    info "Docker is running."
}

# Install dependencies
function install_dependencies() {
    info "Installing dependencies..."
    
    # Install dependencies using the found Python executable
    python -m pip install -r requirements.txt
    info "Dependencies installed."
}

# Build the package
function build_package() {
    info "Building the package..."
    
    # Build package using the found Python executable
    python -m pip install -e .
    info "Package built."
}

# Start LocalStack
function start_localstack() {
    info "Starting LocalStack..."
    
    # Check if LocalStack is already running
    if docker ps | grep -q "ops-api-localstack"; then
        info "LocalStack is already running."
    else
        # Start LocalStack using docker-compose
        docker compose up -d
        info "LocalStack started."
    fi
    
    # Set dummy AWS credentials for LocalStack
    export AWS_ACCESS_KEY_ID="test"
    export AWS_SECRET_ACCESS_KEY="test"
    export AWS_DEFAULT_REGION="us-east-1"
}

# Set up the LocalStack environment
function setup_localstack() {
    info "Setting up the LocalStack environment..."
    ./setup_localstack.sh
    info "LocalStack environment set up."
}

# Test the Lambda function locally
function test_lambda_local() {
    info "Testing the Lambda function locally..."
    
    # Run test using the found Python executable
    python test_lambda_local.py
    info "Local Lambda function test completed."
}

# Test the Lambda function in LocalStack
function test_lambda_localstack() {
    info "Testing the Lambda function in LocalStack..."
    
    # Run test using the found Python executable
    python test_lambda_localstack.py
    info "LocalStack Lambda function test completed."
}

# Main function
function main() {
    info "Starting deployment to LocalStack..."
    
    # Check if Docker is running
    check_docker
    
    # Install dependencies
    install_dependencies
    
    # Build the package
    build_package
    
    # Start LocalStack
    start_localstack
    
    # Set up the LocalStack environment
    setup_localstack
    
    # Test the Lambda function locally
    test_lambda_local
    
    # Test the Lambda function in LocalStack
    test_lambda_localstack
    
    info "Deployment to LocalStack completed successfully!"
    info "You can now use the Lambda function in LocalStack."
    info "To invoke the Lambda function manually, run:"
    echo "aws --endpoint-url=http://localhost:4566 lambda invoke --function-name ops-api-lambda --payload '{\"dry_run\": true}' response.json"
}

# Run the main function
main

#!/bin/bash
# Deploy to Local AWS Lambda Container
# This script deploys the OPS API Lambda function to a local AWS Lambda container.
# It handles the entire deployment process, including:
# 1. Building the package
# 2. Starting the AWS Lambda container
# 3. Setting up the environment variables
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
    
    # Stop any existing containers
    docker-compose down 2>/dev/null || true
}

# Install dependencies
function install_dependencies() {
    info "Installing dependencies..."
    
    # Install dependencies using pip
    python -m pip install -r requirements.txt
    info "Dependencies installed."
}

# Build the package
function build_package() {
    info "Building the package..."
    
    # Install the uscis-opts package
    info "Installing uscis-opts package..."
    python -m pip install "uscis-opts>=0.1.4"
    info "uscis-opts package installed."
    
    # Install the package normally instead of in development mode
    python -m pip install .
    info "Package built."
}

# Set up the AWS Lambda local environment
function setup_lambda_local() {
    info "Setting up the AWS Lambda local environment..."
    
    # Make sure setup_local.py is executable
    chmod +x setup_local.py
    
    # Run the script
    python setup_local.py
    info "AWS Lambda local environment set up."
}

# Test the Lambda function locally
function test_lambda_local() {
    info "Testing the Lambda function locally..."
    
    # Make sure test_lambda_local.py is executable
    chmod +x tests/test_lambda_local.py
    
    # Run test
    python tests/test_lambda_local.py
    info "Local Lambda function test completed."
}

# Test the Lambda function in the Docker container
function test_lambda_container() {
    info "Testing the Lambda function in the Docker container..."
    
    # Create a test event
    local event='{"dry_run": true, "time": "'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'"}'
    
    # Invoke the Lambda function
    info "Invoking Lambda function with event: ${event}"
    curl -s -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d "${event}" | jq .
    
    info "Lambda function test completed."
}

# Main function
function main() {
    info "Starting deployment to local AWS Lambda container..."
    
    # Parse command line arguments
    local skip_tests=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                skip_tests=true
                shift
                ;;
            *)
                error "Unknown option: $1"
                echo "Usage: $0 [--skip-tests]"
                exit 1
                ;;
        esac
    done
    
    # Check if Docker is running
    check_docker
    
    # Install dependencies
    install_dependencies
    
    # Build the package
    build_package
    
    # Set up the AWS Lambda local environment
    setup_lambda_local
    
    # Test the Lambda function
    if [ "$skip_tests" = false ]; then
        # Test the Lambda function locally
        test_lambda_local
        
        # Test the Lambda function in the Docker container
        test_lambda_container
    else
        info "Skipping Lambda function tests"
    fi
    
    info "Deployment to local AWS Lambda container completed successfully!"
    info "You can now use the Lambda function in the Docker container."
    info "To invoke the Lambda function manually, run:"
    echo "curl -XPOST \"http://localhost:9000/2015-03-31/functions/function/invocations\" -d '{\"dry_run\": true}'"
}

# Run the main function with command line arguments
main "$@"

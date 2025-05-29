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
    docker compose down
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
    
    # Install the Archer_API package
    info "Installing Archer_API package..."
    # Use the absolute path to ensure pip can find the package
    ARCHER_API_PATH="$(pwd)/ops_api/Archer_API"
    python -m pip install "${ARCHER_API_PATH}"
    info "Archer_API package installed."
    
    # Install the package normally instead of in development mode
    # This avoids the file conflict error with setuptools
    python -m pip install .
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
        
        # Wait for LocalStack to be ready
        info "Waiting for LocalStack to be ready..."
        sleep 10  # Give LocalStack some time to initialize
    fi
    
    # Set dummy AWS credentials for LocalStack
    export AWS_ACCESS_KEY_ID="test"
    export AWS_SECRET_ACCESS_KEY="test"
    export AWS_DEFAULT_REGION="us-east-1"
    info "AWS credentials set for LocalStack."
}

# Set up the LocalStack environment
function setup_localstack() {
    info "Setting up the LocalStack environment..."
    # Make sure setup_localstack.py is executable
    chmod +x setup_localstack.py
    # Run the script
    python setup_localstack.py
    info "LocalStack environment set up."
}

# Test the Lambda function locally
function test_lambda_local() {
    info "Testing the Lambda function locally..."
    
    # Make sure test_lambda_local.py is executable
    chmod +x test_lambda_local.py
    
    # Run test using the found Python executable
    python test_lambda_local.py
    info "Local Lambda function test completed."
}

# Test the Lambda function in LocalStack
function test_lambda_localstack() {
    info "Testing the Lambda function in LocalStack..."
    
    # Make sure test_lambda_localstack.py is executable
    chmod +x test_lambda_localstack.py
    
    # Run test using the found Python executable
    python test_lambda_localstack.py
    info "LocalStack Lambda function test completed."
}

# Create and deploy Lambda layers
function create_and_deploy_layers() {
    info "Creating and deploying Lambda layers..."
    
    # Check if Docker is available
    if docker info > /dev/null 2>&1; then
        # Use Docker to build the layers (recommended)
        info "Using Docker to build the Lambda layers..."
        
        # Make sure build_layers_with_docker.sh is executable
        chmod +x build_layers_with_docker.sh
        
        # Run the script
        ./build_layers_with_docker.sh
    else
        # Use local Python to build the layers
        info "Docker not available, using local Python to build the Lambda layers..."
        
        # Make sure create_layers.sh is executable
        chmod +x create_layers.sh
        
        # Run the script
        ./create_layers.sh
    fi
    
    # Deploy the layers to LocalStack
    info "Deploying Lambda layers to LocalStack..."
    
    # Define layer paths
    CORE_LAYER_PATH="build/layers/core-dependencies-layer.zip"
    DATA_LAYER_PATH="build/layers/data-processing-layer.zip"
    CUSTOM_LAYER_PATH="build/layers/custom-code-layer.zip"
    
    # Create the layers in LocalStack
    info "Publishing core dependencies layer..."
    aws --endpoint-url=http://localhost:4566 lambda publish-layer-version \
        --layer-name core-dependencies-layer \
        --description "Core dependencies for OPS API Lambda function" \
        --compatible-runtimes python3.9 \
        --zip-file fileb://${CORE_LAYER_PATH}
    
    info "Publishing data processing layer..."
    aws --endpoint-url=http://localhost:4566 lambda publish-layer-version \
        --layer-name data-processing-layer \
        --description "Data processing libraries (pandas) for OPS API Lambda function" \
        --compatible-runtimes python3.9 \
        --zip-file fileb://${DATA_LAYER_PATH}
    
    info "Publishing custom code layer..."
    aws --endpoint-url=http://localhost:4566 lambda publish-layer-version \
        --layer-name custom-code-layer \
        --description "Custom code and libraries for OPS API Lambda function" \
        --compatible-runtimes python3.9 \
        --zip-file fileb://${CUSTOM_LAYER_PATH}
    
    # Get the ARNs of the layers
    CORE_LAYER_ARN=$(aws --endpoint-url=http://localhost:4566 lambda list-layer-versions \
        --layer-name core-dependencies-layer \
        --query 'LayerVersions[0].LayerVersionArn' \
        --output text)
    
    DATA_LAYER_ARN=$(aws --endpoint-url=http://localhost:4566 lambda list-layer-versions \
        --layer-name data-processing-layer \
        --query 'LayerVersions[0].LayerVersionArn' \
        --output text)
    
    CUSTOM_LAYER_ARN=$(aws --endpoint-url=http://localhost:4566 lambda list-layer-versions \
        --layer-name custom-code-layer \
        --query 'LayerVersions[0].LayerVersionArn' \
        --output text)
    
    info "Core Layer ARN: $CORE_LAYER_ARN"
    info "Data Layer ARN: $DATA_LAYER_ARN"
    info "Custom Layer ARN: $CUSTOM_LAYER_ARN"
    
    # Update the Lambda function to use the layers
    info "Updating Lambda function to use the layers..."
    
    # Update the Lambda function configuration to use the layers
    aws --endpoint-url=http://localhost:4566 lambda update-function-configuration \
        --function-name ops-api-lambda \
        --layers "$CORE_LAYER_ARN" "$DATA_LAYER_ARN" "$CUSTOM_LAYER_ARN"
    
    info "Lambda function updated to use the layers."
}

# Main function
function main() {
    info "Starting deployment to LocalStack..."
    
    # Parse command line arguments
    local debug_mode=false
    local skip_tests=false
    local skip_layers=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --debug)
                debug_mode=true
                shift
                ;;
            --skip-tests)
                skip_tests=true
                shift
                ;;
            --skip-layers)
                skip_layers=true
                shift
                ;;
            *)
                error "Unknown option: $1"
                echo "Usage: $0 [--debug] [--skip-tests] [--skip-layers]"
                exit 1
                ;;
        esac
    done
    
    if [ "$debug_mode" = true ]; then
        info "Running in DEBUG mode"
    fi
    
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
    
    # Create and deploy Lambda layers
    if [ "$skip_layers" = false ]; then
        create_and_deploy_layers
    else
        info "Skipping Lambda layers creation and deployment"
    fi
    
    # Test the Lambda function
    if [ "$skip_tests" = false ]; then
        # Test the Lambda function locally
        test_lambda_local
        
        # Test the Lambda function in LocalStack
        test_lambda_localstack
    else
        info "Skipping Lambda function tests"
    fi
    
    info "Deployment to LocalStack completed successfully!"
    info "You can now use the Lambda function in LocalStack."
    info "To invoke the Lambda function manually, run:"
    echo "aws --endpoint-url=http://localhost:4566 lambda invoke --function-name ops-api-lambda --payload '{\"dry_run\": true}' response.json"
}

# Run the main function with command line arguments
main "$@"

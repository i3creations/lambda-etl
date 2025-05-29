#!/bin/bash
# Build Lambda Layers using Docker
# This script uses Docker to build Lambda layers to ensure compatibility with the Lambda execution environment

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

# Create build directory
function ensure_build_directory() {
    local build_dir="$(dirname "$0")/build/layers"
    mkdir -p "${build_dir}"
    echo "${build_dir}"
}

# Create core dependencies layer using Docker
function create_core_dependencies_layer() {
    info "Creating core dependencies layer using Docker..."
    
    local build_dir=$(ensure_build_directory)
    local docker_build_dir="/tmp/build"
    
    # Create a temporary Dockerfile
    cat > Dockerfile.layer << EOF
FROM public.ecr.aws/lambda/python:3.9

# Copy requirements file
COPY requirements-core.txt /tmp/requirements.txt

# Install dependencies
RUN pip install -r /tmp/requirements.txt -t ${docker_build_dir}/python --no-cache-dir

# Create the layer structure
RUN mkdir -p ${docker_build_dir}

# Set permissions
RUN chmod -R 755 ${docker_build_dir}
EOF

    # Create requirements file for core dependencies
    cat > requirements-core.txt << EOF
requests>=2.22.0
pytz>=2019.3
python-dotenv>=0.19.0
boto3>=1.38.19
aws-lambda-powertools>=1.25.0
EOF

    # Build the Docker image
    info "Building Docker image for core dependencies layer..."
    docker build -t lambda-layer-core-deps -f Dockerfile.layer .
    
    # Create a container from the image
    info "Creating container from the image..."
    docker create --name lambda-layer-core-deps-container lambda-layer-core-deps
    
    # Copy the layer files from the container
    info "Copying layer files from the container..."
    docker cp lambda-layer-core-deps-container:${docker_build_dir} "${build_dir}/core-dependencies"
    
    # Remove the container
    info "Removing the container..."
    docker rm lambda-layer-core-deps-container
    
    # Create ZIP file
    info "Creating ZIP file..."
    cd "${build_dir}/core-dependencies"
    zip -r "../core-dependencies-layer.zip" .
    cd - > /dev/null
    
    # Clean up
    rm -f Dockerfile.layer requirements-core.txt
    
    info "Core dependencies layer created: ${build_dir}/../core-dependencies-layer.zip"
}

# Create data processing layer using Docker
function create_data_processing_layer() {
    info "Creating data processing layer using Docker..."
    
    local build_dir=$(ensure_build_directory)
    local docker_build_dir="/tmp/build"
    
    # Create a temporary Dockerfile
    cat > Dockerfile.layer << EOF
FROM public.ecr.aws/lambda/python:3.9

# Copy requirements file
COPY requirements-data.txt /tmp/requirements.txt

# Install dependencies
RUN pip install -r /tmp/requirements.txt -t ${docker_build_dir}/python --no-cache-dir

# Create the layer structure
RUN mkdir -p ${docker_build_dir}

# Set permissions
RUN chmod -R 755 ${docker_build_dir}
EOF

    # Create requirements file for data processing dependencies
    cat > requirements-data.txt << EOF
pandas>=2.2.3
EOF

    # Build the Docker image
    info "Building Docker image for data processing layer..."
    docker build -t lambda-layer-data-proc -f Dockerfile.layer .
    
    # Create a container from the image
    info "Creating container from the image..."
    docker create --name lambda-layer-data-proc-container lambda-layer-data-proc
    
    # Copy the layer files from the container
    info "Copying layer files from the container..."
    docker cp lambda-layer-data-proc-container:${docker_build_dir} "${build_dir}/data-processing"
    
    # Remove the container
    info "Removing the container..."
    docker rm lambda-layer-data-proc-container
    
    # Create ZIP file
    info "Creating ZIP file..."
    cd "${build_dir}/data-processing"
    zip -r "../data-processing-layer.zip" .
    cd - > /dev/null
    
    # Clean up
    rm -f Dockerfile.layer requirements-data.txt
    
    info "Data processing layer created: ${build_dir}/../data-processing-layer.zip"
}

# Create custom code layer using Docker
function create_custom_code_layer() {
    info "Creating custom code layer using Docker..."
    
    local build_dir=$(ensure_build_directory)
    local docker_build_dir="/tmp/build"
    
    # Create a temporary directory for the Archer_API package
    mkdir -p "${build_dir}/archer_api_tmp"
    cp -r ops_api/Archer_API/* "${build_dir}/archer_api_tmp/"
    
    # Create a temporary Dockerfile
    cat > Dockerfile.layer << EOF
FROM public.ecr.aws/lambda/python:3.9

# Copy requirements file and Archer_API package
COPY requirements-custom.txt /tmp/requirements.txt
COPY ${build_dir}/archer_api_tmp /tmp/Archer_API

# Install dependencies
RUN pip install -r /tmp/requirements.txt -t ${docker_build_dir}/python --no-cache-dir
RUN pip install /tmp/Archer_API -t ${docker_build_dir}/python --no-cache-dir

# Create the layer structure
RUN mkdir -p ${docker_build_dir}

# Set permissions
RUN chmod -R 755 ${docker_build_dir}
EOF

    # Create requirements file for custom code dependencies
    cat > requirements-custom.txt << EOF
uscis-opts>=0.1.4
EOF

    # Build the Docker image
    info "Building Docker image for custom code layer..."
    docker build -t lambda-layer-custom-code -f Dockerfile.layer .
    
    # Create a container from the image
    info "Creating container from the image..."
    docker create --name lambda-layer-custom-code-container lambda-layer-custom-code
    
    # Copy the layer files from the container
    info "Copying layer files from the container..."
    docker cp lambda-layer-custom-code-container:${docker_build_dir} "${build_dir}/custom-code"
    
    # Remove the container
    info "Removing the container..."
    docker rm lambda-layer-custom-code-container
    
    # Create ZIP file
    info "Creating ZIP file..."
    cd "${build_dir}/custom-code"
    zip -r "../custom-code-layer.zip" .
    cd - > /dev/null
    
    # Clean up
    rm -f Dockerfile.layer requirements-custom.txt
    rm -rf "${build_dir}/archer_api_tmp"
    
    info "Custom code layer created: ${build_dir}/../custom-code-layer.zip"
}

# Create all layers
function create_all_layers() {
    info "Creating all Lambda layers using Docker..."
    
    create_core_dependencies_layer
    create_data_processing_layer
    create_custom_code_layer
    
    info "All Lambda layers created successfully!"
}

# Main function
function main() {
    info "Starting Lambda layers creation using Docker..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    create_all_layers
    
    info "Lambda layers creation using Docker completed!"
}

# Run the main function
main

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
    
    # Create ZIP file using Docker
    info "Creating ZIP file using Docker..."
    docker run --rm -v "${build_dir}:/data" -w /data alpine:latest sh -c "apk add --no-cache zip && cd core-dependencies && zip -r ../core-dependencies-layer.zip ."
    
    # Clean up
    rm -f Dockerfile.layer requirements-core.txt
    
    info "Core dependencies layer created: ${build_dir}/../core-dependencies-layer.zip"
}

# Note: We no longer create a custom data processing layer with pandas
# Instead, we use the AWS managed layer for AWS SDK for pandas
# This provides better performance, smaller deployment size, and automatic updates

# Create archer layer
function create_archer_layer() {
    info "Creating Archer API layer..."
    
    local build_dir=$(ensure_build_directory)
    local layer_dir="${build_dir}/archer-layer"
    local python_dir="${layer_dir}/python"
    
    # Clean up previous build
    rm -rf "${layer_dir}"
    mkdir -p "${python_dir}/archer"
    
    # Create archer directory structure
    mkdir -p "${python_dir}/archer/content"
    mkdir -p "${python_dir}/archer/restful/content"
    mkdir -p "${python_dir}/archer/restful/metadata"
    mkdir -p "${python_dir}/archer/templates"
    mkdir -p "${python_dir}/archer/web_services"
    
    info "Copying only essential Archer_API files..."
    
    # Copy only the absolutely essential Python files
    cp ops_api/Archer_API/src/archer/__init__.py "${python_dir}/archer/"
    cp ops_api/Archer_API/src/archer/ArcherAuth.py "${python_dir}/archer/"
    cp ops_api/Archer_API/src/archer/ArcherClient.py "${python_dir}/archer/"
    
    # Only copy the most essential files from each subdirectory
    cp ops_api/Archer_API/src/archer/content/__init__.py "${python_dir}/archer/content/"
    cp ops_api/Archer_API/src/archer/content/ContentClient.py "${python_dir}/archer/content/"
    
    cp ops_api/Archer_API/src/archer/restful/__init__.py "${python_dir}/archer/restful/"
    cp ops_api/Archer_API/src/archer/restful/RestfulClient.py "${python_dir}/archer/restful/"
    
    cp ops_api/Archer_API/src/archer/restful/content/__init__.py "${python_dir}/archer/restful/content/"
    cp ops_api/Archer_API/src/archer/restful/content/Content.py "${python_dir}/archer/restful/content/"
    
    cp ops_api/Archer_API/src/archer/restful/metadata/__init__.py "${python_dir}/archer/restful/metadata/"
    cp ops_api/Archer_API/src/archer/restful/metadata/Application.py "${python_dir}/archer/restful/metadata/"
    
    cp ops_api/Archer_API/src/archer/templates/__init__.py "${python_dir}/archer/templates/"
    cp ops_api/Archer_API/src/archer/templates/ExecuteSearch.xml "${python_dir}/archer/templates/"
    
    cp ops_api/Archer_API/src/archer/web_services/__init__.py "${python_dir}/archer/web_services/"
    cp ops_api/Archer_API/src/archer/web_services/WebServicesClient.py "${python_dir}/archer/web_services/"
    
    # Set permissions
    chmod -R 755 "${layer_dir}"
    
    # Create ZIP file with maximum compression using Docker
    info "Creating ZIP file with maximum compression using Docker..."
    docker run --rm -v "${build_dir}:/data" -w /data alpine:latest sh -c "apk add --no-cache zip && cd archer-layer && zip -r -9 ../archer-layer.zip ."
    
    # Get the size of the ZIP file
    local zip_size=$(du -h "${build_dir}/archer-layer.zip" | cut -f1)
    local zip_size_bytes=$(stat -c %s "${build_dir}/archer-layer.zip")
    info "Archer layer size: ${zip_size} (${zip_size_bytes} bytes)"
    
    info "Archer layer created: ${build_dir}/archer-layer.zip"
}

# Create ops-api layer
function create_ops_api_layer() {
    info "Creating OPS API layer..."
    
    local build_dir=$(ensure_build_directory)
    local layer_dir="${build_dir}/ops-api-layer"
    local python_dir="${layer_dir}/python"
    
    # Clean up previous build
    rm -rf "${layer_dir}"
    mkdir -p "${python_dir}"
    
    # Copy ops_api modules directly instead of using uscis-opts package
    info "Copying ops_api modules directly..."
    
    # Create ops_portal directory
    mkdir -p "${python_dir}/ops_portal"
    cp ops_api/ops_portal/__init__.py "${python_dir}/ops_portal/"
    cp ops_api/ops_portal/api.py "${python_dir}/ops_portal/"
    
    # Create processing directory
    mkdir -p "${python_dir}/processing"
    cp ops_api/processing/__init__.py "${python_dir}/processing/"
    cp ops_api/processing/field_mapping.py "${python_dir}/processing/"
    cp ops_api/processing/html_stripper.py "${python_dir}/processing/"
    cp ops_api/processing/preprocess.py "${python_dir}/processing/"
    
    # Create utils directory
    mkdir -p "${python_dir}/utils"
    cp ops_api/utils/__init__.py "${python_dir}/utils/"
    cp ops_api/utils/logging_utils.py "${python_dir}/utils/"
    cp ops_api/utils/time_utils.py "${python_dir}/utils/"
    
    # Set permissions
    chmod -R 755 "${layer_dir}"
    
    # Create ZIP file with maximum compression using Docker
    info "Creating ZIP file with maximum compression using Docker..."
    docker run --rm -v "${build_dir}:/data" -w /data alpine:latest sh -c "apk add --no-cache zip && cd ops-api-layer && zip -r -9 ../ops-api-layer.zip ."
    
    # Get the size of the ZIP file
    local zip_size=$(du -h "${build_dir}/ops-api-layer.zip" | cut -f1)
    local zip_size_bytes=$(stat -c %s "${build_dir}/ops-api-layer.zip")
    info "OPS API layer size: ${zip_size} (${zip_size_bytes} bytes)"
    
    info "OPS API layer created: ${build_dir}/ops-api-layer.zip"
}

# Create custom code layer (for backward compatibility)
function create_custom_code_layer() {
    info "Creating custom code layer (split into separate layers)..."
    
    # Create the individual layers
    create_archer_layer
    create_ops_api_layer
    
    info "Custom code layers created successfully!"
}

# Create pandas layer directly (without Docker)
function create_pandas_layer_direct() {
    info "Creating pandas layer directly (without Docker)..."
    
    local build_dir=$(ensure_build_directory)
    local layer_dir="${build_dir}/pandas-direct-layer"
    local python_dir="${layer_dir}/python"
    
    # Clean up previous build
    rm -rf "${layer_dir}"
    mkdir -p "${python_dir}"
    
    # Create a virtual environment
    info "Creating virtual environment..."
    python -m venv "${layer_dir}/venv"
    
    # Activate the virtual environment
    source "${layer_dir}/venv/bin/activate"
    
    # Install pandas and its dependencies
    info "Installing pandas and dependencies..."
    pip install pandas numpy pytz python-dateutil six
    
    # List installed packages for debugging
    info "Installed packages:"
    pip list
    
    # Copy pandas and dependencies from the virtual environment to the layer
    info "Copying pandas and dependencies to the layer..."
    cp -r "${layer_dir}/venv/lib/python"*"/site-packages/pandas" "${python_dir}/"
    cp -r "${layer_dir}/venv/lib/python"*"/site-packages/numpy" "${python_dir}/"
    cp -r "${layer_dir}/venv/lib/python"*"/site-packages/pytz" "${python_dir}/"
    cp -r "${layer_dir}/venv/lib/python"*"/site-packages/dateutil" "${python_dir}/"
    cp -r "${layer_dir}/venv/lib/python"*"/site-packages/six.py" "${python_dir}/"
    
    # Verify the files were copied
    info "Verifying pandas files in layer:"
    ls -la "${python_dir}/pandas"
    
    # Deactivate the virtual environment
    deactivate
    
    # Clean up the virtual environment
    rm -rf "${layer_dir}/venv"
    
    # Create ZIP file using Docker
    info "Creating ZIP file using Docker..."
    docker run --rm -v "${build_dir}:/data" -w /data alpine:latest sh -c "apk add --no-cache zip && cd pandas-direct-layer && zip -r ../pandas-direct-layer.zip ."
    
    # Get the size of the ZIP file
    local zip_size=$(du -h "${build_dir}/pandas-direct-layer.zip" | cut -f1)
    local zip_size_bytes=$(stat -c %s "${build_dir}/pandas-direct-layer.zip")
    info "Pandas direct layer size: ${zip_size} (${zip_size_bytes} bytes)"
    
    info "Pandas direct layer created: ${build_dir}/pandas-direct-layer.zip"
}

# Create all layers
function create_all_layers() {
    info "Creating all Lambda layers using Docker..."
    
    create_core_dependencies_layer
    # Note: We no longer create a custom data processing layer with pandas
    # Instead, we use the AWS managed layer for AWS SDK for pandas
    create_custom_code_layer
    # Keep pandas layer direct for LocalStack compatibility (optional)
    create_pandas_layer_direct
    
    info "All Lambda layers created successfully!"
    info "Note: For AWS deployment, use the AWS managed layer for pandas instead of the custom layer."
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

#!/bin/bash
# Create Lambda Layers for the OPS API project
# This script creates three Lambda layers:
# 1. core-dependencies-layer: Common libraries (requests, pytz, boto3, etc.)
# 2. data-processing-layer: Pandas and its dependencies
# 3. custom-code-layer: Archer API and uscis-opts

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

# Create core dependencies layer
function create_core_dependencies_layer() {
    info "Creating core dependencies layer..."
    
    local build_dir=$(ensure_build_directory)
    local layer_dir="${build_dir}/core-dependencies"
    local python_dir="${layer_dir}/python"
    
    # Clean up previous build
    rm -rf "${layer_dir}"
    mkdir -p "${python_dir}"
    
    # Install dependencies
    pip install requests pytz python-dotenv boto3 aws-lambda-powertools -t "${python_dir}" --no-cache-dir
    
    # Create ZIP file
    cd "${layer_dir}"
    zip -r "${build_dir}/core-dependencies-layer.zip" .
    cd - > /dev/null
    
    info "Core dependencies layer created: ${build_dir}/core-dependencies-layer.zip"
}

# Create data processing layer
function create_data_processing_layer() {
    info "Creating data processing layer..."
    
    local build_dir=$(ensure_build_directory)
    local layer_dir="${build_dir}/data-processing"
    local python_dir="${layer_dir}/python"
    
    # Clean up previous build
    rm -rf "${layer_dir}"
    mkdir -p "${python_dir}"
    
    # Install pandas (which will include numpy and other dependencies)
    pip install pandas -t "${python_dir}" --no-cache-dir
    
    # Create ZIP file
    cd "${layer_dir}"
    zip -r "${build_dir}/data-processing-layer.zip" .
    cd - > /dev/null
    
    info "Data processing layer created: ${build_dir}/data-processing-layer.zip"
}

# Create custom code layer
function create_custom_code_layer() {
    info "Creating custom code layer..."
    
    local build_dir=$(ensure_build_directory)
    local layer_dir="${build_dir}/custom-code"
    local python_dir="${layer_dir}/python"
    
    # Clean up previous build
    rm -rf "${layer_dir}"
    mkdir -p "${python_dir}"
    
    # Install uscis-opts
    pip install uscis-opts -t "${python_dir}" --no-cache-dir
    
    # Install Archer_API from local directory
    pip install ./ops_api/Archer_API -t "${python_dir}" --no-cache-dir
    
    # Create ZIP file
    cd "${layer_dir}"
    zip -r "${build_dir}/custom-code-layer.zip" .
    cd - > /dev/null
    
    info "Custom code layer created: ${build_dir}/custom-code-layer.zip"
}

# Create all layers
function create_all_layers() {
    info "Creating all Lambda layers..."
    
    create_core_dependencies_layer
    create_data_processing_layer
    create_custom_code_layer
    
    info "All Lambda layers created successfully!"
}

# Main function
function main() {
    info "Starting Lambda layers creation..."
    create_all_layers
    info "Lambda layers creation completed!"
}

# Run the main function
main

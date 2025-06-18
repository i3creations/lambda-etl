#!/bin/bash
# Start Local Environment Script
#
# This script starts the LocalStack environment and sets up everything needed for local development.
# It performs the following steps:
# 1. Start the LocalStack container using docker-compose
# 2. Wait for LocalStack to be ready
# 3. Set up the SSM parameters
# 4. Set up the secrets
# 5. Set up the Lambda function
#
# Usage:
#   ./start_local_environment.sh

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

# Start the LocalStack container
function start_localstack() {
    info "Starting LocalStack container..."
    docker-compose up -d localstack
    info "LocalStack container started."
}

# Wait for LocalStack to be ready
function wait_for_localstack() {
    info "Waiting for LocalStack to be ready..."
    
    local max_retries=30
    local retry_interval=2
    
    for ((i=1; i<=$max_retries; i++)); do
        # Check LocalStack health endpoint directly
        local health_response=$(curl -s "http://localhost:4566/_localstack/health")
        
        # Check if jq is installed
        if ! command -v jq &> /dev/null; then
            warn "jq is not installed. Using grep instead."
            # Check for either "running" or "available" status for required services
            if (echo "$health_response" | grep -q "\"ssm\": \"running\"" || echo "$health_response" | grep -q "\"ssm\": \"available\"") && \
               (echo "$health_response" | grep -q "\"lambda\": \"running\"" || echo "$health_response" | grep -q "\"lambda\": \"available\"") && \
               (echo "$health_response" | grep -q "\"s3\": \"running\"" || echo "$health_response" | grep -q "\"s3\": \"available\"") && \
               (echo "$health_response" | grep -q "\"secretsmanager\": \"running\"" || echo "$health_response" | grep -q "\"secretsmanager\": \"available\""); then
                info "LocalStack is ready!"
                return 0
            fi
        else
            # Use jq to check if required services are running or available
            if echo "$health_response" | jq -e '
                (.services.ssm == "running" or .services.ssm == "available") and
                (.services.lambda == "running" or .services.lambda == "available") and
                (.services.s3 == "running" or .services.s3 == "available") and
                (.services.secretsmanager == "running" or .services.secretsmanager == "available")
            ' &> /dev/null; then
                info "LocalStack is ready!"
                # Display the health status
                echo "LocalStack health status:"
                echo "$health_response" | jq
                return 0
            else
                # Show which services are not ready
                if command -v jq &> /dev/null; then
                    echo "Waiting for services to be ready:"
                    echo "$health_response" | jq '.services | {ssm, lambda, s3, secretsmanager}'
                fi
            fi
        fi
        
        echo -n "."
        sleep $retry_interval
    done
    
    error "LocalStack failed to start within the expected time."
    exit 1
}

# Set up the SSM parameters
function setup_ssm_parameters() {
    info "Setting up SSM parameters..."
    ./setup_localstack.sh
    info "SSM parameters set up."
}

# Set up the secrets
function setup_secrets() {
    info "Setting up secrets..."
    python setup_secrets.py
    info "Secrets set up."
}

# Start the Lambda container
function start_lambda_container() {
    info "Starting Lambda container..."
    docker-compose up -d lambda
    info "Lambda container started."
}

# Main function
function main() {
    info "Starting local environment..."
    
    # Check if Docker is running
    check_docker
    
    # Start the LocalStack container
    start_localstack
    
    # Wait for LocalStack to be ready
    wait_for_localstack
    
    # Set up the SSM parameters
    setup_ssm_parameters
    
    # Set up the secrets
    setup_secrets
    
    # Start the Lambda container
    start_lambda_container
    
    info "Local environment started successfully!"
    info "You can now test the Lambda function with:"
    echo "curl -XPOST \"http://localhost:9000/2015-03-31/functions/function/invocations\" -d '{\"dry_run\": true}'"
}

# Run the main function
main

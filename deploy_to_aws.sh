#!/bin/bash
# Deploy to AWS
# This script deploys the OPS API Lambda function to AWS.
# It handles the entire deployment process, including:
# 1. Building the package
# 2. Creating Lambda layers
# 3. Creating/updating the Lambda function
# 4. Setting up CloudWatch Events for scheduled execution

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

# AWS region
AWS_REGION="us-east-1"

# Lambda function name
LAMBDA_FUNCTION_NAME="ops-api-lambda"

# CloudWatch Events rule name
EVENT_RULE_NAME="ops-api-schedule"

# Lambda execution role
LAMBDA_ROLE_ARN=""

# Check if AWS CLI is installed
function check_aws_cli() {
    info "Checking if AWS CLI is installed..."
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed. Please install it and try again."
        exit 1
    fi
    info "AWS CLI is installed."
    
    # Check if AWS CLI is configured
    info "Checking if AWS CLI is configured..."
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS CLI is not configured. Please configure it with 'aws configure' and try again."
        exit 1
    fi
    info "AWS CLI is configured."
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
    
    # Install the Archer_API package in development mode
    info "Installing Archer_API package..."
    # Use the absolute path to ensure pip can find the package
    ARCHER_API_PATH="$(pwd)/ops_api/Archer_API"
    python -m pip install -e "${ARCHER_API_PATH}"
    info "Archer_API package installed."
    
    # Build package using pip
    python -m pip install -e .
    info "Package built."
}

# Create Lambda layers
function create_layers() {
    info "Creating Lambda layers..."
    
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
    
    info "Lambda layers created."
}

# Deploy Lambda layers to AWS
function deploy_layers() {
    info "Deploying Lambda layers to AWS..."
    
    # Define layer paths
    CORE_LAYER_PATH="build/layers/core-dependencies-layer.zip"
    DATA_LAYER_PATH="build/layers/data-processing-layer.zip"
    CUSTOM_LAYER_PATH="build/layers/custom-code-layer.zip"
    
    # Check if the layer files exist
    if [ ! -f "${CORE_LAYER_PATH}" ] || [ ! -f "${DATA_LAYER_PATH}" ] || [ ! -f "${CUSTOM_LAYER_PATH}" ]; then
        error "Layer files not found. Please run create_layers.sh or build_layers_with_docker.sh first."
        exit 1
    fi
    
    # Publish the layers to AWS
    info "Publishing core dependencies layer..."
    CORE_LAYER_ARN=$(aws lambda publish-layer-version \
        --layer-name core-dependencies-layer \
        --description "Core dependencies for OPS API Lambda function" \
        --compatible-runtimes python3.9 \
        --zip-file fileb://${CORE_LAYER_PATH} \
        --query 'LayerVersionArn' \
        --output text)
    
    info "Publishing data processing layer..."
    DATA_LAYER_ARN=$(aws lambda publish-layer-version \
        --layer-name data-processing-layer \
        --description "Data processing libraries (pandas) for OPS API Lambda function" \
        --compatible-runtimes python3.9 \
        --zip-file fileb://${DATA_LAYER_PATH} \
        --query 'LayerVersionArn' \
        --output text)
    
    info "Publishing custom code layer..."
    CUSTOM_LAYER_ARN=$(aws lambda publish-layer-version \
        --layer-name custom-code-layer \
        --description "Custom code and libraries for OPS API Lambda function" \
        --compatible-runtimes python3.9 \
        --zip-file fileb://${CUSTOM_LAYER_PATH} \
        --query 'LayerVersionArn' \
        --output text)
    
    info "Core Layer ARN: $CORE_LAYER_ARN"
    info "Data Layer ARN: $DATA_LAYER_ARN"
    info "Custom Layer ARN: $CUSTOM_LAYER_ARN"
    
    # Export the layer ARNs for later use
    export CORE_LAYER_ARN
    export DATA_LAYER_ARN
    export CUSTOM_LAYER_ARN
    
    info "Lambda layers deployed to AWS."
}

# Create Lambda function package
function create_lambda_package() {
    info "Creating Lambda function package..."
    
    # Ensure build directory exists
    local build_dir="$(dirname "$0")/build"
    mkdir -p "${build_dir}"
    
    # Create a temporary directory for the package
    local temp_dir="${build_dir}/lambda_package"
    rm -rf "${temp_dir}"
    mkdir -p "${temp_dir}"
    
    # Copy only the ops_api package to the temporary directory
    # (excluding Archer_API which will be in a layer)
    info "Copying ops_api package (excluding Archer_API)..."
    
    # Create ops_api directory structure
    mkdir -p "${temp_dir}/ops_api"
    
    # Copy Python files from ops_api directory
    for item in ops_api/*; do
        if [[ "${item}" == *"Archer_API"* ]]; then
            # Skip Archer_API as it will be in a layer
            continue
        fi
        
        if [ -d "${item}" ]; then
            cp -r "${item}" "${temp_dir}/ops_api/"
        elif [[ "${item}" == *.py ]] || [[ "${item}" == *"__init__.py" ]]; then
            cp "${item}" "${temp_dir}/ops_api/"
        fi
    done
    
    # Copy the config directory to the temporary directory
    info "Copying config files..."
    cp -r config "${temp_dir}/"
    
    # Create an empty __init__.py file in the root directory
    touch "${temp_dir}/__init__.py"
    
    info "Dependencies will be provided by Lambda layers..."
    
    # Create the ZIP file
    local zip_path="${build_dir}/ops_api_lambda.zip"
    
    # Create the ZIP file from the temporary directory
    info "Creating ZIP file..."
    cd "${temp_dir}"
    zip -r "${zip_path}" .
    cd - > /dev/null
    
    # Clean up the temporary directory
    rm -rf "${temp_dir}"
    
    info "Lambda function package created: ${zip_path}"
    
    # Return the path to the ZIP file
    echo "${zip_path}"
}

# Create or update Lambda function
function deploy_lambda_function() {
    info "Deploying Lambda function to AWS..."
    
    # Create the Lambda function package
    local zip_path=$(create_lambda_package)
    
    # Check if the Lambda function already exists
    if aws lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" &> /dev/null; then
        # Function exists, update it
        info "Updating existing Lambda function: ${LAMBDA_FUNCTION_NAME}"
        
        # Update the function code
        aws lambda update-function-code \
            --function-name "${LAMBDA_FUNCTION_NAME}" \
            --zip-file "fileb://${zip_path}"
        
        # Update the function configuration to use the layers
        aws lambda update-function-configuration \
            --function-name "${LAMBDA_FUNCTION_NAME}" \
            --layers "${CORE_LAYER_ARN}" "${DATA_LAYER_ARN}" "${CUSTOM_LAYER_ARN}"
        
        info "Lambda function updated: ${LAMBDA_FUNCTION_NAME}"
    else
        # Function doesn't exist, create it
        info "Creating new Lambda function: ${LAMBDA_FUNCTION_NAME}"
        
        # Check if Lambda role ARN is provided
        if [ -z "${LAMBDA_ROLE_ARN}" ]; then
            error "Lambda role ARN is not provided. Please set the LAMBDA_ROLE_ARN variable in the script."
            exit 1
        fi
        
        # Create the function
        aws lambda create-function \
            --function-name "${LAMBDA_FUNCTION_NAME}" \
            --runtime "python3.9" \
            --role "${LAMBDA_ROLE_ARN}" \
            --handler "ops_api.lambda_handler.handler" \
            --zip-file "fileb://${zip_path}" \
            --timeout 300 \
            --memory-size 512 \
            --layers "${CORE_LAYER_ARN}" "${DATA_LAYER_ARN}" "${CUSTOM_LAYER_ARN}"
        
        info "Lambda function created: ${LAMBDA_FUNCTION_NAME}"
    fi
    
    info "Lambda function deployed to AWS."
}

# Create CloudWatch Events rule for scheduled execution
function create_cloudwatch_event_rule() {
    info "Creating CloudWatch Events rule for scheduled execution..."
    
    # Check if the rule already exists
    if aws events describe-rule --name "${EVENT_RULE_NAME}" &> /dev/null; then
        info "CloudWatch Events rule already exists: ${EVENT_RULE_NAME}"
    else
        # Create the rule
        aws events put-rule \
            --name "${EVENT_RULE_NAME}" \
            --schedule-expression "rate(1 day)" \
            --state "ENABLED"
        
        info "CloudWatch Events rule created: ${EVENT_RULE_NAME}"
    fi
    
    # Get the Lambda function ARN
    local lambda_arn=$(aws lambda get-function \
        --function-name "${LAMBDA_FUNCTION_NAME}" \
        --query 'Configuration.FunctionArn' \
        --output text)
    
    # Add the Lambda function as a target
    aws events put-targets \
        --rule "${EVENT_RULE_NAME}" \
        --targets "Id=1,Arn=${lambda_arn}"
    
    info "Added Lambda function as target for CloudWatch Events rule: ${EVENT_RULE_NAME}"
    
    # Add permission for CloudWatch Events to invoke the Lambda function
    aws lambda add-permission \
        --function-name "${LAMBDA_FUNCTION_NAME}" \
        --statement-id "${EVENT_RULE_NAME}-Permission" \
        --action "lambda:InvokeFunction" \
        --principal "events.amazonaws.com" \
        --source-arn "$(aws events describe-rule --name ${EVENT_RULE_NAME} --query 'Arn' --output text)" \
        2>/dev/null || true
    
    info "Added permission for CloudWatch Events to invoke Lambda function: ${LAMBDA_FUNCTION_NAME}"
}

# Create SSM parameters for configuration
function create_ssm_parameters() {
    info "Creating SSM parameters for configuration..."
    
    # Prompt for Archer authentication settings
    read -p "Enter Archer username: " archer_username
    read -sp "Enter Archer password: " archer_password
    echo
    read -p "Enter Archer instance: " archer_instance
    
    # Prompt for OPS Portal API settings
    read -p "Enter OPS Portal auth URL: " ops_portal_auth_url
    read -p "Enter OPS Portal item URL: " ops_portal_item_url
    read -p "Enter OPS Portal client ID: " ops_portal_client_id
    read -sp "Enter OPS Portal client secret: " ops_portal_client_secret
    echo
    read -p "Verify SSL for OPS Portal API (true/false): " ops_portal_verify_ssl
    
    # Create the SSM parameters
    aws ssm put-parameter \
        --name "/ops-api/archer/username" \
        --value "${archer_username}" \
        --type "String" \
        --overwrite
    
    aws ssm put-parameter \
        --name "/ops-api/archer/password" \
        --value "${archer_password}" \
        --type "SecureString" \
        --overwrite
    
    aws ssm put-parameter \
        --name "/ops-api/archer/instance" \
        --value "${archer_instance}" \
        --type "String" \
        --overwrite
    
    aws ssm put-parameter \
        --name "/ops-api/ops-portal/auth-url" \
        --value "${ops_portal_auth_url}" \
        --type "String" \
        --overwrite
    
    aws ssm put-parameter \
        --name "/ops-api/ops-portal/item-url" \
        --value "${ops_portal_item_url}" \
        --type "String" \
        --overwrite
    
    aws ssm put-parameter \
        --name "/ops-api/ops-portal/client-id" \
        --value "${ops_portal_client_id}" \
        --type "SecureString" \
        --overwrite
    
    aws ssm put-parameter \
        --name "/ops-api/ops-portal/client-secret" \
        --value "${ops_portal_client_secret}" \
        --type "SecureString" \
        --overwrite
    
    aws ssm put-parameter \
        --name "/ops-api/ops-portal/verify-ssl" \
        --value "${ops_portal_verify_ssl}" \
        --type "String" \
        --overwrite
    
    # Initialize the time log parameter with current time
    aws ssm put-parameter \
        --name "/ops-api/time-log" \
        --value "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")" \
        --type "String" \
        --overwrite
    
    info "SSM parameters created."
}

# Main function
function main() {
    info "Starting deployment to AWS..."
    
    # Check if AWS CLI is installed and configured
    check_aws_cli
    
    # Prompt for AWS region
    read -p "Enter AWS region (default: ${AWS_REGION}): " input_region
    AWS_REGION=${input_region:-${AWS_REGION}}
    
    # Set AWS region
    export AWS_DEFAULT_REGION="${AWS_REGION}"
    
    # Prompt for Lambda function name
    read -p "Enter Lambda function name (default: ${LAMBDA_FUNCTION_NAME}): " input_function_name
    LAMBDA_FUNCTION_NAME=${input_function_name:-${LAMBDA_FUNCTION_NAME}}
    
    # Prompt for Lambda execution role ARN
    read -p "Enter Lambda execution role ARN: " LAMBDA_ROLE_ARN
    
    if [ -z "${LAMBDA_ROLE_ARN}" ]; then
        error "Lambda execution role ARN is required."
        exit 1
    fi
    
    # Install dependencies
    install_dependencies
    
    # Build the package
    build_package
    
    # Create Lambda layers
    create_layers
    
    # Deploy Lambda layers to AWS
    deploy_layers
    
    # Deploy Lambda function to AWS
    deploy_lambda_function
    
    # Create CloudWatch Events rule for scheduled execution
    create_cloudwatch_event_rule
    
    # Create SSM parameters for configuration
    create_ssm_parameters
    
    info "Deployment to AWS completed successfully!"
    info "Lambda function: ${LAMBDA_FUNCTION_NAME}"
    info "CloudWatch Events rule: ${EVENT_RULE_NAME}"
    info "You can now test the Lambda function with:"
    echo "aws lambda invoke --function-name ${LAMBDA_FUNCTION_NAME} --payload '{\"dry_run\": true}' response.json"
}

# Run the main function
main

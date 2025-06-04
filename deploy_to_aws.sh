#!/bin/bash
# Deploy to AWS
# This script deploys the OPS API Lambda function to AWS.
# It handles the entire deployment process, including:
# 1. Building the package
# 2. Creating custom Lambda layer (only for application-specific dependencies)
# 3. Using AWS SDK for pandas managed layer for core dependencies and data processing
# 4. Creating/updating the Lambda function
# 5. Setting up CloudWatch Events for scheduled execution

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

# Python version for Lambda
PYTHON_VERSION="3.9"

# Architecture (x86_64 or arm64)
ARCHITECTURE="x86_64"

# Get the correct AWS SDK for pandas managed layer ARN based on region, Python version, and architecture
function get_aws_sdk_pandas_layer_arn() {
    local region="$1"
    local python_version="$2"
    local architecture="$3"
    
    # Map Python version to the format used in layer names
    local python_suffix
    case "$python_version" in
        "3.9") python_suffix="39" ;;
        "3.10") python_suffix="310" ;;
        "3.11") python_suffix="311" ;;
        "3.12") python_suffix="312" ;;
        "3.13") python_suffix="313" ;;
        *) 
            warn "Unsupported Python version: $python_version. Defaulting to 3.9"
            python_suffix="39"
            ;;
    esac
    
    # Determine the layer name based on architecture
    local layer_name
    if [ "$architecture" = "arm64" ]; then
        layer_name="AWSSDKPandas-Python${python_suffix}-Arm64"
    else
        layer_name="AWSSDKPandas-Python${python_suffix}"
    fi
    
    # Get the version number based on Python version and architecture
    local version
    case "$python_suffix" in
        "39")
            if [ "$architecture" = "arm64" ]; then
                version="29"
            else
                version="29"
            fi
            ;;
        "310")
            if [ "$architecture" = "arm64" ]; then
                version="24"
            else
                version="24"
            fi
            ;;
        "311")
            if [ "$architecture" = "arm64" ]; then
                version="21"
            else
                version="21"
            fi
            ;;
        "312")
            if [ "$architecture" = "arm64" ]; then
                version="17"
            else
                version="17"
            fi
            ;;
        "313")
            if [ "$architecture" = "arm64" ]; then
                version="2"
            else
                version="2"
            fi
            ;;
        *) version="29" ;;
    esac
    
    # Special handling for regions with different account IDs
    local account_id
    local arn_prefix
    
    if [[ "$region" == cn-* ]]; then
        account_id="406640652441"
        arn_prefix="arn:aws-cn:lambda"
    elif [ "$region" = "ap-east-1" ]; then
        account_id="839552336658"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "ap-south-2" ]; then
        account_id="246107603503"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "ap-southeast-3" ]; then
        account_id="258944054355"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "ap-southeast-4" ]; then
        account_id="945386623051"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "eu-central-2" ]; then
        account_id="956415814219"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "eu-south-1" ]; then
        account_id="774444163449"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "eu-south-2" ]; then
        account_id="982086096842"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "il-central-1" ]; then
        account_id="263840725265"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "me-central-1" ]; then
        account_id="593833071574"
        arn_prefix="arn:aws:lambda"
    elif [ "$region" = "me-south-1" ]; then
        account_id="938046470361"
        arn_prefix="arn:aws:lambda"
    else
        # Default account ID for most regions
        account_id="336392948345"
        arn_prefix="arn:aws:lambda"
    fi
    
    # Construct and return the ARN
    local arn="${arn_prefix}:${region}:${account_id}:layer:${layer_name}:${version}"
    echo "$arn"
}

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
    
    # Install the uscis-opts package
    info "Installing uscis-opts package..."
    python -m pip install "uscis-opts>=0.1.4"
    info "uscis-opts package installed."
    
    # Build package using pip
    python -m pip install -e .
    info "Package built."
}

# Create Lambda layers using the optimized build script
function create_layers() {
    info "Creating Lambda layers using the optimized build script..."
    
    # Run the build_layers_with_docker.sh script
    if [ -f "build_layers_with_docker.sh" ]; then
        info "Running build_layers_with_docker.sh..."
        bash build_layers_with_docker.sh
        info "Lambda layers created successfully!"
    else
        error "build_layers_with_docker.sh script not found. Please make sure it exists in the current directory."
        exit 1
    fi
}

# Deploy Lambda layers to AWS
function deploy_layers() {
    info "Deploying Lambda layers to AWS..."
    
    # Define layer paths
    OPS_API_LAYER_PATH="build/layers/ops-api-layer.zip"
    
    # Check if the layer files exist
    if [ ! -f "${OPS_API_LAYER_PATH}" ]; then
        error "OPS API layer file not found. Please run build_layers_with_docker.sh first."
        exit 1
    fi
    
    # Publish the OPS API layer to AWS
    info "Publishing OPS API layer..."
    OPS_API_LAYER_ARN=$(aws lambda publish-layer-version \
        --layer-name ops-api-layer \
        --description "OPS API modules for Lambda function" \
        --compatible-runtimes python${PYTHON_VERSION} \
        --zip-file fileb://${OPS_API_LAYER_PATH} \
        --query 'LayerVersionArn' \
        --output text)
    
    info "OPS API Layer ARN: $OPS_API_LAYER_ARN"
    
    # Get the AWS SDK for pandas managed layer ARN
    info "Getting AWS SDK for pandas managed layer ARN..."
    
    # Use the correct ARN for the AWS SDK for pandas managed layer
    # Based on the region, Python version, and architecture
    AWS_SDK_PANDAS_LAYER_ARN=$(get_aws_sdk_pandas_layer_arn "$AWS_REGION" "$PYTHON_VERSION" "$ARCHITECTURE")
    
    info "AWS SDK for pandas Layer ARN: $AWS_SDK_PANDAS_LAYER_ARN"
    
    # Export the layer ARNs for later use
    export OPS_API_LAYER_ARN
    export AWS_SDK_PANDAS_LAYER_ARN
    
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
    
    # Copy only the src package to the temporary directory
    # (excluding Archer_API which will be in a layer)
    info "Copying src package (excluding Archer_API)..."
    
    # Create src directory structure
    mkdir -p "${temp_dir}/src"
    
    # Copy Python files from src directory
    for item in src/*; do
        if [[ "${item}" == *"Archer_API"* ]]; then
            # Skip Archer_API as it will be in a layer
            continue
        fi
        
        if [ -d "${item}" ]; then
            cp -r "${item}" "${temp_dir}/src/"
        elif [[ "${item}" == *.py ]] || [[ "${item}" == *"__init__.py" ]]; then
            cp "${item}" "${temp_dir}/src/"
        fi
    done
    
    # Copy the config directory to the temporary directory
    info "Copying config files..."
    cp -r config "${temp_dir}/"
    
    # Create an empty __init__.py file in the root directory
    touch "${temp_dir}/__init__.py"
    
    info "Dependencies will be provided by Lambda layers..."
    
    # Create the ZIP file
    local zip_path="${build_dir}/src_lambda.zip"
    
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
            --layers "${AWS_SDK_PANDAS_LAYER_ARN}" "${OPS_API_LAYER_ARN}"
        
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
            --runtime "python${PYTHON_VERSION}" \
            --role "${LAMBDA_ROLE_ARN}" \
            --handler "lambda_handler.handler" \
            --zip-file "fileb://${zip_path}" \
            --timeout 300 \
            --memory-size 512 \
            --layers "${AWS_SDK_PANDAS_LAYER_ARN}" "${OPS_API_LAYER_ARN}"
        
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
    info "Starting deployment to AWS using AWS SDK for pandas managed layer..."
    
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
    
    # Prompt for Python version
    read -p "Enter Python version (default: ${PYTHON_VERSION}): " input_python_version
    PYTHON_VERSION=${input_python_version:-${PYTHON_VERSION}}
    
    # Prompt for architecture
    read -p "Enter architecture (x86_64 or arm64, default: ${ARCHITECTURE}): " input_architecture
    ARCHITECTURE=${input_architecture:-${ARCHITECTURE}}
    
    # Validate architecture
    if [ "${ARCHITECTURE}" != "x86_64" ] && [ "${ARCHITECTURE}" != "arm64" ]; then
        error "Invalid architecture. Must be either x86_64 or arm64."
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

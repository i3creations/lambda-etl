#!/bin/bash
# LocalStack Setup Script
#
# This script sets up the LocalStack environment for local development and testing
# of the OPS API Lambda function. It creates the necessary AWS resources in the
# LocalStack environment, including:
#
# 1. SSM parameters for configuration (including time log)
# 2. Lambda function
# 3. CloudWatch Events rule for scheduled execution
#
# Usage:
#   ./setup_localstack.sh

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

# LocalStack endpoint URL
ENDPOINT_URL="http://localhost:4566"

# AWS region
REGION="us-east-1"

# Lambda function name
LAMBDA_FUNCTION_NAME="ops-api-lambda"

# CloudWatch Events rule name
EVENT_RULE_NAME="ops-api-schedule"

# AWS CLI common parameters
AWS_COMMON_ARGS="--endpoint-url=${ENDPOINT_URL} --region=${REGION} --no-verify-ssl --no-sign-request"

# Set dummy AWS credentials for LocalStack
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
export AWS_DEFAULT_REGION="${REGION}"

# This function has been moved to deploy_localstack.sh

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
               (echo "$health_response" | grep -q "\"s3\": \"running\"" || echo "$health_response" | grep -q "\"s3\": \"available\""); then
                info "LocalStack is ready!"
                return 0
            fi
        else
            # Use jq to check if required services are running or available
            if echo "$health_response" | jq -e '
                (.services.ssm == "running" or .services.ssm == "available") and
                (.services.lambda == "running" or .services.lambda == "available") and
                (.services.s3 == "running" or .services.s3 == "available")
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
                    echo "$health_response" | jq '.services | {ssm, lambda, s3}'
                fi
            fi
        fi
        
        echo -n "."
        sleep $retry_interval
    done
    
    error "LocalStack failed to start within the expected time."
    exit 1
}

# Create SSM parameters for configuration
function create_ssm_parameters() {
    info "Creating SSM parameters..."
    
    # Archer authentication settings
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/archer/username" --value "your_username" --type String --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/archer/password" --value "your_password" --type SecureString --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/archer/instance" --value "your_instance" --type String --overwrite
    
    # OPS Portal API settings - using --cli-input-json to avoid URL validation
    aws ${AWS_COMMON_ARGS} ssm put-parameter --cli-input-json '{"Name": "/ops-api/ops-portal/auth-url", "Value": "https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token", "Type": "String", "Overwrite": true}'
    aws ${AWS_COMMON_ARGS} ssm put-parameter --cli-input-json '{"Name": "/ops-api/ops-portal/item-url", "Value": "https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item", "Type": "String", "Overwrite": true}'
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/client-id" --value "your_client_id" --type SecureString --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/client-secret" --value "your_client_secret" --type SecureString --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/verify-ssl" --value "false" --type String --overwrite
    
    # Time log parameter (initialize with current time)
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/time-log" --value "$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")" --type String --overwrite
    
    info "SSM parameters created."
}

# Ensure the build directory exists
function ensure_build_directory() {
    local build_dir="$(dirname "$0")/build"
    mkdir -p "${build_dir}"
    echo "${build_dir}"
}

# Create a ZIP package of the OPS API code for Lambda deployment
function create_zip_package() {
    # Ensure build directory exists
    local build_dir=$(ensure_build_directory)
    local zip_path="${build_dir}/ops_api_lambda.zip"
    local temp_dir="${build_dir}/lambda_package"
    
    # Log message to stderr instead of stdout
    info "Creating ZIP package for Lambda deployment..." >&2
    
    # Create a temporary directory for the package
    rm -rf "${temp_dir}"
    mkdir -p "${temp_dir}"
    
    # Install dependencies into the temporary directory
    info "Installing dependencies..." >&2
    pip install -r requirements.txt -t "${temp_dir}" --no-cache-dir --no-user
    
    # Create a proper package structure to avoid numpy import issues
    info "Creating proper package structure..." >&2
    mkdir -p "${temp_dir}/numpy"
    touch "${temp_dir}/numpy/__init__.py"
    
    # Create a __version__ attribute for numpy to fix pandas import issue
    echo "__version__ = '1.22.0'" > "${temp_dir}/numpy/__init__.py"
    info "Added __version__ attribute to numpy package..." >&2
    
    # Copy the ops_api package to the temporary directory
    info "Copying ops_api package..." >&2
    cp -r ops_api "${temp_dir}/"
    
    # Copy the config directory to the temporary directory
    info "Copying config files..." >&2
    cp -r config "${temp_dir}/"
    
    # Create the ZIP file from the temporary directory
    info "Creating ZIP file..." >&2
    cd "${temp_dir}"
    ls -la
    echo "Current directory: $(pwd)"
    
    # Make sure the build directory exists and is writable
    mkdir -p "$(dirname "${zip_path}")"
    touch "$(dirname "${zip_path}")/.write_test" && rm "$(dirname "${zip_path}")/.write_test" || {
        error "Build directory is not writable: $(dirname "${zip_path}")" >&2
        cd - > /dev/null
        return 1
    }
    
    # Use relative path for the zip file to avoid absolute path issues
    local rel_zip_path="../$(basename "${zip_path}")"
    echo "Creating zip file at: ${rel_zip_path} (which resolves to ${zip_path})"
    
    # Create the ZIP file
    zip -r "${rel_zip_path}" .
    zip_exit_code=$?
    echo "zip command exit code: ${zip_exit_code}"
    
    # Check if the zip file was created successfully
    if [ ${zip_exit_code} -ne 0 ]; then
        error "Failed to create ZIP file: ${rel_zip_path}" >&2
        cd - > /dev/null
        return 1
    fi
    
    cd - > /dev/null
    
    # Clean up the temporary directory
    rm -rf "${temp_dir}"
    
    # Log message to stderr instead of stdout
    info "ZIP package created: ${zip_path}" >&2
    
    # Only output the zip path to stdout
    echo "${zip_path}"
}

# Create the Lambda function
function create_lambda_function() {
    local zip_path=$1
    info "Creating Lambda function: ${LAMBDA_FUNCTION_NAME}"
    
    # Create S3 bucket for Lambda code if it doesn't exist
    local bucket_name="lambda-code-bucket"
    info "Creating S3 bucket for Lambda code: ${bucket_name}"
    
    if ! aws ${AWS_COMMON_ARGS} s3api head-bucket --bucket "${bucket_name}" 2>/dev/null; then
        aws ${AWS_COMMON_ARGS} s3 mb "s3://${bucket_name}"
        info "S3 bucket created: ${bucket_name}"
    else
        info "S3 bucket already exists: ${bucket_name}"
    fi
    
    # Upload ZIP file to S3
    local s3_key="${LAMBDA_FUNCTION_NAME}.zip"
    info "Uploading Lambda code to S3: s3://${bucket_name}/${s3_key}"
    aws ${AWS_COMMON_ARGS} s3 cp "${zip_path}" "s3://${bucket_name}/${s3_key}"
    info "Lambda code uploaded to S3"
    
    # Check if the function already exists
    if aws ${AWS_COMMON_ARGS} lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" 2>/dev/null; then
        # Function exists, update it
        aws ${AWS_COMMON_ARGS} lambda update-function-code \
            --function-name "${LAMBDA_FUNCTION_NAME}" \
            --s3-bucket "${bucket_name}" \
            --s3-key "${s3_key}"
        info "Lambda function updated: ${LAMBDA_FUNCTION_NAME}"
    else
        # Function doesn't exist, create it
        aws ${AWS_COMMON_ARGS} lambda create-function \
            --function-name "${LAMBDA_FUNCTION_NAME}" \
            --runtime "python3.9" \
            --role "arn:aws:iam::000000000000:role/lambda-role" \
            --handler "lambda_handler.handler" \
            --code "{\"S3Bucket\":\"${bucket_name}\",\"S3Key\":\"${s3_key}\"}" \
            --timeout 300 \
            --memory-size 512
        info "Lambda function created: ${LAMBDA_FUNCTION_NAME}"
    fi
}

# Create a CloudWatch Events rule for scheduled execution
function create_cloudwatch_event_rule() {
    info "Creating CloudWatch Events rule: ${EVENT_RULE_NAME}"
    
    # Create the rule
    aws ${AWS_COMMON_ARGS} events put-rule \
        --name "${EVENT_RULE_NAME}" \
        --schedule-expression "rate(1 day)" \
        --state "ENABLED"
    info "CloudWatch Events rule created: ${EVENT_RULE_NAME}"
    
    # Add the Lambda function as a target
    aws ${AWS_COMMON_ARGS} events put-targets \
        --rule "${EVENT_RULE_NAME}" \
        --targets "Id=1,Arn=arn:aws:lambda:${REGION}:000000000000:function:${LAMBDA_FUNCTION_NAME}"
    info "Added Lambda function as target for CloudWatch Events rule: ${EVENT_RULE_NAME}"
    
    # Add permission for CloudWatch Events to invoke the Lambda function
    aws ${AWS_COMMON_ARGS} lambda add-permission \
        --function-name "${LAMBDA_FUNCTION_NAME}" \
        --statement-id "${EVENT_RULE_NAME}-Permission" \
        --action "lambda:InvokeFunction" \
        --principal "events.amazonaws.com" \
        --source-arn "arn:aws:events:${REGION}:000000000000:rule/${EVENT_RULE_NAME}" 2>/dev/null || true
    info "Added permission for CloudWatch Events to invoke Lambda function: ${LAMBDA_FUNCTION_NAME}"
}

# Main function
function main() {
    info "Setting up LocalStack environment for OPS API Lambda function..."
    
    # Wait for LocalStack to be ready
    wait_for_localstack
    
    # Create SSM parameters
    create_ssm_parameters
    
    # Create the Lambda function
    local zip_path=$(create_zip_package)
    create_lambda_function "${zip_path}"
    
    # Create the CloudWatch Events rule
    create_cloudwatch_event_rule
    
    info "LocalStack environment setup complete!"
    info "You can now test the Lambda function with:"
    echo "aws --endpoint-url=${ENDPOINT_URL} lambda invoke --function-name ${LAMBDA_FUNCTION_NAME} --payload '{}' response.json"
    info "Lambda package is stored at: ${zip_path}"
}

# Run the main function
main

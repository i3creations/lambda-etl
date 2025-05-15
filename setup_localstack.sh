#!/bin/bash
# LocalStack Setup Script
#
# This script sets up the LocalStack environment for local development and testing
# of the OPS API Lambda function. It creates the necessary AWS resources in the
# LocalStack environment, including:
#
# 1. S3 bucket for storing time logs
# 2. SSM parameters for configuration
# 3. Lambda function
# 4. CloudWatch Events rule for scheduled execution
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

# S3 bucket for time logs
TIME_LOG_BUCKET="ops-api-time-logs"
TIME_LOG_KEY="time_log.txt"

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
        # Check if jq is installed
        if ! command -v jq &> /dev/null; then
            warn "jq is not installed. Using grep instead."
            if curl -s "http://localhost:4566/_localstack/health" | grep -q "\"s3\": \"available\""; then
                info "LocalStack is ready!"
                return 0
            fi
        else
            # Use curl and jq to check LocalStack health
            if curl -s "http://localhost:4566/_localstack/health" | jq -e '.services.s3 == "available"' &> /dev/null; then
                info "LocalStack is ready!"
                # Display the health status
                echo "LocalStack health status:"
                curl -s "http://localhost:4566/_localstack/health" | jq
                return 0
            fi
        fi
        echo -n "."
        sleep $retry_interval
    done
    
    error "LocalStack failed to start within the expected time."
    exit 1
}

# Create an S3 bucket for storing time logs
function create_s3_bucket() {
    info "Creating S3 bucket: ${TIME_LOG_BUCKET}"
    
    # Check if bucket exists
    if aws ${AWS_COMMON_ARGS} s3api head-bucket --bucket "${TIME_LOG_BUCKET}" 2>/dev/null; then
        info "S3 bucket already exists: ${TIME_LOG_BUCKET}"
    else
        aws ${AWS_COMMON_ARGS} s3 mb "s3://${TIME_LOG_BUCKET}"
        info "S3 bucket created: ${TIME_LOG_BUCKET}"
    fi
}

# Create SSM parameters for configuration
function create_ssm_parameters() {
    info "Creating SSM parameters..."
    
    # Archer authentication settings
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/archer/username" --value "your_username" --type String --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/archer/password" --value "your_password" --type SecureString --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/archer/instance" --value "your_instance" --type String --overwrite
    
    # OPS Portal API settings
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/auth-url" --value "https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token" --type String --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/item-url" --value "https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item" --type String --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/client-id" --value "your_client_id" --type SecureString --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/client-secret" --value "your_client_secret" --type SecureString --overwrite
    aws ${AWS_COMMON_ARGS} ssm put-parameter --name "/ops-api/ops-portal/verify-ssl" --value "false" --type String --overwrite
    
    info "SSM parameters created."
}

# Create a ZIP package of the OPS API code for Lambda deployment
function create_zip_package() {
    info "Creating ZIP package for Lambda deployment..."
    
    # Create a temporary directory
    local temp_dir=$(mktemp -d)
    local zip_path="${temp_dir}/ops_api_lambda.zip"
    
    # Create the ZIP file
    cd $(dirname "$0")
    
    # Add the ops_api package
    find ops_api -name "*.py" -print | zip -@ "${zip_path}"
    
    # Add the config directory
    find config -name "*.csv" -o -name "*.ini" -print | zip -@ "${zip_path}"
    
    info "ZIP package created: ${zip_path}"
    echo "${zip_path}"
}

# Create the Lambda function
function create_lambda_function() {
    local zip_path=$1
    info "Creating Lambda function: ${LAMBDA_FUNCTION_NAME}"
    
    # Check if the function already exists
    if aws ${AWS_COMMON_ARGS} lambda get-function --function-name "${LAMBDA_FUNCTION_NAME}" 2>/dev/null; then
        # Function exists, update it
        aws ${AWS_COMMON_ARGS} lambda update-function-code \
            --function-name "${LAMBDA_FUNCTION_NAME}" \
            --zip-file "fileb://${zip_path}"
        info "Lambda function updated: ${LAMBDA_FUNCTION_NAME}"
    else
        # Function doesn't exist, create it
        aws ${AWS_COMMON_ARGS} lambda create-function \
            --function-name "${LAMBDA_FUNCTION_NAME}" \
            --runtime "python3.9" \
            --role "arn:aws:iam::000000000000:role/lambda-role" \
            --handler "ops_api.lambda_handler.handler" \
            --zip-file "fileb://${zip_path}" \
            --timeout 300 \
            --memory-size 512 \
            --environment "Variables={TIME_LOG_BUCKET=${TIME_LOG_BUCKET},TIME_LOG_KEY=${TIME_LOG_KEY}}"
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
    
    # Create the S3 bucket
    create_s3_bucket
    
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
    
    # Clean up temporary files
    rm -f "${zip_path}"
}

# Run the main function
main

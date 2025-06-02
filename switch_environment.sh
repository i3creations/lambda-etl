#!/bin/bash
# Environment Switcher Script
# This script helps switch between different environment configurations

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

function header() {
    log "SWITCH" "$1" "${BLUE}"
}

# Function to display usage
function usage() {
    echo "Usage: $0 [environment]"
    echo ""
    echo "Available environments:"
    echo "  development     - Development environment (no SSL certificate required)"
    echo "  preproduction   - Preproduction environment (SSL certificate required)"
    echo "  production      - Production environment (SSL certificate required)"
    echo ""
    echo "Examples:"
    echo "  $0 development"
    echo "  $0 preproduction"
    echo "  $0 production"
    echo ""
    echo "If no environment is specified, you will be prompted to choose."
}

# Function to validate environment
function validate_environment() {
    local env=$1
    case $env in
        development|preproduction|production)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Function to switch environment
function switch_environment() {
    local env=$1
    local env_file=".env.${env}"
    
    # Check if environment file exists
    if [ ! -f "$env_file" ]; then
        error "Environment file $env_file not found!"
        exit 1
    fi
    
    # Backup current .env if it exists
    if [ -f ".env" ]; then
        info "Backing up current .env to .env.backup"
        cp .env .env.backup
    fi
    
    # Copy environment file to .env
    info "Switching to $env environment..."
    cp "$env_file" .env
    
    # Display environment info
    header "Environment switched to: $env"
    echo ""
    
    case $env in
        development)
            info "Development Environment Configuration:"
            echo "  - No SSL certificate required"
            echo "  - Swagger UI available at: https://gii-dev.ardentmc.net/DHSOpsPortal.Api/swagger/index.html"
            echo "  - Auth URL: https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token"
            echo "  - Item URL: https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item"
            echo ""
            warn "Remember to update your ClientID and ClientSecret in .env file"
            ;;
        preproduction)
            info "Preproduction Environment Configuration:"
            echo "  - SSL certificate REQUIRED"
            echo "  - Auth URL: https://giitest-api.dhs.gov/dhsopsportal.api/api/auth/token"
            echo "  - Item URL: https://giitest-api.dhs.gov/dhsopsportal.api/api/Item"
            echo ""
            warn "Required updates in .env file:"
            echo "  - OPSAPI_OPS_PORTAL_CLIENT_ID"
            echo "  - OPSAPI_OPS_PORTAL_CLIENT_SECRET"
            echo "  - OPSAPI_OPS_PORTAL_CERT_FILE (path to SSL certificate)"
            echo "  - OPSAPI_OPS_PORTAL_KEY_FILE (path to SSL private key)"
            ;;
        production)
            info "Production Environment Configuration:"
            echo "  - SSL certificate REQUIRED"
            echo "  - Auth URL: https://gii-api.dhs.gov/dhsopsportal.api/api/auth/token"
            echo "  - Item URL: https://gii-api.dhs.gov/dhsopsportal.api/api/Item"
            echo ""
            warn "Required updates in .env file:"
            echo "  - OPSAPI_OPS_PORTAL_CLIENT_ID"
            echo "  - OPSAPI_OPS_PORTAL_CLIENT_SECRET"
            echo "  - OPSAPI_OPS_PORTAL_CERT_FILE (path to SSL certificate)"
            echo "  - OPSAPI_OPS_PORTAL_KEY_FILE (path to SSL private key)"
            ;;
    esac
    
    echo ""
    info "Next steps:"
    echo "  1. Edit .env file with your credentials"
    echo "  2. Test authentication: python tests/test_ops_portal_auth.py"
    echo "  3. Deploy: ./deploy_local.sh (development) or ./deploy_to_aws.sh (production)"
}

# Function to prompt for environment selection
function prompt_environment() {
    echo ""
    header "Select Environment"
    echo ""
    echo "1) Development (no SSL certificate required)"
    echo "2) Preproduction (SSL certificate required)"
    echo "3) Production (SSL certificate required)"
    echo ""
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            echo "development"
            ;;
        2)
            echo "preproduction"
            ;;
        3)
            echo "production"
            ;;
        *)
            error "Invalid choice. Please select 1, 2, or 3."
            exit 1
            ;;
    esac
}

# Main function
function main() {
    header "OPS API Environment Switcher"
    
    local environment=""
    
    # Check command line arguments
    if [ $# -eq 0 ]; then
        # No arguments, prompt for environment
        environment=$(prompt_environment)
    elif [ $# -eq 1 ]; then
        # One argument, validate it
        if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
            usage
            exit 0
        fi
        
        if validate_environment "$1"; then
            environment="$1"
        else
            error "Invalid environment: $1"
            echo ""
            usage
            exit 1
        fi
    else
        error "Too many arguments"
        echo ""
        usage
        exit 1
    fi
    
    # Switch to the selected environment
    switch_environment "$environment"
}

# Run the main function with command line arguments
main "$@"

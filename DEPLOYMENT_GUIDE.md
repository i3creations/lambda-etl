# OPS API Deployment Guide

This guide provides instructions for deploying and running the OPS API in different environments according to the DHS OPS Portal API requirements.

## Overview

The OPS API integrates with the DHS OPS Portal Web Application Programming Interface to create items (incidents, events, RFAs, and suspicious activities) programmatically. The implementation follows the requirements specified in `dhs_ops_portal_info.txt`.

## Environment Requirements

### Development Environment
- **Authentication**: ClientID/ClientSecret only (no SSL certificate required)
- **API Endpoint**: `https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token`
- **Item Endpoint**: `https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item`
- **Swagger UI**: Available at `https://gii-dev.ardentmc.net/DHSOpsPortal.Api/swagger/index.html`

### Preproduction Environment
- **Authentication**: ClientID/ClientSecret + SSL Certificate (REQUIRED)
- **API Endpoint**: `https://giitest-api.dhs.gov/dhsopsportal.api/api/auth/token`
- **Item Endpoint**: `https://giitest-api.dhs.gov/dhsopsportal.api/api/Item`
- **Swagger UI**: Not available

### Production Environment
- **Authentication**: ClientID/ClientSecret + SSL Certificate (REQUIRED)
- **API Endpoint**: `https://gii-api.dhs.gov/dhsopsportal.api/api/auth/token`
- **Item Endpoint**: `https://gii-api.dhs.gov/dhsopsportal.api/api/Item`
- **Swagger UI**: Not available

## Implementation Compliance

The current implementation has been updated to comply with the DHS OPS Portal API requirements:

### ✅ Fixed Issues:
1. **Authentication Payload**: Updated to use `ClientID` and `ClientSecret` (capital letters) as required
2. **SSL Certificate Support**: Added support for client certificates in preproduction and production
3. **Environment Configuration**: Created environment-specific configurations
4. **Error Handling**: Proper error handling and logging for API responses

### ✅ Key Features:
- Proper authentication flow with bearer token
- SSL certificate support for secure environments
- Environment-specific configuration management
- Comprehensive error handling and logging
- Support for both file-based and data-based certificates (for Lambda)

## Quick Start

### 1. Development Environment (Local Testing)

```bash
# Copy the development environment configuration
cp .env.development .env

# Update credentials in .env file
# Edit OPSAPI_OPS_PORTAL_CLIENT_ID and OPSAPI_OPS_PORTAL_CLIENT_SECRET

# Install dependencies
pip install -r requirements.txt

# Run locally
python -m ops_api.main

# Or test with Docker
./deploy_local.sh
```

### 2. Preproduction Environment

```bash
# Copy the preproduction environment configuration
cp .env.preproduction .env

# Update credentials and SSL certificate paths in .env file
# Required: OPSAPI_OPS_PORTAL_CLIENT_ID, OPSAPI_OPS_PORTAL_CLIENT_SECRET
# Required: OPSAPI_OPS_PORTAL_CERT_FILE, OPSAPI_OPS_PORTAL_KEY_FILE

# Deploy to AWS Lambda
./deploy_to_aws.sh
```

### 3. Production Environment

```bash
# Copy the production environment configuration
cp .env.production .env

# Update credentials and SSL certificate paths in .env file
# Required: OPSAPI_OPS_PORTAL_CLIENT_ID, OPSAPI_OPS_PORTAL_CLIENT_SECRET
# Required: OPSAPI_OPS_PORTAL_CERT_FILE, OPSAPI_OPS_PORTAL_KEY_FILE

# Deploy to AWS Lambda
./deploy_to_aws.sh
```

## Configuration

### Environment Variables

All configuration is managed through environment variables with the `OPSAPI_` prefix:

#### Required for All Environments:
- `OPSAPI_OPS_PORTAL_AUTH_URL`: Authentication endpoint URL
- `OPSAPI_OPS_PORTAL_ITEM_URL`: Item creation endpoint URL
- `OPSAPI_OPS_PORTAL_CLIENT_ID`: Client ID provided by DHS OPS Portal API team
- `OPSAPI_OPS_PORTAL_CLIENT_SECRET`: Client secret provided by DHS OPS Portal API team

#### Required for Preproduction/Production:
- `OPSAPI_OPS_PORTAL_CERT_FILE`: Path to SSL certificate file (.pem)
- `OPSAPI_OPS_PORTAL_KEY_FILE`: Path to SSL private key file (.key)

#### Alternative for Lambda (Preproduction/Production):
- `OPSAPI_OPS_PORTAL_CERT_DATA`: Base64-encoded SSL certificate data
- `OPSAPI_OPS_PORTAL_KEY_DATA`: Base64-encoded SSL private key data

### SSL Certificate Setup

#### For Local/Server Deployment:
1. Obtain SSL certificate and private key files from DHS OPS Portal API team
2. Place files in a secure location
3. Set `OPSAPI_OPS_PORTAL_CERT_FILE` and `OPSAPI_OPS_PORTAL_KEY_FILE` environment variables

#### For Lambda Deployment:
1. Convert certificate files to base64:
   ```bash
   base64 -w 0 client.pem > cert.b64
   base64 -w 0 client.key > key.b64
   ```
2. Set `OPSAPI_OPS_PORTAL_CERT_DATA` and `OPSAPI_OPS_PORTAL_KEY_DATA` environment variables

## Testing

### Test Authentication
```bash
# Test OPS Portal authentication
python tests/test_ops_portal_auth.py
```

### Test Full Pipeline
```bash
# Run with dry run mode
python -c "
from lambda_handler import handler
result = handler({'dry_run': True}, None)
print(result)
"
```

### Test in Development Environment
Use the Swagger UI interface available at:
`https://gii-dev.ardentmc.net/DHSOpsPortal.Api/swagger/index.html`

## Deployment Options

### Option 1: Local Development
- Use `deploy_local.sh` for local Docker container testing
- Suitable for development and initial testing
- No SSL certificate required

### Option 2: AWS Lambda (Recommended for Production)
- Use `deploy_to_aws.sh` for AWS Lambda deployment
- Automatic scaling and serverless execution
- Supports SSL certificates via environment variables
- CloudWatch logging and monitoring

### Option 3: Server Deployment
- Deploy directly to a server with Python environment
- Use systemd or similar for service management
- SSL certificates via file paths

## Monitoring and Logging

### CloudWatch (AWS Lambda)
- Function logs available in CloudWatch Logs
- Metrics for invocations, errors, and duration
- Custom metrics for successful/failed record submissions

### Local Logging
- Logs written to `logs/ops_api.log`
- Configurable log levels via `OPSAPI_LOGGING_LEVEL`

## Security Considerations

1. **Credentials**: Store sensitive credentials securely (AWS Secrets Manager, environment variables)
2. **SSL Certificates**: Protect certificate files with appropriate file permissions
3. **Network**: Ensure secure network connectivity to DHS endpoints
4. **Logging**: Avoid logging sensitive information (credentials, personal data)

## Troubleshooting

### Common Issues:

1. **Authentication Failed**
   - Verify ClientID and ClientSecret are correct
   - Check if SSL certificate is required for the environment
   - Ensure certificate files are accessible and valid

2. **SSL Certificate Errors**
   - Verify certificate and key files are in correct format
   - Check file permissions and paths
   - Ensure certificate is issued by DHS OPS Portal API team

3. **Network Connectivity**
   - Verify firewall rules allow outbound HTTPS connections
   - Check DNS resolution for DHS endpoints
   - Test connectivity with curl or similar tools

### Debug Mode:
Set `OPSAPI_LOGGING_LEVEL=DEBUG` for detailed logging.

## Support

For issues related to:
- **DHS OPS Portal API**: Contact DHS OPS Portal API team for credentials and certificates
- **Implementation**: Check logs and refer to this guide
- **AWS Deployment**: Refer to AWS Lambda documentation

## API Response Examples

### Successful Response:
```json
{
  "ItemId": "USCIS-0016-24"
}
```

### Error Response:
```json
[
  {
    "propertyName": "Tenant Item ID",
    "errorMessage": "Tenant Item ID/Tracking Number already exists; cannot add a duplicate Tenant ID Number",
    "attemptedValue": "SIR 123-0001"
  }
]

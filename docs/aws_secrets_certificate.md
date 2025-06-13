# Using Certificates with AWS Secrets Manager

This document provides guidance on storing and using the PKCS#12 (.pfx) certificate with AWS Secrets Manager for AWS Lambda deployments.

## Overview

When deploying the application to AWS Lambda, the certificate (`giitest-api.pfx`) should be stored in AWS Secrets Manager rather than being included in the deployment package. This approach provides several benefits:

1. **Security**: Certificates and private keys are stored securely in AWS Secrets Manager
2. **Separation of Concerns**: Sensitive credentials are kept separate from application code
3. **Rotation**: Certificates can be rotated without redeploying the application
4. **Access Control**: Fine-grained access control to the certificate using IAM policies

## Configuration

The application has been updated to support two certificate sources:

1. **File System**: Used for local development
2. **AWS Secrets Manager**: Used for AWS Lambda deployments

### Local Development

For local development, the certificate is loaded from the file system. The path to the certificate is specified in the `.env` file:

```
OPSAPI_OPS_PORTAL_CERT_PATH=certs/giitest-api.pfx
OPSAPI_OPS_PORTAL_CERT_PASSWORD=your_certificate_password
```

### AWS Lambda Deployment

For AWS Lambda deployments, the certificate is loaded from AWS Secrets Manager. The certificate is stored as a base64-encoded string in the secret.

## Storing the Certificate in AWS Secrets Manager

To store the certificate in AWS Secrets Manager:

1. **Convert the certificate to base64**:

   ```bash
   base64 -i giitest-api.pfx -o giitest-api.pfx.b64
   ```

2. **Create a secret in AWS Secrets Manager**:

   - Use the AWS Management Console or AWS CLI to create a secret
   - The secret should include the following key-value pairs:
     - `OPSAPI_OPS_PORTAL_CERT_PFX`: The base64-encoded certificate
     - `OPSAPI_OPS_PORTAL_PFX_PASSWORD`: The certificate password

   Example using AWS CLI:

   ```bash
   aws secretsmanager create-secret \
     --name opts-prod-secret \
     --description "OPS Portal API credentials for production" \
     --secret-string "{\"OPSAPI_OPS_PORTAL_AUTH_URL\":\"https://giitest-api.dhs.gov/dhsopsportal.api/api/auth/token\",\"OPSAPI_OPS_PORTAL_ITEM_URL\":\"https://giitest-api.dhs.gov/dhsopsportal.api/api/Item\",\"OPSAPI_OPS_PORTAL_CLIENT_ID\":\"your_client_id\",\"OPSAPI_OPS_PORTAL_CLIENT_SECRET\":\"your_client_secret\",\"OPSAPI_OPS_PORTAL_VERIFY_SSL\":\"true\",\"OPSAPI_OPS_PORTAL_CERT_PFX\":\"$(cat giitest-api.pfx.b64)\",\"OPSAPI_OPS_PORTAL_PFX_PASSWORD\":\"your_certificate_password\"}"
   ```

3. **Grant the Lambda function access to the secret**:

   - Ensure the Lambda execution role has the `secretsmanager:GetSecretValue` permission for the secret
   - Example IAM policy:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": "secretsmanager:GetSecretValue",
         "Resource": "arn:aws:secretsmanager:region:account-id:secret:opts-*"
       }
     ]
   }
   ```

## How It Works

The application determines the certificate source based on the environment:

1. **AWS Lambda Environment**:
   - The `load_config_from_secrets()` function is called in `lambda_handler.py`
   - This function retrieves the secret from AWS Secrets Manager
   - If the secret contains `OPSAPI_OPS_PORTAL_CERT_PFX`, it's decoded from base64 and used as the certificate data

2. **Local Development Environment**:
   - The `get_config()` function is called to load configuration from environment variables
   - The certificate path is loaded from the `OPSAPI_OPS_PORTAL_CERT_PATH` environment variable
   - The certificate is read from the file system

## Testing

A test script is provided to verify the certificate loading from both sources:

```bash
python tests/test_aws_secrets_certificate.py
```

This script tests:
1. Loading a certificate from AWS Secrets Manager (using mocks)
2. Loading a certificate from the file system

## Troubleshooting

If you encounter issues with certificate loading:

1. **Check AWS Secrets Manager**:
   - Verify the secret exists and contains the correct keys
   - Ensure the Lambda function has permission to access the secret

2. **Check the Certificate**:
   - Verify the certificate is valid and not expired
   - Ensure the certificate password is correct

3. **Check Logs**:
   - Review the Lambda function logs for any errors related to certificate loading
   - Look for messages from the `secrets_manager` and `ops_portal.api` loggers

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html)
- [AWS Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [PKCS#12 Certificate Format](https://en.wikipedia.org/wiki/PKCS_12)

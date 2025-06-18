# Incident ID Fix for Lambda ETL

This document describes the changes made to fix the issue with the incident ID not being properly saved to SSM (Systems Manager Parameter Store).

## Problem

The incident ID was not being properly saved to SSM after processing records. This was causing the system to reprocess the same records multiple times.

## Solution

The following changes were made to fix the issue:

1. Updated `src/processing/preprocess.py` to keep the 'Incident_ID' column in the processed data.
2. Enhanced `lambda_handler.py` with better logging and error handling for incident ID updates.
3. Updated the AWS client initialization in `lambda_handler.py` and `src/utils/time_utils.py` to use the correct endpoint URL when running locally.
4. Updated `src/utils/secrets_manager.py` to use the correct endpoint URL when running locally.
5. Updated `setup_localstack.sh` to create the necessary SSM parameters for incident ID tracking.
6. Created new scripts for setting up and testing the local environment.

## New Scripts

### 1. `setup_secrets.py`

This script sets up the secrets in LocalStack for local development and testing. It creates the necessary secrets in AWS Secrets Manager in the LocalStack environment.

Usage:
```bash
./setup_secrets.py [--endpoint-url ENDPOINT_URL]
```

### 2. `start_local_environment.sh`

This script starts the LocalStack environment and sets up everything needed for local development. It performs the following steps:
1. Start the LocalStack container using docker-compose
2. Wait for LocalStack to be ready
3. Set up the SSM parameters
4. Set up the secrets
5. Start the Lambda container

Usage:
```bash
./start_local_environment.sh
```

### 3. `tests/test_incident_id.py`

This test module verifies that the incident ID is being properly saved to SSM. It includes two test cases:

1. `test_incident_id_saving`: Tests the incident ID saving by invoking the Lambda function via HTTP and verifying the SSM parameter is updated correctly.
2. `test_direct_lambda_invocation`: Tests the incident ID saving by directly invoking the lambda_handler function and verifying the SSM parameter is updated correctly.

You can run the tests using pytest:
```bash
python -m pytest tests/test_incident_id.py -v
```

Or using unittest:
```bash
python -m unittest tests/test_incident_id.py
```

## Docker Compose Changes

The `docker-compose.yml` file was updated to include the following changes:
1. Added the `secretsmanager` service to the LocalStack container.
2. Added the `AWS_ENDPOINT_URL` environment variable to the Lambda container.
3. Added a dependency from the Lambda container to the LocalStack container.

## How to Test

1. Start the local environment:
```bash
./start_local_environment.sh
```

2. Run the tests to verify that the incident ID is being properly saved to SSM:
```bash
python -m pytest tests/test_incident_id.py -v
```

3. Check the logs to verify that the incident ID is being properly saved to SSM:
```bash
docker logs ops-api-lambda-container
```

## Troubleshooting

If you encounter issues with the incident ID not being saved to SSM, check the following:

1. Verify that the LocalStack container is running and healthy:
```bash
docker ps
curl http://localhost:4566/_localstack/health
```

2. Verify that the SSM parameter exists:
```bash
aws --endpoint-url=http://localhost:4566 ssm get-parameter --name "/ops-api/last-incident-id"
```

3. Check the Lambda container logs for errors:
```bash
docker logs ops-api-lambda-container
```

4. If needed, reset the SSM parameter:
```bash
aws --endpoint-url=http://localhost:4566 ssm put-parameter --name "/ops-api/last-incident-id" --value "0" --type String --overwrite
```

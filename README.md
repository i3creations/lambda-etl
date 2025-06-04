# OPS API

A Python package for syncing Significant Incident Report (SIR) data from USCIS's Archer system to the DHS OPS Portal, designed to run as an AWS Lambda function.

## Overview

This package provides functionality to:

1. Extract Significant Incident Report (SIR) data from USCIS's Archer system
2. Process and transform the data to match the DHS OPS Portal API requirements
3. Map USCIS SIR categories to corresponding DHS OPS Portal categories
4. Filter out categories that should not be sent to DHS
5. Send the transformed data to the DHS OPS Portal API
6. Run as an AWS Lambda function with scheduled execution

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd src

# Install the required dependencies
pip install uscis-opts

# Install the package
pip install -e .
```

### Using pip

```bash
# Install the USCIS Archer API library
pip install uscis-opts

# Install the OPS API package
pip install ops-api
```

## Configuration

The package uses a configuration file to store settings. By default, it looks for `config.ini` in the `config` directory. You can also specify a different configuration file using the `--config` command-line argument.

### Example Configuration

```ini
[general]
time_log_path = logs/time_log.txt

[archer]
username = your_username
password = your_password
instance = your_instance

[ops_portal]
auth_url = https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token
item_url = https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item
client_id = your_client_id
client_secret = your_client_secret
verify_ssl = false

[processing]
category_mapping_file = config/category_mappings.csv
filter_rejected = true
filter_unprocessed = true
filter_by_date = true
```

### Environment Variables

You can configure the package using environment variables in two ways:

1. **Using a .env file**: Create a `.env` file in the project root directory with environment variables in the format `OPSAPI_SECTION_KEY=value`. For example:
   ```
   OPSAPI_ARCHER_USERNAME=your_username
   OPSAPI_ARCHER_PASSWORD=your_password
   OPSAPI_ARCHER_INSTANCE=your_instance
   ```
   A `.env.example` file is provided as a template.

2. **Using system environment variables**: Set environment variables in your system in the format `OPSAPI_SECTION_KEY`. For example, `OPSAPI_ARCHER_USERNAME` would override `config['archer']['username']`.

Environment variables take precedence over values in the config.ini file.

## Usage

### Command Line

```bash
# Run with default configuration
ops-api

# Run with a specific configuration file
ops-api --config /path/to/config.ini

# Run with debug logging
ops-api --log-level DEBUG

# Run with a specific log file
ops-api --log-file /path/to/log/file.log

# Run with a specific time log file
ops-api --time-log /path/to/time_log.txt

# Run in dry-run mode (process data but don't send to OPS Portal)
ops-api --dry-run

# Run with a specific .env file
ops-api --env-file /path/to/.env
```

### Python API

```python
from src.config import get_config
from src.archer.auth import get_archer_auth
from src.processing.preprocess import preprocess
from src.ops_portal.api import send
from src.utils.time_utils import log_time

# Load configuration
config = get_config('config.ini', '.env')

# Get the last run time
last_run = log_time('time_log.txt')

# Authenticate with Archer and get SIR data
archer = get_archer_auth(config.get_section('archer'))
raw_data = archer.get_sir_data(since_date=last_run)

# Preprocess the data
processed_data = preprocess(raw_data, last_run, config.get_section('processing'))

# Send the processed data to the OPS Portal
if not processed_data.empty:
    records = processed_data.to_dict('records')
    responses = send(records, config.get_section('ops_portal'))
```

## Project Structure

```
lambda-etl/
│
├── README.md                      # Project documentation
├── setup.py                       # Package setup file
├── requirements.txt               # Dependencies
├── .gitignore                     # Git ignore file
├── lambda_handler.py              # AWS Lambda handler function
│
├── src/                           # Main package directory
│   ├── __init__.py                # Package initialization
│   ├── main.py                    # Main orchestration script
│   ├── config.py                  # Configuration management
│   │
│   ├── archer/                    # Archer integration module
│   │   ├── __init__.py
│   │   └── auth.py                # Archer authentication
│   │
│   ├── ops_portal/                # OPS Portal integration module
│   │   ├── __init__.py
│   │   └── api.py                 # OPS Portal API client
│   │
│   ├── processing/                # Data processing module
│   │   ├── __init__.py
│   │   ├── preprocess.py          # Data preprocessing
│   │   ├── field_mapping.py       # Field name mapping
│   │   ├── default_fields.py      # Default field values
│   │   └── html_stripper.py       # HTML tag stripper
│   │
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── logging_utils.py       # Logging utilities
│       ├── secrets_manager.py     # AWS Secrets Manager utilities
│       └── time_utils.py          # Time tracking utilities
│
├── config/                        # Configuration files
│   ├── config.ini                 # Main configuration file
│   ├── field_mappings.csv         # Field mappings
│   ├── category_mappings.csv      # Category mappings
│   ├── categories_to_send.csv     # Categories to send to OPS Portal
│   └── categories_not_to_send.csv # Categories NOT to send to OPS Portal
│
├── logs/                          # Log files directory
│   └── .gitkeep                   # Placeholder to include directory in git
│
└── tests/                         # Test directory
    ├── __init__.py
    ├── test_archer.py             # Tests for Archer module
    ├── test_ops_portal.py         # Tests for OPS Portal module
    ├── test_processing.py         # Tests for processing module
    ├── test_config.py             # Tests for configuration module
    ├── test_lambda_handler.py     # Tests for Lambda handler
    └── test_utils.py              # Tests for utilities
```

## AWS Lambda Function

The OPS API can be deployed as an AWS Lambda function for serverless execution. The Lambda function is configured to run on a schedule using CloudWatch Events, and it uses the following AWS services:

- **Lambda**: Executes the code in a serverless environment
- **Lambda Layers**: Manages dependencies separately from function code
- **CloudWatch Events**: Triggers the Lambda function on a schedule
- **AWS Secrets Manager**: Securely stores sensitive configuration data like credentials and API keys

### Lambda Handler

The Lambda handler function is defined in `lambda_handler.py` at the project root. It adapts the main functionality of the OPS API to run in an AWS Lambda environment.

```python
# Example event for the Lambda function
{
  "dry_run": false,
  "time": "2025-04-22T11:30:00.000000"
}
```

### Lambda Layers

The project uses Lambda Layers to manage dependencies separately from the function code. This approach offers several benefits:

1. **Reduced deployment package size**: The core function code remains small and focused on business logic
2. **Separation of concerns**: Dependencies are managed separately from function code
3. **Code reuse**: Layers can be shared across multiple Lambda functions
4. **Easier updates**: Dependencies can be updated independently of function code

The project uses three Lambda layers:

1. **Core Dependencies Layer**: Contains common libraries like requests, pytz, boto3, and aws-lambda-powertools
2. **Data Processing Layer**: Contains pandas and its dependencies
3. **Custom Code Layer**: Contains the Archer API and uscis-opts libraries

#### Creating Lambda Layers

Two scripts are provided to create Lambda layers:

1. **Using Docker (recommended)**:

```bash
./build_layers_with_docker.sh
```

This script uses Docker to build Lambda layers in an environment that matches the Lambda execution environment, ensuring compatibility.

2. **Using local Python**:

```bash
./create_layers.sh
```

This script uses your local Python environment to build Lambda layers. It's faster but may have compatibility issues if your local environment differs from the Lambda execution environment.

Both scripts create three layer ZIP files in the `build/layers` directory:
- `core-dependencies-layer.zip`
- `data-processing-layer.zip`
- `custom-code-layer.zip`

## Deployment

### AWS Lambda Docker Container for Local Development

For local development and testing, you can use the AWS Lambda Docker container to simulate the AWS Lambda environment. This approach provides a more accurate representation of the production environment compared to emulators like LocalStack.

#### Automated Setup

The easiest way to set up the AWS Lambda Docker container is to use the provided deployment script:

```bash
./deploy_local.sh
```

This script automates the entire deployment process:
1. Checks if Docker is running
2. Installs dependencies
3. Builds the package
4. Creates a Docker container with the Lambda function
5. Sets up the environment variables
6. Tests the Lambda function locally and in the Docker container

#### Manual Setup

If you prefer to set up the environment manually:

1. Install Docker and Docker Compose
2. Create a `.env` file with the required environment variables:

```bash
# Archer authentication settings
OPSAPI_ARCHER_USERNAME=your_username
OPSAPI_ARCHER_PASSWORD=your_password
OPSAPI_ARCHER_INSTANCE=Test
OPSAPI_ARCHER_URL=https://optstest.uscis.dhs.gov/

# OPS Portal API settings
OPSAPI_OPS_PORTAL_AUTH_URL=https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token
OPSAPI_OPS_PORTAL_ITEM_URL=https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item
OPSAPI_OPS_PORTAL_CLIENT_ID=test_client_id
OPSAPI_OPS_PORTAL_CLIENT_SECRET=test_client_secret
OPSAPI_OPS_PORTAL_VERIFY_SSL=false
```

3. Start the Docker container:

```bash
docker-compose up -d
```

4. Create and deploy the Lambda function package:

```bash
python setup_local.py
```

### AWS Secrets Manager Configuration

The Lambda function uses AWS Secrets Manager to securely store sensitive configuration data instead of environment variables. This provides better security and centralized secret management.

#### Setting Up Secrets

Before deploying to AWS, you need to create secrets in AWS Secrets Manager:

1. **Create secrets for each environment** (development, preproduction, production):
   - `opts-dev-secret`
   - `opts-preprod-secret`
   - `opts-prod-secret`

2. **Secret structure**: Each secret should be a JSON object containing:
   ```json
   {
     "OPSAPI_ARCHER_USERNAME": "your_archer_username",
     "OPSAPI_ARCHER_PASSWORD": "your_archer_password",
     "OPSAPI_ARCHER_INSTANCE": "your_archer_instance",
     "OPSAPI_ARCHER_URL": "https://your-archer-url.com/",
     "OPSAPI_ARCHER_VERIFY_SSL": "true",
     "OPSAPI_OPS_PORTAL_AUTH_URL": "https://your-ops-portal-auth-url/api/auth/token",
     "OPSAPI_OPS_PORTAL_ITEM_URL": "https://your-ops-portal-item-url/api/Item",
     "OPSAPI_OPS_PORTAL_CLIENT_ID": "your_client_id",
     "OPSAPI_OPS_PORTAL_CLIENT_SECRET": "your_client_secret",
     "OPSAPI_OPS_PORTAL_VERIFY_SSL": "false"
   }
   ```

3. **IAM Permissions**: The Lambda execution role needs permission to access secrets:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": ["secretsmanager:GetSecretValue"],
         "Resource": [
           "arn:aws:secretsmanager:us-east-1:*:secret:opts-dev-secret*",
           "arn:aws:secretsmanager:us-east-1:*:secret:opts-preprod-secret*",
           "arn:aws:secretsmanager:us-east-1:*:secret:opts-prod-secret*"
         ]
       }
     ]
   }
   ```

For detailed setup instructions, see [SECRETS_MANAGER_SETUP.md](SECRETS_MANAGER_SETUP.md).

### AWS Deployment

To deploy the Lambda function to AWS:

```bash
./deploy_to_aws.sh
```

This script:
1. Checks if AWS CLI is installed and configured
2. Prompts for AWS region, Lambda function name, and execution role ARN
3. Builds the package and creates Lambda layers
4. Deploys the layers and Lambda function to AWS
5. Sets up CloudWatch Events for scheduled execution
6. Configures the Lambda function to use AWS Secrets Manager

You'll need to provide:
- AWS credentials with appropriate permissions
- Lambda execution role ARN with Secrets Manager permissions
- Pre-configured secrets in AWS Secrets Manager

### Testing

You can test the Lambda function locally in two ways:

1. **Direct invocation**:

```bash
python test_lambda_local.py
```

2. **Using the Docker container**:

```bash
python test_lambda_container.py
```

You can also invoke the Lambda function using curl:

```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"dry_run": true}'
```

## Testing

The project includes a comprehensive test suite using pytest. Tests cover all major components including authentication, data processing, configuration management, and Lambda function handling.

### Running Tests

#### Prerequisites

Ensure you have pytest installed:

```bash
# Install pytest if not already available
pip install pytest

# Optional: Install pytest-cov for coverage reports
pip install pytest-cov
```

#### Basic Test Execution

```bash
# Run all tests
python -m pytest tests/

# Run tests with verbose output
python -m pytest tests/ -v

# Run tests for a specific module
python -m pytest tests/test_utils.py -v
python -m pytest tests/test_processing.py -v
python -m pytest tests/test_config.py -v
```

#### Test Coverage

```bash
# Run tests with coverage report
python -m pytest tests/ --cov=src

# Generate HTML coverage report
python -m pytest tests/ --cov=src --cov-report=html

# Generate coverage report with missing lines
python -m pytest tests/ --cov=src --cov-report=term-missing
```

#### Running Specific Test Categories

```bash
# Run unit tests (excluding integration tests that require network)
python -m pytest tests/ -k "not test_archer_auth and not test_ops_portal_auth"

# Run only configuration tests
python -m pytest tests/test_config.py

# Run only processing tests
python -m pytest tests/test_processing.py

# Run only utility tests
python -m pytest tests/test_utils.py

# Run Lambda handler tests
python -m pytest tests/test_lambda_handler.py
```

#### Test Environment Setup

Some tests require environment variables to be set. Create a `.env` file for testing:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with test credentials (use test/mock values)
# Note: Integration tests may fail without valid credentials
```

#### Test Structure

The test suite is organized as follows:

- `tests/test_archer.py` - Archer API authentication and data retrieval tests
- `tests/test_archer_auth.py` - Integration tests for Archer authentication
- `tests/test_config.py` - Configuration management tests
- `tests/test_data_structure.py` - Data structure validation tests
- `tests/test_lambda_handler.py` - AWS Lambda function handler tests
- `tests/test_lambda_container.py` - Docker container tests for Lambda
- `tests/test_lambda_local.py` - Local Lambda execution tests
- `tests/test_ops_portal.py` - OPS Portal API client tests
- `tests/test_ops_portal_auth.py` - Integration tests for OPS Portal authentication
- `tests/test_processing.py` - Data processing and transformation tests
- `tests/test_utils.py` - Utility function tests

#### Test Output

A successful test run will show output similar to:

```
================================= test session starts =================================
platform linux -- Python 3.12.9, pytest-8.3.5
cachedir: .pytest_cache
rootdir: /workspace/lambda-etl
collected 82 items

tests/test_config.py ................                                    [ 19%]
tests/test_processing.py ............                                    [ 34%]
tests/test_utils.py .........                                            [ 45%]
tests/test_lambda_handler.py ...............                             [ 63%]
...

================= 80 passed, 2 failed, 2 warnings in 121.66s ==================
```

#### Troubleshooting Test Failures

**Network-related test failures:**
- Tests like `test_archer_auth` and `test_ops_portal_auth` require network connectivity
- These may fail in isolated environments or with invalid credentials
- Use the `-k` flag to exclude these tests if needed

**Environment variable issues:**
- Ensure `.env` file is properly configured
- Check that all required environment variables are set
- Use `.env.example` as a template

**Dependency issues:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Install test dependencies: `pip install pytest pytest-cov`

#### Continuous Integration

The test suite is designed to run in CI/CD environments. For automated testing:

```bash
# Run tests suitable for CI (excluding integration tests)
python -m pytest tests/ -k "not test_archer_auth and not test_ops_portal_auth" --tb=short
```

## Dependencies

- pandas>=1.0.0
- numpy>=1.18.0
- requests>=2.22.0
- pytz>=2019.3
- uscis-opts>=0.1.4 (USCIS Archer API library)
- python-dotenv>=0.19.0
- boto3>=1.18.0
- aws-lambda-powertools>=1.25.0

### Development Dependencies

- pytest>=8.0.0 (for running tests)
- pytest-cov (for test coverage reports)

## License

This project is licensed under the terms of the license included in the repository.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

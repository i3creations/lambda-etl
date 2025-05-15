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
cd ops_api

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
from ops_api.config import get_config
from ops_api.archer.auth import get_archer_auth
from ops_api.processing.preprocess import preprocess
from ops_api.ops_portal.api import send
from ops_api.utils.time_utils import log_time

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
ops_api/
│
├── README.md                      # Project documentation
├── setup.py                       # Package setup file
├── requirements.txt               # Dependencies
├── .gitignore                     # Git ignore file
│
├── ops_api/                       # Main package directory
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
    └── test_utils.py              # Tests for utilities
```

## AWS Lambda Function

The OPS API can be deployed as an AWS Lambda function for serverless execution. The Lambda function is configured to run on a schedule using CloudWatch Events, and it uses the following AWS services:

- **Lambda**: Executes the code in a serverless environment
- **CloudWatch Events**: Triggers the Lambda function on a schedule
- **S3**: Stores the time log file to track the last run time
- **SSM Parameter Store**: Stores configuration parameters securely

### Lambda Handler

The Lambda handler function is defined in `ops_api/lambda_handler.py`. It adapts the main functionality of the OPS API to run in an AWS Lambda environment.

```python
# Example event for the Lambda function
{
  "dry_run": false,
  "time": "2025-04-22T11:30:00.000000"
}
```

## LocalStack Development Environment

For local development and testing, you can use LocalStack to emulate AWS services. This allows you to test the Lambda function without deploying to AWS.

### Setup

#### Automated Setup

The easiest way to set up the LocalStack environment is to use the provided deployment script:

```bash
cd ops_api
./deploy_localstack.sh
```

This script automates the entire deployment process:
1. Checks if Docker is running
2. Installs dependencies
3. Builds the package
4. Starts LocalStack
5. Sets up the LocalStack environment
6. Tests the Lambda function locally and in LocalStack

#### Manual Setup

If you prefer to set up the environment manually:

1. Install Docker and Docker Compose
2. Start the LocalStack container:

```bash
cd ops_api
docker compose up -d
```

3. Set up the LocalStack environment:

```bash
./setup_localstack.sh
```

This script creates the necessary AWS resources in the LocalStack environment, including:
- S3 bucket for storing time logs
- SSM parameters for configuration
- Lambda function
- CloudWatch Events rule for scheduled execution

### Testing

You can test the Lambda function locally in two ways:

1. **Direct invocation**:

```bash
python test_lambda_local.py
```

2. **Using LocalStack**:

```bash
python test_lambda_localstack.py
```

You can also invoke the Lambda function using the AWS CLI:

```bash
aws --endpoint-url=http://localhost:4566 lambda invoke \
  --function-name ops-api-lambda \
  --payload '{"dry_run": true}' \
  response.json
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

## License

This project is licensed under the terms of the license included in the repository.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

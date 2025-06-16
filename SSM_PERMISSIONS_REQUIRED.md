# AWS Systems Manager Permissions Required

## Overview

The Lambda function now uses AWS Systems Manager Parameter Store to persist both the last run time and the last incident ID between executions. This ensures that these values are properly maintained across Lambda invocations.

## Required IAM Permissions

The Lambda execution role needs the following additional permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "ssm:PutParameter"
            ],
            "Resource": [
                "arn:aws:ssm:*:*:parameter/ops-api/last-run-time",
                "arn:aws:ssm:*:*:parameter/ops-api/last-incident-id"
            ]
        }
    ]
}
```

## Parameter Details

### Last Run Time
- **Parameter Name**: `/ops-api/last-run-time`
- **Type**: String
- **Description**: Last run time for OPS API Lambda function in US/Eastern timezone
- **Format**: ISO 8601 format with timezone offset (e.g., `2025-06-05T15:46:12.123456-04:00`)

### Last Incident ID
- **Parameter Name**: `/ops-api/last-incident-id`
- **Type**: String
- **Description**: Last processed incident ID for OPS API Lambda function
- **Format**: Integer stored as string (e.g., `742181`)

## Changes Made

1. **Fixed Timezone Bug**: The Lambda handler now consistently uses US/Eastern timezone instead of UTC
2. **Added Persistent Storage**: Last run time and last incident ID are now stored in AWS Systems Manager Parameter Store
3. **Improved Logging**: Better log messages for first-run scenarios and SSM operations

## Expected Log Output

### Last Run Time

#### First Run (No Parameter Exists)
```json
{
    "level": "INFO",
    "message": "No previous run time found in SSM. Using current US/Eastern time: 2025-06-05 15:46:12.123456-04:00"
}
```

#### Subsequent Runs
```json
{
    "level": "INFO", 
    "message": "Retrieved last run time from SSM: 2025-06-05 15:46:12.123456-04:00"
}
```

#### Update Operation
```json
{
    "level": "INFO",
    "message": "Updated last run time in SSM: 2025-06-05T15:46:12.123456-04:00"
}
```

### Last Incident ID

#### First Run (No Parameter Exists)
```json
{
    "level": "INFO",
    "message": "No previous incident ID found in SSM. Starting from 0"
}
```

#### Subsequent Runs
```json
{
    "level": "INFO", 
    "message": "Retrieved last incident ID from SSM: 742181"
}
```

#### Update Operation
```json
{
    "level": "INFO",
    "message": "Updated last incident ID in SSM: 742181"
}
```

## Deployment Notes

1. Ensure the Lambda execution role has the required SSM permissions for both parameters
2. The parameters will be created automatically on first run
3. All timestamps are stored in US/Eastern timezone with proper timezone offset information
4. The last incident ID is stored as a string but represents an integer value

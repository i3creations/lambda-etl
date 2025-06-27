# DateTime Filtering Implementation

This document describes the changes made to implement datetime filtering in the OPS API Lambda function.

## Overview

The OPS API Lambda function has been updated to filter records based on the `Date_Time_SIR_Processed` field and `Submission_Status_1` field, rather than using the `Incident_ID` field. This change allows for more accurate filtering of records that have been assigned for further action since the last run time.

## Changes Made

1. **Lambda Handler**
   - Updated to use `get_last_run_time_from_ssm` and `update_last_run_time_in_ssm` instead of the incident ID functions
   - Modified to pass the last run time to the Archer API for filtering records

2. **Archer Authentication**
   - Added a new `since_date` parameter to the `get_sir_data` method
   - Implemented a new `_filter_records_by_date` method to filter records based on the `Date_Time_SIR_Processed` field
   - Added a `_parse_datetime` method to handle various datetime formats

3. **Preprocessing**
   - Updated the `preprocess` function to filter records based on the `Date_Time_SIR_Processed` field and `Submission_Status_1` field
   - Added fallback to `Date_SIR_Processed__NT` if `Date_Time_SIR_Processed` is not available

4. **Tests**
   - Added new tests for datetime filtering in `tests/test_datetime_filtering.py`
   - Updated existing tests to use datetime objects instead of incident IDs

## Configuration

The datetime filtering can be enabled or disabled using the `filter_by_datetime` configuration option:

```python
config = {
    'category_mapping_file': 'config/category_mappings.csv',
    'filter_rejected': True,
    'filter_unprocessed': True,
    'filter_by_datetime': True  # Set to False to disable datetime filtering
}
```

## How It Works

1. The Lambda function retrieves the last run time from SSM Parameter Store
2. The Archer API is called with the last run time to retrieve records
3. Records are filtered based on the following criteria:
   - `Date_Time_SIR_Processed` > last run time
   - `Submission_Status_1` = 'Assigned for Further Action'
4. The filtered records are processed and sent to the OPS Portal
5. The current time is saved to SSM Parameter Store as the new last run time

## Fallback Mechanism

If the `Date_Time_SIR_Processed` field is not available in a record, the system will fall back to using the `Date_SIR_Processed__NT` field for filtering. This ensures backward compatibility with older records.

## Testing

The datetime filtering functionality can be tested using the new test file `tests/test_datetime_filtering.py`. This file contains tests for:

- Filtering records based on the `Date_Time_SIR_Processed` field
- Filtering records based on the `Submission_Status_1` field
- Falling back to `Date_SIR_Processed__NT` when `Date_Time_SIR_Processed` is not available

To run the tests:

```bash
python -m pytest tests/test_datetime_filtering.py -v
```

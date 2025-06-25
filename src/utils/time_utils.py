"""
Time Utilities Module

This module provides utilities for tracking and managing time-related operations,
particularly for logging the last run time of the script.
"""

import os
import pytz
import boto3
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union


def log_time(log_file_path=None) -> datetime:
    """
    Log the current time and return the previous logged time.
    
    This function reads the previous timestamp from a log file, updates the file
    with the current timestamp, and returns the previous timestamp. This is useful
    for tracking when the script was last run.
    
    Args:
        log_file_path (str, optional): Path to the log file. If None, defaults to 'time_log.txt'
            in the current working directory.
            
    Returns:
        datetime: The previous logged time as a datetime object
        
    Raises:
        FileNotFoundError: If the log file doesn't exist
        ValueError: If the log file contains an invalid timestamp format
    """
    # Set default log file path if not provided
    if log_file_path is None:
        log_file_path = 'time_log.txt'
    
    # Ensure the directory exists
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set timezone and datetime format
    tz = pytz.timezone('US/Eastern')
    fmt = '%Y-%m-%dT%H:%M:%S%z'
    
    # Get current time
    current_time = datetime.now(pytz.UTC).astimezone(tz)
    
    try:
        # Read previous time and update the log file
        with open(log_file_path, 'r+') as file:
            previous_time = datetime.strptime(file.read().strip(), fmt)
            file.seek(0)
            file.write(current_time.strftime(fmt))
            file.truncate()
    except FileNotFoundError:
        # If the file doesn't exist, create it and use current time as previous time
        with open(log_file_path, 'w') as file:
            file.write(current_time.strftime(fmt))
        previous_time = current_time
    
    return previous_time


def get_current_time(timezone_str='US/Eastern') -> datetime:
    """
    Get the current time in the specified timezone.
    
    Args:
        timezone_str (str, optional): Timezone string. Defaults to 'US/Eastern'.
        
    Returns:
        datetime: Current time as a datetime object with timezone information
    """
    tz = pytz.timezone(timezone_str)
    return datetime.now(pytz.UTC).astimezone(tz)


def format_datetime(dt, fmt='%Y-%m-%dT%H:%M:%S%z') -> str:
    """
    Format a datetime object as a string.
    
    Args:
        dt (datetime): Datetime object to format
        fmt (str, optional): Format string. Defaults to '%Y-%m-%dT%H:%M:%S%z'.
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime(fmt)


def get_last_run_time(log_file_path=None) -> datetime:
    """
    Get the last run time from a log file without updating it.
    
    This function is useful for AWS Lambda functions where we want to read
    the last run time but update it only after successful execution.
    
    Args:
        log_file_path (str, optional): Path to the log file. If None, defaults to 'time_log.txt'
            in the current working directory.
            
    Returns:
        datetime: The last logged time as a datetime object
    """
    # Set default log file path if not provided
    if log_file_path is None:
        log_file_path = 'time_log.txt'
    
    # Set timezone and datetime format
    tz = pytz.timezone('US/Eastern')
    fmt = '%Y-%m-%dT%H:%M:%S%z'
    
    # Get current time as fallback
    current_time = datetime.now(pytz.UTC).astimezone(tz)
    
    try:
        # Read previous time from the log file
        with open(log_file_path, 'r') as file:
            previous_time = datetime.strptime(file.read().strip(), fmt)
            return previous_time
    except (FileNotFoundError, ValueError):
        # If the file doesn't exist or has invalid format, return current time
        return current_time


def update_last_run_time(log_file_path=None, timestamp=None) -> None:
    """
    Update the last run time in a log file.
    
    This function is useful for AWS Lambda functions where we want to update
    the last run time only after successful execution.
    
    Args:
        log_file_path (str, optional): Path to the log file. If None, defaults to 'time_log.txt'
            in the current working directory.
        timestamp (datetime, optional): Timestamp to write to the log file. If None, uses current time.
    """
    # Set default log file path if not provided
    if log_file_path is None:
        log_file_path = 'time_log.txt'
    
    # Ensure the directory exists
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Set timezone and datetime format
    tz = pytz.timezone('US/Eastern')
    fmt = '%Y-%m-%dT%H:%M:%S%z'
    
    # Get current time if timestamp not provided
    if timestamp is None:
        timestamp = datetime.now(pytz.UTC).astimezone(tz)
    elif timestamp.tzinfo is None:
        timestamp = tz.localize(timestamp)
    
    # Update the log file
    with open(log_file_path, 'w') as file:
        file.write(timestamp.strftime(fmt))


def get_last_run_time_from_ssm() -> datetime:
    """
    Get the last run time from AWS Systems Manager Parameter Store.
    
    This function retrieves the last run time from the SSM Parameter Store,
    which is used to track when the Lambda function was last executed.
    
    Returns:
        datetime: Last run time as a datetime object with timezone information,
                 or current time if parameter doesn't exist or there's an error
    """
    try:
        # Import logger here to avoid circular imports
        from ..utils.logging_utils import get_logger
        logger = get_logger('time_utils')
        
        # Get endpoint URL from environment variable if running locally
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        
        # Create SSM client with endpoint URL if provided
        if endpoint_url:
            ssm = boto3.client('ssm', endpoint_url=endpoint_url)
        else:
            ssm = boto3.client('ssm')
            
        parameter_name = '/ops-api/last-run-time'
        
        try:
            response = ssm.get_parameter(Name=parameter_name)
            time_str = response['Parameter']['Value']
            
            # Parse the datetime with timezone information
            last_time = datetime.fromisoformat(time_str)
            
            logger.info(f"Retrieved last run time from SSM: {last_time}")
            return last_time
            
        except ssm.exceptions.ParameterNotFound:
            # Parameter doesn't exist yet, this is normal for first run
            current_time = get_current_time()
            logger.info(f"No previous run time found in SSM. Using current US/Eastern time: {current_time}")
            return current_time
            
    except Exception as e:
        # Import logger here to avoid circular imports
        from ..utils.logging_utils import get_logger
        logger = get_logger('time_utils')
        
        logger.warning(f"Error getting last run time from SSM: {str(e)}. Using current time.")
        return get_current_time()


def update_last_run_time_in_ssm(timestamp: Optional[datetime] = None) -> None:
    """
    Update the last run time in AWS Systems Manager Parameter Store.
    
    This function updates the last run time in the SSM Parameter Store,
    which is used to track when the Lambda function was last executed.
    
    Args:
        timestamp (datetime, optional): Timestamp to save. If None, uses current time.
    """
    try:
        # Import logger here to avoid circular imports
        from ..utils.logging_utils import get_logger
        logger = get_logger('time_utils')
        
        if timestamp is None:
            timestamp = get_current_time()
        elif timestamp.tzinfo is None:
            # Ensure timestamp has timezone information
            eastern_tz = pytz.timezone('US/Eastern')
            timestamp = eastern_tz.localize(timestamp)
        
        # Format the timestamp as ISO 8601 string
        time_str = timestamp.isoformat()
        
        # Get endpoint URL from environment variable if running locally
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        
        # Create SSM client with endpoint URL if provided
        if endpoint_url:
            ssm = boto3.client('ssm', endpoint_url=endpoint_url)
        else:
            ssm = boto3.client('ssm')
            
        parameter_name = '/ops-api/last-run-time'
        
        ssm.put_parameter(
            Name=parameter_name,
            Value=time_str,
            Type='String',
            Overwrite=True,
            Description='Last run time for OPS API Lambda function in US/Eastern timezone'
        )
        
        logger.info(f"Updated last run time in SSM: {time_str}")
        
    except Exception as e:
        # Import logger here to avoid circular imports
        from ..utils.logging_utils import get_logger
        logger = get_logger('time_utils')
        
        logger.error(f"Error updating last run time in SSM: {str(e)}")
        raise



def format_datetime_for_api(dt_series: Union[pd.Series, datetime], field_name: str = "datetime") -> Union[pd.Series, str]:
    """
    Format datetime values for API consumption.
    
    This function handles datetime conversion for API requests, ensuring proper timezone
    handling and formatting to the expected format: "2025-06-25T14:58:17.424Z"
    - If the datetime has a timezone, it's converted to UTC
    - If the datetime has no timezone info, it's assumed to be in UTC
    - The result is formatted with exactly 3 decimal places for milliseconds and a 'Z' suffix
    
    Args:
        dt_series (Union[pd.Series, datetime]): A pandas Series of datetime values or a single datetime object
        field_name (str, optional): Name of the field being processed. Defaults to "datetime".
            
    Returns:
        Union[pd.Series, str]: Formatted datetime string(s) ready for API consumption
    """
    # Handle single datetime object
    if isinstance(dt_series, datetime):
        # If datetime has no timezone info, assume it's UTC
        if dt_series.tzinfo is None:
            dt = dt_series.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if it has a different timezone
            dt = dt_series.astimezone(timezone.utc)
            
        # Format with exactly 3 decimal places for milliseconds and 'Z' suffix
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    
    # Handle pandas Series
    elif isinstance(dt_series, pd.Series):
        def convert_datetime(dt):
            if pd.isna(dt):
                return None
                
            # Convert pandas Timestamp to datetime if needed
            if isinstance(dt, pd.Timestamp):
                dt = dt.to_pydatetime()
                
            # If datetime has no timezone info, assume it's UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC if it has a different timezone
                dt = dt.astimezone(timezone.utc)
                
            # Format with exactly 3 decimal places for milliseconds and 'Z' suffix
            return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        # Apply conversion to each element in the series
        return dt_series.apply(convert_datetime)
    
    else:
        raise TypeError(f"Expected datetime or pandas Series, got {type(dt_series).__name__}")

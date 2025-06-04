"""
Time Utilities Module

This module provides utilities for tracking and managing time-related operations,
particularly for logging the last run time of the script.
"""

import os
import pytz
from datetime import datetime
from pathlib import Path


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
    current_time = tz.localize(datetime.now())
    
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
    return tz.localize(datetime.now())


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
    current_time = tz.localize(datetime.now())
    
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
        timestamp = tz.localize(datetime.now())
    elif timestamp.tzinfo is None:
        timestamp = tz.localize(timestamp)
    
    # Update the log file
    with open(log_file_path, 'w') as file:
        file.write(timestamp.strftime(fmt))

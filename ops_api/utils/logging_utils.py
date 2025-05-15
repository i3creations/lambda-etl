"""
Logging Utilities Module

This module provides utilities for setting up and managing logging throughout the application.
"""

import os
import logging
from datetime import datetime
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_file=None, log_format=None):
    """
    Set up logging configuration for the application.
    
    Args:
        log_level (int, optional): Logging level. Defaults to logging.INFO.
        log_file (str, optional): Path to the log file. If None, logs will only be output to console.
        log_format (str, optional): Log message format. If None, uses a default format.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Set default log format if not provided
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure basic logging
    logging_config = {
        'level': log_level,
        'format': log_format,
    }
    
    # Add file handler if log_file is provided
    if log_file:
        # Ensure the log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Add file handler configuration
        logging_config['filename'] = log_file
        logging_config['filemode'] = 'a'  # Append to the log file
    
    # Apply the configuration
    logging.basicConfig(**logging_config)
    
    # Create and return a logger for the application
    logger = logging.getLogger('ops_api')
    
    return logger


def get_logger(name=None):
    """
    Get a logger instance.
    
    Args:
        name (str, optional): Name of the logger. If None, returns the root logger.
        
    Returns:
        logging.Logger: Logger instance
    """
    if name is None:
        return logging.getLogger('ops_api')
    else:
        return logging.getLogger(f'ops_api.{name}')


def log_exception(logger, exception, message=None):
    """
    Log an exception with an optional custom message.
    
    Args:
        logger (logging.Logger): Logger instance
        exception (Exception): The exception to log
        message (str, optional): Custom message to include with the exception
    """
    if message:
        logger.exception(f"{message}: {str(exception)}")
    else:
        logger.exception(str(exception))

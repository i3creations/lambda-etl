"""
Logging Utilities Module

This module provides utilities for setting up and managing logging throughout the application.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


def get_logging_level_from_env() -> int:
    """
    Get the logging level from the OPSAPI_LOGGING_LEVEL environment variable.
    
    Returns:
        int: Logging level constant from the logging module (e.g., logging.INFO, logging.DEBUG)
    """
    log_level_str = os.environ.get('OPSAPI_LOGGING_LEVEL', 'INFO').upper()
    return _convert_log_level_str_to_int(log_level_str)


def get_logging_level_from_config(config: Dict[str, Any]) -> Optional[int]:
    """
    Get the logging level from a configuration dictionary.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary, potentially from AWS Secrets Manager
        
    Returns:
        Optional[int]: Logging level constant from the logging module, or None if not found
    """
    if not config or 'logging' not in config or 'level' not in config['logging']:
        return None
    
    log_level_str = config['logging']['level'].upper()
    return _convert_log_level_str_to_int(log_level_str)


def _convert_log_level_str_to_int(log_level_str: str) -> int:
    """
    Convert a string log level to the corresponding logging module constant.
    
    Args:
        log_level_str (str): String representation of log level (e.g., 'DEBUG', 'INFO')
        
    Returns:
        int: Logging level constant from the logging module
    """
    # Map string log levels to logging module constants
    log_levels = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    # Return the corresponding log level, default to INFO if not found
    return log_levels.get(log_level_str, logging.INFO)


def setup_logging(log_level=None, log_file=None, log_format=None, config=None):
    """
    Set up logging configuration for the application.
    
    Args:
        log_level (int, optional): Logging level. If None, uses environment variable or config.
        log_file (str, optional): Path to the log file. If None, uses environment variable or config.
        log_format (str, optional): Log message format. If None, uses a default format.
        config (Dict[str, Any], optional): Configuration dictionary, potentially from AWS Secrets Manager.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Determine the log level (priority: parameter > config > environment variable > default)
    if log_level is None:
        if config:
            log_level = get_logging_level_from_config(config)
        
        if log_level is None:
            log_level = get_logging_level_from_env()
    
    # Determine the log file (priority: parameter > config > environment variable)
    if log_file is None:
        if config and 'logging' in config and 'file' in config['logging']:
            log_file = config['logging']['file']
        
        if not log_file:
            log_file = os.environ.get('OPSAPI_LOGGING_FILE')
    
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
    logger = logging.getLogger('src')
    
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
        return logging.getLogger('src')
    else:
        return logging.getLogger(f'src.{name}')


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

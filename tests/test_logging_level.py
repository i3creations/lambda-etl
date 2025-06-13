"""
Test Logging Level Module

This module tests the logging level functionality to ensure that the OPSAPI_LOGGING_LEVEL
environment variable is being used correctly.
"""

import os
import logging
import unittest
from unittest.mock import patch, MagicMock

from src.utils.logging_utils import (
    get_logging_level_from_env,
    get_logging_level_from_config,
    _convert_log_level_str_to_int,
    setup_logging
)


class TestLoggingLevel(unittest.TestCase):
    """Test the logging level functionality."""
    
    def test_convert_log_level_str_to_int(self):
        """Test converting string log levels to logging module constants."""
        self.assertEqual(_convert_log_level_str_to_int('DEBUG'), logging.DEBUG)
        self.assertEqual(_convert_log_level_str_to_int('INFO'), logging.INFO)
        self.assertEqual(_convert_log_level_str_to_int('WARNING'), logging.WARNING)
        self.assertEqual(_convert_log_level_str_to_int('ERROR'), logging.ERROR)
        self.assertEqual(_convert_log_level_str_to_int('CRITICAL'), logging.CRITICAL)
        # Test default case
        self.assertEqual(_convert_log_level_str_to_int('UNKNOWN'), logging.INFO)
    
    @patch.dict(os.environ, {'OPSAPI_LOGGING_LEVEL': 'DEBUG'})
    def test_get_logging_level_from_env(self):
        """Test getting the logging level from environment variables."""
        self.assertEqual(get_logging_level_from_env(), logging.DEBUG)
    
    @patch.dict(os.environ, {'OPSAPI_LOGGING_LEVEL': 'ERROR'})
    def test_get_logging_level_from_env_error(self):
        """Test getting the ERROR logging level from environment variables."""
        self.assertEqual(get_logging_level_from_env(), logging.ERROR)
    
    @patch.dict(os.environ, {})
    def test_get_logging_level_from_env_default(self):
        """Test getting the default logging level when environment variable is not set."""
        self.assertEqual(get_logging_level_from_env(), logging.INFO)
    
    def test_get_logging_level_from_config(self):
        """Test getting the logging level from a configuration dictionary."""
        config = {'logging': {'level': 'DEBUG'}}
        self.assertEqual(get_logging_level_from_config(config), logging.DEBUG)
    
    def test_get_logging_level_from_config_missing(self):
        """Test getting the logging level from a configuration dictionary with missing keys."""
        self.assertIsNone(get_logging_level_from_config({}))
        self.assertIsNone(get_logging_level_from_config({'logging': {}}))
    
    @patch('logging.basicConfig')
    @patch('src.utils.logging_utils.get_logging_level_from_env')
    def test_setup_logging_with_env(self, mock_get_level, mock_basic_config):
        """Test setting up logging with environment variables."""
        mock_get_level.return_value = logging.DEBUG
        
        logger = setup_logging()
        
        mock_get_level.assert_called_once()
        mock_basic_config.assert_called_once_with(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @patch('logging.basicConfig')
    def test_setup_logging_with_config(self, mock_basic_config):
        """Test setting up logging with a configuration dictionary."""
        config = {'logging': {'level': 'ERROR'}}
        
        logger = setup_logging(config=config)
        
        mock_basic_config.assert_called_once_with(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @patch('logging.basicConfig')
    @patch('src.utils.logging_utils.get_logging_level_from_env')
    def test_setup_logging_priority(self, mock_get_level, mock_basic_config):
        """Test the priority of logging level sources."""
        mock_get_level.return_value = logging.INFO
        
        # 1. Explicit log_level parameter should have highest priority
        logger = setup_logging(log_level=logging.DEBUG, config={'logging': {'level': 'ERROR'}})
        mock_basic_config.assert_called_with(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        mock_basic_config.reset_mock()
        
        # 2. Config should have second priority
        logger = setup_logging(config={'logging': {'level': 'ERROR'}})
        mock_basic_config.assert_called_with(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        mock_basic_config.reset_mock()
        
        # 3. Environment variable should have third priority
        logger = setup_logging()
        mock_get_level.assert_called()
        mock_basic_config.assert_called_with(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


if __name__ == '__main__':
    unittest.main()

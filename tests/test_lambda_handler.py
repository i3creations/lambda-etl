"""
Unit tests for the lambda_handler module.
"""

import pytest
import json
import os
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
from ops_api.lambda_handler import (
    get_env_variable, 
    load_config_from_env, 
    get_time_log_from_env, 
    update_time_log_in_env,
    handler
)


class TestLambdaHandler:
    """Test cases for the lambda_handler module."""

    def test_get_env_variable_success(self):
        """Test successful retrieval of environment variable."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = get_env_variable('TEST_VAR')
            assert result == 'test_value'

    def test_get_env_variable_with_default(self):
        """Test retrieval of environment variable with default value."""
        result = get_env_variable('NONEXISTENT_VAR', 'default_value')
        assert result == 'default_value'

    def test_get_env_variable_missing_no_default(self):
        """Test retrieval of missing environment variable without default."""
        with pytest.raises(ValueError, match="Environment variable NONEXISTENT_VAR is not set"):
            get_env_variable('NONEXISTENT_VAR')

    def test_load_config_from_env_success(self):
        """Test successful loading of configuration from environment variables."""
        env_vars = {
            'OPSAPI_ARCHER_USERNAME': 'test_user',
            'OPSAPI_ARCHER_PASSWORD': 'test_pass',
            'OPSAPI_ARCHER_INSTANCE': 'test_instance',
            'OPSAPI_OPS_PORTAL_AUTH_URL': 'https://auth.test.com',
            'OPSAPI_OPS_PORTAL_ITEM_URL': 'https://item.test.com',
            'OPSAPI_OPS_PORTAL_CLIENT_ID': 'test_client_id',
            'OPSAPI_OPS_PORTAL_CLIENT_SECRET': 'test_client_secret',
            'OPSAPI_OPS_PORTAL_VERIFY_SSL': 'true'
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config_from_env()
            
            # Check archer configuration
            assert config['archer']['username'] == 'test_user'
            assert config['archer']['password'] == 'test_pass'
            assert config['archer']['instance'] == 'test_instance'
            
            # Check ops_portal configuration
            assert config['ops_portal']['auth_url'] == 'https://auth.test.com'
            assert config['ops_portal']['item_url'] == 'https://item.test.com'
            assert config['ops_portal']['client_id'] == 'test_client_id'
            assert config['ops_portal']['client_secret'] == 'test_client_secret'
            assert config['ops_portal']['verify_ssl'] == True
            
            # Check processing configuration
            assert 'processing' in config
            assert config['processing']['category_mapping_file'] == 'config/category_mappings.csv'

    def test_load_config_from_env_ssl_false(self):
        """Test loading configuration with SSL verification disabled."""
        env_vars = {
            'OPSAPI_ARCHER_USERNAME': 'test_user',
            'OPSAPI_ARCHER_PASSWORD': 'test_pass',
            'OPSAPI_ARCHER_INSTANCE': 'test_instance',
            'OPSAPI_OPS_PORTAL_AUTH_URL': 'https://auth.test.com',
            'OPSAPI_OPS_PORTAL_ITEM_URL': 'https://item.test.com',
            'OPSAPI_OPS_PORTAL_CLIENT_ID': 'test_client_id',
            'OPSAPI_OPS_PORTAL_CLIENT_SECRET': 'test_client_secret',
            'OPSAPI_OPS_PORTAL_VERIFY_SSL': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config_from_env()
            assert config['ops_portal']['verify_ssl'] == False

    def test_load_config_from_env_missing_vars(self):
        """Test loading configuration with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                load_config_from_env()

    def test_get_time_log_from_env_success(self):
        """Test successful retrieval of time log from environment."""
        test_time = '2023-01-01T12:00:00'
        with patch.dict(os.environ, {'OPSAPI_TIME_LOG': test_time}):
            result = get_time_log_from_env()
            assert result.year == 2023
            assert result.month == 1
            assert result.day == 1

    def test_get_time_log_from_env_missing(self):
        """Test retrieval of time log when environment variable is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_time_log_from_env()
            # Should return current time when missing
            assert isinstance(result, datetime)

    def test_get_time_log_from_env_invalid_format(self):
        """Test retrieval of time log with invalid format."""
        with patch.dict(os.environ, {'OPSAPI_TIME_LOG': 'invalid_date'}):
            result = get_time_log_from_env()
            # Should return current time when invalid
            assert isinstance(result, datetime)

    def test_update_time_log_in_env(self):
        """Test updating time log in environment."""
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        
        # Should not raise an error
        update_time_log_in_env(test_time)

    @patch('ops_api.lambda_handler.send')
    @patch('ops_api.lambda_handler.preprocess')
    @patch('ops_api.lambda_handler.get_archer_auth')
    @patch('ops_api.lambda_handler.load_config_from_env')
    @patch('ops_api.lambda_handler.get_time_log_from_env')
    @patch('ops_api.lambda_handler.update_time_log_in_env')
    def test_handler_success_dry_run(self, mock_update_time, mock_get_time, mock_load_config, 
                                   mock_get_archer, mock_preprocess, mock_send):
        """Test successful handler execution with dry run."""
        # Setup mocks
        mock_get_time.return_value = datetime(2023, 1, 1)
        mock_load_config.return_value = {
            'archer': {'username': 'test'},
            'ops_portal': {'auth_url': 'test'},
            'processing': {'category_mapping_file': 'test.csv'}
        }
        
        mock_archer = MagicMock()
        mock_archer.get_sir_data.return_value = [{'test': 'data'}]
        mock_get_archer.return_value = mock_archer
        
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [{'test': 'processed_data'}]
        mock_df.__len__.return_value = 1  # Mock the len() function
        mock_preprocess.return_value = mock_df
        
        # Test event
        event = {'dry_run': True}
        context = MagicMock()
        
        # Call handler
        result = handler(event, context)
        
        # Verify result
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert 'message' in body
        assert 'results' in body
        assert body['results']['processed'] == 1
        assert body['results']['sent'] == 0  # Dry run, so nothing sent
        
        # Verify mocks were called
        mock_get_archer.assert_called_once()
        mock_archer.get_sir_data.assert_called_once()
        mock_preprocess.assert_called_once()
        mock_send.assert_not_called()  # Should not send in dry run

    @patch('ops_api.lambda_handler.send')
    @patch('ops_api.lambda_handler.preprocess')
    @patch('ops_api.lambda_handler.get_archer_auth')
    @patch('ops_api.lambda_handler.load_config_from_env')
    @patch('ops_api.lambda_handler.get_time_log_from_env')
    @patch('ops_api.lambda_handler.update_time_log_in_env')
    def test_handler_success_with_sending(self, mock_update_time, mock_get_time, mock_load_config, 
                                        mock_get_archer, mock_preprocess, mock_send):
        """Test successful handler execution with actual sending."""
        # Setup mocks
        mock_get_time.return_value = datetime(2023, 1, 1)
        mock_load_config.return_value = {
            'archer': {'username': 'test'},
            'ops_portal': {'auth_url': 'test'},
            'processing': {'category_mapping_file': 'test.csv'}
        }
        
        mock_archer = MagicMock()
        mock_archer.get_sir_data.return_value = [{'test': 'data'}]
        mock_get_archer.return_value = mock_archer
        
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [{'test': 'processed_data'}]
        mock_df.__len__.return_value = 1  # Mock the len() function
        mock_preprocess.return_value = mock_df
        
        # Mock successful sending
        mock_send.return_value = {'record1': (200, 'success')}
        
        # Test event (no dry_run flag)
        event = {}
        context = MagicMock()
        
        # Call handler
        result = handler(event, context)
        
        # Verify result
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['results']['processed'] == 1
        assert body['results']['sent'] == 1
        assert body['results']['success'] == 1
        assert body['results']['failed'] == 0
        
        # Verify send was called
        mock_send.assert_called_once()

    @patch('ops_api.lambda_handler.send')
    @patch('ops_api.lambda_handler.preprocess')
    @patch('ops_api.lambda_handler.get_archer_auth')
    @patch('ops_api.lambda_handler.load_config_from_env')
    @patch('ops_api.lambda_handler.get_time_log_from_env')
    @patch('ops_api.lambda_handler.update_time_log_in_env')
    def test_handler_empty_data(self, mock_update_time, mock_get_time, mock_load_config, 
                              mock_get_archer, mock_preprocess, mock_send):
        """Test handler execution with empty data."""
        # Setup mocks
        mock_get_time.return_value = datetime(2023, 1, 1)
        mock_load_config.return_value = {
            'archer': {'username': 'test'},
            'ops_portal': {'auth_url': 'test'},
            'processing': {'category_mapping_file': 'test.csv'}
        }
        
        mock_archer = MagicMock()
        mock_archer.get_sir_data.return_value = []  # Empty data
        mock_get_archer.return_value = mock_archer
        
        mock_df = MagicMock()
        mock_df.empty = True  # Empty DataFrame
        mock_preprocess.return_value = mock_df
        
        # Test event
        event = {}
        context = MagicMock()
        
        # Call handler
        result = handler(event, context)
        
        # Verify result
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['results']['processed'] == 0
        assert body['results']['sent'] == 0
        
        # Verify send was not called
        mock_send.assert_not_called()

    @patch('ops_api.lambda_handler.send')
    @patch('ops_api.lambda_handler.preprocess')
    @patch('ops_api.lambda_handler.get_archer_auth')
    @patch('ops_api.lambda_handler.load_config_from_env')
    @patch('ops_api.lambda_handler.get_time_log_from_env')
    @patch('ops_api.lambda_handler.update_time_log_in_env')
    def test_handler_with_failures(self, mock_update_time, mock_get_time, mock_load_config, 
                                 mock_get_archer, mock_preprocess, mock_send):
        """Test handler execution with some sending failures."""
        # Setup mocks
        mock_get_time.return_value = datetime(2023, 1, 1)
        mock_load_config.return_value = {
            'archer': {'username': 'test'},
            'ops_portal': {'auth_url': 'test'},
            'processing': {'category_mapping_file': 'test.csv'}
        }
        
        mock_archer = MagicMock()
        mock_archer.get_sir_data.return_value = [{'test': 'data1'}, {'test': 'data2'}]
        mock_get_archer.return_value = mock_archer
        
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.to_dict.return_value = [{'test': 'data1'}, {'test': 'data2'}]
        mock_preprocess.return_value = mock_df
        
        # Mock mixed success/failure
        mock_send.return_value = {
            'record1': (200, 'success'),
            'record2': (400, 'error')
        }
        
        # Test event
        event = {}
        context = MagicMock()
        
        # Call handler
        result = handler(event, context)
        
        # Verify result
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['results']['sent'] == 2
        assert body['results']['success'] == 1
        assert body['results']['failed'] == 1

    @patch('ops_api.lambda_handler.load_config_from_env')
    def test_handler_exception(self, mock_load_config):
        """Test handler execution with exception."""
        # Setup mock to raise exception
        mock_load_config.side_effect = Exception("Test exception")
        
        # Test event
        event = {}
        context = MagicMock()
        
        # Call handler
        result = handler(event, context)
        
        # Verify error result
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'Error in OPS API Lambda function' in body['message']


class TestMockLambdaContext:
    """Test the MockLambdaContext class from test_lambda_local.py."""
    
    def test_mock_context_creation(self):
        """Test that we can import and use the MockLambdaContext."""
        # Import here to avoid circular imports
        from tests.test_lambda_local import MockLambdaContext
        
        context = MockLambdaContext()
        
        # Test basic attributes
        assert context.function_name == 'ops-api-lambda'
        assert context.function_version == '$LATEST'
        assert context.memory_limit_in_mb == 512
        assert context.remaining_time_in_millis == 300000
        
        # Test method
        assert context.get_remaining_time_in_millis() == 300000

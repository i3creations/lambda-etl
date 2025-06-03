"""
Test module for AWS Secrets Manager functionality.

This module contains tests for the secrets manager utility functions.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os

from ops_api.utils.secrets_manager import (
    SecretsManager,
    get_environment_secret_name,
    load_config_from_secrets
)


class TestSecretsManager(unittest.TestCase):
    """Test cases for SecretsManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_secret_data = {
            'OPSAPI_ARCHER_USERNAME': 'test_user',
            'OPSAPI_ARCHER_PASSWORD': 'test_password',
            'OPSAPI_ARCHER_INSTANCE': 'test_instance',
            'OPSAPI_ARCHER_URL': 'https://test-archer.com/',
            'OPSAPI_ARCHER_VERIFY_SSL': 'true',
            'OPSAPI_OPS_PORTAL_AUTH_URL': 'https://test-auth.com/token',
            'OPSAPI_OPS_PORTAL_ITEM_URL': 'https://test-item.com/item',
            'OPSAPI_OPS_PORTAL_CLIENT_ID': 'test_client_id',
            'OPSAPI_OPS_PORTAL_CLIENT_SECRET': 'test_client_secret',
            'OPSAPI_OPS_PORTAL_VERIFY_SSL': 'false'
        }
    
    @patch('boto3.session.Session')
    def test_secrets_manager_init(self, mock_session):
        """Test SecretsManager initialization."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        sm = SecretsManager(region_name='us-west-2')
        
        self.assertEqual(sm.region_name, 'us-west-2')
        mock_session.return_value.client.assert_called_once_with(
            service_name='secretsmanager',
            region_name='us-west-2'
        )
    
    @patch('boto3.session.Session')
    def test_get_secret_success(self, mock_session):
        """Test successful secret retrieval."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock the response
        mock_response = {
            'SecretString': json.dumps(self.mock_secret_data)
        }
        mock_client.get_secret_value.return_value = mock_response
        
        sm = SecretsManager()
        result = sm.get_secret('test-secret')
        
        self.assertEqual(result, self.mock_secret_data)
        mock_client.get_secret_value.assert_called_once_with(SecretId='test-secret')
    
    @patch('boto3.session.Session')
    def test_get_secret_value(self, mock_session):
        """Test getting a specific value from a secret."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock the response
        mock_response = {
            'SecretString': json.dumps(self.mock_secret_data)
        }
        mock_client.get_secret_value.return_value = mock_response
        
        sm = SecretsManager()
        result = sm.get_secret_value('test-secret', 'OPSAPI_ARCHER_USERNAME')
        
        self.assertEqual(result, 'test_user')
    
    @patch('boto3.session.Session')
    def test_get_secret_value_with_default(self, mock_session):
        """Test getting a secret value with default when key doesn't exist."""
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Mock the response
        mock_response = {
            'SecretString': json.dumps(self.mock_secret_data)
        }
        mock_client.get_secret_value.return_value = mock_response
        
        sm = SecretsManager()
        result = sm.get_secret_value('test-secret', 'NON_EXISTENT_KEY', 'default_value')
        
        self.assertEqual(result, 'default_value')


class TestSecretManagerUtilities(unittest.TestCase):
    """Test cases for secrets manager utility functions."""
    
    def test_get_environment_secret_name_development(self):
        """Test getting secret name for development environment."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            result = get_environment_secret_name()
            self.assertEqual(result, 'opts-dev-secret')
    
    def test_get_environment_secret_name_preproduction(self):
        """Test getting secret name for preproduction environment."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'preproduction'}):
            result = get_environment_secret_name()
            self.assertEqual(result, 'opts-preprod-secret')
    
    def test_get_environment_secret_name_production(self):
        """Test getting secret name for production environment."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            result = get_environment_secret_name()
            self.assertEqual(result, 'opts-prod-secret')
    
    def test_get_environment_secret_name_default(self):
        """Test getting secret name with no environment set (should default to development)."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_environment_secret_name()
            self.assertEqual(result, 'opts-dev-secret')
    
    @patch('ops_api.utils.secrets_manager.get_secrets_manager')
    @patch('ops_api.utils.secrets_manager.get_environment_secret_name')
    def test_load_config_from_secrets(self, mock_get_secret_name, mock_get_secrets_manager):
        """Test loading configuration from secrets."""
        # Mock the secret name
        mock_get_secret_name.return_value = 'opts-dev-secret'
        
        # Mock the secrets manager
        mock_sm = MagicMock()
        mock_get_secrets_manager.return_value = mock_sm
        
        # Mock secret data
        mock_secret_data = {
            'OPSAPI_ARCHER_USERNAME': 'test_user',
            'OPSAPI_ARCHER_PASSWORD': 'test_password',
            'OPSAPI_ARCHER_INSTANCE': 'test_instance',
            'OPSAPI_ARCHER_URL': 'https://test-archer.com/',
            'OPSAPI_ARCHER_VERIFY_SSL': 'true',
            'OPSAPI_OPS_PORTAL_AUTH_URL': 'https://test-auth.com/token',
            'OPSAPI_OPS_PORTAL_ITEM_URL': 'https://test-item.com/item',
            'OPSAPI_OPS_PORTAL_CLIENT_ID': 'test_client_id',
            'OPSAPI_OPS_PORTAL_CLIENT_SECRET': 'test_client_secret',
            'OPSAPI_OPS_PORTAL_VERIFY_SSL': 'false'
        }
        mock_sm.get_secret.return_value = mock_secret_data
        
        # Call the function
        result = load_config_from_secrets()
        
        # Verify the structure
        expected_config = {
            'archer': {
                'username': 'test_user',
                'password': 'test_password',
                'instance': 'test_instance',
                'url': 'https://test-archer.com/',
                'verify_ssl': True
            },
            'ops_portal': {
                'auth_url': 'https://test-auth.com/token',
                'item_url': 'https://test-item.com/item',
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'verify_ssl': False
            }
        }
        
        self.assertEqual(result, expected_config)
        
        # Verify the calls
        mock_get_secret_name.assert_called_once()
        mock_get_secrets_manager.assert_called_once()
        mock_sm.get_secret.assert_called_once_with('opts-dev-secret')


if __name__ == '__main__':
    unittest.main()

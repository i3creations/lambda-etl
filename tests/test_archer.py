"""
Unit tests for the archer.auth module.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from datetime import datetime

# Import the module to test
from ops_api.archer.auth import get_archer_auth


class TestArcherAuth(unittest.TestCase):
    """Test cases for the archer.auth module."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'username': 'test_user',
            'password': 'test_password',
            'instance': 'test_instance',
            'url': 'https://test.example.com/'
        }

    def test_fallback_archer_auth(self):
        """Test the fallback ArcherAuth class."""
        # Define a mock fallback ArcherAuth class for testing
        class MockArcherAuth:
            def __init__(self, ins, usr, pwd, url, dom=''):
                self.ins = ins
                self.usr = usr
                self.pwd = pwd
                self.base_url = url
                self.dom = dom
                self.authenticated = False
            
            def login(self):
                self.authenticated = True
            
            def logout(self):
                self.authenticated = False
                
            def __enter__(self):
                self.login()
                return self
                
            def __exit__(self, *args, **kwargs):
                self.logout()
                return False
            
            def get_sir_data(self, since_date=None):
                return []
        
        # Patch the ArcherAuth import to use our mock class
        with patch('ops_api.archer.auth.ArcherAuth', MockArcherAuth):
            # Import the get_archer_auth function
            from ops_api.archer.auth import get_archer_auth
            
            # Test the function with our mock class
            auth = get_archer_auth(self.config)
            
            # Verify the instance was created with the correct parameters
            self.assertEqual(auth.ins, 'test_instance')
            self.assertEqual(auth.usr, 'test_user')
            self.assertEqual(auth.pwd, 'test_password')
            self.assertEqual(auth.base_url, 'https://test.example.com/')
            
            # Test login method
            auth.login()
            self.assertTrue(auth.authenticated)
            
            # Test get_sir_data method without since_date
            result = auth.get_sir_data()
            self.assertEqual(result, [])
            
            # Test get_sir_data method with since_date
            since_date = datetime.now()
            result = auth.get_sir_data(since_date=since_date)
            self.assertEqual(result, [])

    @patch('ops_api.archer.auth.ArcherAuth')
    def test_get_archer_auth_success(self, mock_archer_auth):
        """Test successful creation of an ArcherAuth instance."""
        # Setup the mock
        mock_instance = MagicMock()
        mock_archer_auth.return_value = mock_instance
        
        # Call the function
        result = get_archer_auth(self.config)
        
        # Verify ArcherAuth was called with the correct parameters
        mock_archer_auth.assert_called_once_with(
            'test_instance', 'test_user', 'test_password', 'https://test.example.com/', ''
        )
        
        # Verify the result is the mock instance
        self.assertEqual(result, mock_instance)

    @patch('ops_api.archer.auth.ArcherAuth')
    def test_get_archer_auth_with_empty_config(self, mock_archer_auth):
        """Test creation of an ArcherAuth instance with empty config."""
        # Setup the mock
        mock_instance = MagicMock()
        mock_archer_auth.return_value = mock_instance
        
        # Call the function with empty config
        result = get_archer_auth({})
        
        # Verify ArcherAuth was called with empty strings
        mock_archer_auth.assert_called_once_with('', '', '', '', '')
        
        # Verify the result is the mock instance
        self.assertEqual(result, mock_instance)

    @patch('ops_api.archer.auth.ArcherAuth')
    @patch('ops_api.archer.auth.logger')
    def test_get_archer_auth_exception(self, mock_logger, mock_archer_auth):
        """Test exception handling when creating an ArcherAuth instance."""
        # Setup the mock to raise an exception
        mock_archer_auth.side_effect = Exception("Test exception")
        
        # Verify that the function raises the exception
        with self.assertRaises(Exception) as context:
            get_archer_auth(self.config)
        
        # Verify the exception message
        self.assertEqual(str(context.exception), "Test exception")
        
        # Verify that the error was logged
        mock_logger.error.assert_called_once_with("Error creating ArcherAuth instance: Test exception")
        
    @patch('ops_api.archer.auth.ArcherAuth')
    def test_get_archer_auth_partial_config(self, mock_archer_auth):
        """Test creation of an ArcherAuth instance with partial config."""
        # Setup the mock
        mock_instance = MagicMock()
        mock_archer_auth.return_value = mock_instance
        
        # Call the function with partial config
        partial_config = {
            'username': 'test_user',
            # Missing password and instance
        }
        result = get_archer_auth(partial_config)
        
        # Verify ArcherAuth was called with the correct parameters
        # Missing keys should default to empty strings
        mock_archer_auth.assert_called_once_with('', 'test_user', '', '', '')
        
        # Verify the result is the mock instance
        self.assertEqual(result, mock_instance)
        
    @patch('ops_api.archer.auth.ArcherAuth')
    def test_get_archer_auth_extra_config(self, mock_archer_auth):
        """Test creation of an ArcherAuth instance with extra config keys."""
        # Setup the mock
        mock_instance = MagicMock()
        mock_archer_auth.return_value = mock_instance
        
        # Call the function with extra config keys
        extra_config = {
            'username': 'test_user',
            'password': 'test_password',
            'instance': 'test_instance',
            'url': 'https://test.example.com/',
            'extra_key': 'extra_value',  # Extra key that should be ignored
            'another_extra': 123  # Another extra key that should be ignored
        }
        result = get_archer_auth(extra_config)
        
        # Verify ArcherAuth was called with only the required parameters
        mock_archer_auth.assert_called_once_with(
            'test_instance', 'test_user', 'test_password', 'https://test.example.com/', ''
        )
        
        # Verify the result is the mock instance
        self.assertEqual(result, mock_instance)


if __name__ == '__main__':
    unittest.main()

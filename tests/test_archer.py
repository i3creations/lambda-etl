"""
Unit tests for the archer.auth module.
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
from datetime import datetime, timezone

# Mock the uscis-opts package import to force fallback implementation
with patch.dict('sys.modules', {'opts.ArcherAuth': None, 'opts.ArcherServerClient': None}):
    # Import the module to test - this will force the fallback implementation
    from src.archer.auth import get_archer_auth, ArcherAuth


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
        """Test the fallback ArcherAuth class when uscis-opts package is not available."""
        # Test the fallback implementation directly
        auth = get_archer_auth(self.config)
        
        # Verify the instance was created with the correct parameters
        self.assertEqual(auth.ins, 'test_instance')
        self.assertEqual(auth.usr, 'test_user')
        self.assertEqual(auth.pwd, 'test_password')
        self.assertEqual(auth.base_url, 'https://test.example.com/')  # Fixed URL assertion
        self.assertEqual(auth.dom, '')
        self.assertEqual(auth.verify_ssl, True)
        
        # Test initial authentication state
        self.assertFalse(auth.authenticated)
        
        # Test get_sir_data method without since_incident_id
        result = auth.get_sir_data()
        self.assertEqual(result, [])
        
        # Test get_sir_data method with since_incident_id
        since_incident_id = 100
        result = auth.get_sir_data(since_incident_id=since_incident_id)
        self.assertEqual(result, [])

    def test_archer_auth_ssl_verification_config(self):
        """Test SSL verification configuration handling."""
        # Test with boolean True
        config_bool_true = self.config.copy()
        config_bool_true['verify_ssl'] = True
        auth = get_archer_auth(config_bool_true)
        self.assertTrue(auth.verify_ssl)
        
        # Test with boolean False
        config_bool_false = self.config.copy()
        config_bool_false['verify_ssl'] = False
        auth = get_archer_auth(config_bool_false)
        self.assertFalse(auth.verify_ssl)
        
        # Test with string 'true'
        config_str_true = self.config.copy()
        config_str_true['verify_ssl'] = 'true'
        auth = get_archer_auth(config_str_true)
        self.assertTrue(auth.verify_ssl)
        
        # Test with string 'false'
        config_str_false = self.config.copy()
        config_str_false['verify_ssl'] = 'false'
        auth = get_archer_auth(config_str_false)
        self.assertFalse(auth.verify_ssl)
        
        # Test with string '1'
        config_str_one = self.config.copy()
        config_str_one['verify_ssl'] = '1'
        auth = get_archer_auth(config_str_one)
        self.assertTrue(auth.verify_ssl)
        
        # Test with string '0'
        config_str_zero = self.config.copy()
        config_str_zero['verify_ssl'] = '0'
        auth = get_archer_auth(config_str_zero)
        self.assertFalse(auth.verify_ssl)
        
        # Test with string 'yes'
        config_str_yes = self.config.copy()
        config_str_yes['verify_ssl'] = 'yes'
        auth = get_archer_auth(config_str_yes)
        self.assertTrue(auth.verify_ssl)
        
        # Test with string 'no'
        config_str_no = self.config.copy()
        config_str_no['verify_ssl'] = 'no'
        auth = get_archer_auth(config_str_no)
        self.assertFalse(auth.verify_ssl)

    def test_archer_auth_with_domain(self):
        """Test ArcherAuth creation with domain parameter."""
        config_with_domain = self.config.copy()
        config_with_domain['domain'] = 'test_domain'
        
        auth = get_archer_auth(config_with_domain)
        self.assertEqual(auth.dom, 'test_domain')

    def test_get_archer_auth_with_empty_config(self):
        """Test get_archer_auth function with empty config values."""
        # Test with empty config - fallback implementation should handle this gracefully
        empty_config = {
            'username': '',
            'password': '',
            'instance': '',
            'url': ''
        }
        
        auth = get_archer_auth(empty_config)
        
        # Verify the instance was created with empty parameters
        self.assertEqual(auth.ins, '')
        self.assertEqual(auth.usr, '')
        self.assertEqual(auth.pwd, '')
        self.assertEqual(auth.base_url, '')
        self.assertEqual(auth.dom, '')
        self.assertEqual(auth.verify_ssl, True)  # Default value

    def test_archer_auth_login_logout(self):
        """Test ArcherAuth login and logout functionality with fallback implementation."""
        # Test the fallback implementation directly
        auth = get_archer_auth(self.config)
        
        # Test initial authentication state
        self.assertFalse(auth.authenticated)
        
        # Test login method
        auth.login()
        self.assertTrue(auth.authenticated)
        
        # Test logout method
        auth.logout()
        self.assertFalse(auth.authenticated)

    def test_archer_auth_get_sir_data_fallback(self):
        """Test ArcherAuth get_sir_data method with fallback implementation."""
        # Test the fallback implementation directly
        auth = get_archer_auth(self.config)
        
        # Test without incident ID filter - fallback should return empty list
        all_data = auth.get_sir_data()
        self.assertEqual(all_data, [])
        
        # Test with incident ID filter - fallback should return empty list
        since_incident_id = 100
        filtered_data = auth.get_sir_data(since_incident_id=since_incident_id)
        self.assertEqual(filtered_data, [])


if __name__ == '__main__':
    unittest.main()

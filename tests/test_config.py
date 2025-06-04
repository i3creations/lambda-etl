"""
Unit tests for the config module.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from ops_api.config import Config, get_config


class TestConfig:
    """Test cases for the Config class."""

    def test_init_with_defaults(self):
        """Test Config initialization with default paths."""
        with patch('os.path.exists', return_value=False):
            config = Config()
            assert config.config_file is not None
            assert isinstance(config.config, dict)

    def test_init_with_custom_paths(self):
        """Test Config initialization with custom paths."""
        config_file = '/custom/config.ini'
        
        with patch('os.path.exists', return_value=False):
            config = Config(config_file=config_file)
            assert str(config.config_file) == config_file

    def test_load_from_file_success(self, tmpdir):
        """Test successful loading from config file."""
        config_file = tmpdir.join('config.ini')
        config_file.write("""
[archer]
username = test_user
password = test_pass

[ops]
portal_url = https://test.com
""")
        
        # Clear environment variables that might interfere
        env_vars_to_clear = [key for key in os.environ.keys() if key.startswith('OPSAPI_')]
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]
            
            config = Config(config_file=config_file.strpath)
            
            assert 'archer' in config.config
            assert config.config['archer']['username'] == 'test_user'
            assert config.config['archer']['password'] == 'test_pass'
            assert 'ops' in config.config
            assert config.config['ops']['portal_url'] == 'https://test.com'

    def test_load_from_file_not_found(self, tmpdir):
        """Test loading from non-existent config file."""
        non_existent = tmpdir.join('nonexistent.ini')
        
        config = Config(config_file=non_existent.strpath)
        
        # Should not raise an error, just log a warning
        assert isinstance(config.config, dict)

    def test_load_from_env_vars(self):
        """Test successful loading from environment variables."""
        # Clear existing environment variables first
        env_vars_to_clear = [key for key in os.environ.keys() if key.startswith('OPSAPI_')]
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]
            
            with patch.dict(os.environ, {
                'OPSAPI_ARCHER_USERNAME': 'env_user',
                'OPSAPI_ARCHER_PASSWORD': 'env_pass',
                'OPSAPI_OPS_PORTAL_URL': 'https://env.com'
            }):
                config = Config(config_file='/nonexistent/config.ini')
                
                assert config.config['archer']['username'] == 'env_user'
                assert config.config['archer']['password'] == 'env_pass'
                assert config.config['ops']['portal_url'] == 'https://env.com'

    def test_process_env_vars(self):
        """Test processing of environment variables."""
        with patch.dict(os.environ, {
            'OPSAPI_ARCHER_USERNAME': 'env_user',
            'OPSAPI_ARCHER_PASSWORD': 'env_pass',
            'OPSAPI_OPS_PORTAL_URL': 'https://env.com',
            'OPSAPI_PROCESSING_FILTER': 'true',
            'OTHER_VAR': 'should_be_ignored'
        }):
            config = Config(config_file='/nonexistent/config.ini')
            
            assert config.config['archer']['username'] == 'env_user'
            assert config.config['archer']['password'] == 'env_pass'
            assert config.config['ops']['portal_url'] == 'https://env.com'
            assert config.config['processing']['filter'] == 'true'
            
            # Should not include non-OPSAPI variables
            assert 'other' not in config.config

    def test_get_method(self):
        """Test the get method."""
        with patch.dict(os.environ, {
            'OPSAPI_ARCHER_USERNAME': 'test_user'
        }):
            config = Config(config_file='/nonexistent/config.ini')
            
            # Test existing value
            assert config.get('archer', 'username') == 'test_user'
            
            # Test non-existing value with default
            assert config.get('archer', 'nonexistent', 'default_value') == 'default_value'
            
            # Test non-existing section
            assert config.get('nonexistent', 'key', 'default') == 'default'

    def test_get_section(self):
        """Test the get_section method."""
        with patch.dict(os.environ, {
            'OPSAPI_ARCHER_USERNAME': 'test_user',
            'OPSAPI_ARCHER_PASSWORD': 'test_pass'
        }):
            config = Config(config_file='/nonexistent/config.ini')
            
            archer_section = config.get_section('archer')
            assert archer_section['username'] == 'test_user'
            assert archer_section['password'] == 'test_pass'
            
            # Test non-existing section
            empty_section = config.get_section('nonexistent')
            assert empty_section == {}

    def test_get_all(self):
        """Test the get_all method."""
        with patch.dict(os.environ, {
            'OPSAPI_ARCHER_USERNAME': 'test_user',
            'OPSAPI_OPS_PORTAL_URL': 'https://test.com'
        }):
            config = Config(config_file='/nonexistent/config.ini')
            
            all_config = config.get_all()
            assert isinstance(all_config, dict)
            assert 'archer' in all_config
            assert 'ops' in all_config

    def test_get_sensitive_keys(self):
        """Test the get_sensitive_keys method."""
        config = Config(config_file='/nonexistent/config.ini')
        
        sensitive_keys = config.get_sensitive_keys()
        assert isinstance(sensitive_keys, list)
        assert 'password' in sensitive_keys
        assert 'secret' in sensitive_keys
        assert 'key' in sensitive_keys
        assert 'token' in sensitive_keys

    def test_config_precedence(self, tmpdir):
        """Test that environment variables override config file values."""
        config_file = tmpdir.join('config.ini')
        config_file.write("""
[archer]
username = file_user
password = file_pass
""")
        
        # Clear existing environment variables first
        env_vars_to_clear = [key for key in os.environ.keys() if key.startswith('OPSAPI_')]
        with patch.dict(os.environ, {}, clear=False):
            for var in env_vars_to_clear:
                if var in os.environ:
                    del os.environ[var]
            
            with patch.dict(os.environ, {
                'OPSAPI_ARCHER_USERNAME': 'env_user'
            }):
                config = Config(config_file=config_file.strpath)
                
                # Environment variable should override file value
                assert config.get('archer', 'username') == 'env_user'
                # File value should be used when no env var exists
                assert config.get('archer', 'password') == 'file_pass'

    def test_error_handling_in_load_config(self):
        """Test error handling in load_config method."""
        with patch('src.config.Config._load_from_file', side_effect=Exception("File error")):
            with pytest.raises(Exception):
                Config(config_file='/some/file')


class TestGetConfig:
    """Test cases for the get_config function."""

    def test_get_config_with_defaults(self):
        """Test get_config with default parameters."""
        config = get_config()
        assert isinstance(config, Config)

    def test_get_config_with_custom_paths(self):
        """Test get_config with custom paths."""
        with patch('src.config.Config') as mock_config:
            get_config(config_file='/custom/config.ini')
            mock_config.assert_called_once_with('/custom/config.ini')

    def test_get_config_returns_default_instance(self):
        """Test that get_config returns the default instance when no params provided."""
        config1 = get_config()
        config2 = get_config()
        # Should return the same default instance
        assert config1 is config2

"""
Configuration Module

This module handles loading and managing configuration settings for the OPS API.
It provides functionality to load configuration from files and environment variables.
Environment variables should be loaded into memory using 'source .env' before running the application.
"""

import os
import configparser
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        """Fallback function when python-dotenv is not available."""
        pass

from .utils.logging_utils import get_logger

# Get logger for this module
logger = get_logger('config')


class Config:
    """
    Configuration manager for the OPS API.
    
    This class handles loading and managing configuration settings from files
    and environment variables. Environment variables should be loaded into memory
    using 'source .env' before running the application.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str, optional): Path to the configuration file.
                If None, looks for 'config.ini' in the config directory.
        """
        self.config = {}
        
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        
        # Set default config file path if not provided
        if config_file is None:
            config_file = project_root / 'config' / 'config.ini'
        
        self.config_file = config_file
        
        logger.info(f"Initializing configuration from {self.config_file} and environment variables")
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """
        Load configuration from the config file and environment variables.
        
        This method loads configuration in the following order:
        1. From the config file
        2. From environment variables (which should be loaded via 'source .env')
        
        Environment variables override config file values.
        """
        try:
            # Load from config file
            self._load_from_file()
            
            # Load from environment variables
            self._load_from_env()
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
    
    def _load_from_file(self):
        """
        Load configuration from the config file.
        """
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Config file not found: {self.config_file}")
                return
            
            logger.info(f"Loading configuration from file: {self.config_file}")
            
            parser = configparser.ConfigParser()
            parser.read(self.config_file)
            
            # Convert to dictionary
            for section in parser.sections():
                self.config[section] = {}
                for key, value in parser[section].items():
                    self.config[section][key] = value
            
            logger.info(f"Loaded configuration from file: {list(self.config.keys())}")
            
        except Exception as e:
            logger.error(f"Error loading configuration from file: {str(e)}")
            raise
    

    
    def _load_from_env(self):
        """
        Load configuration from environment variables.
        
        This method processes environment variables that are already set in the environment.
        """
        try:
            logger.info("Loading configuration from environment variables")
            
            # Process environment variables
            self._process_env_vars()
            
        except Exception as e:
            logger.error(f"Error loading configuration from environment variables: {str(e)}")
            raise
    
    def _process_env_vars(self):
        """
        Process environment variables and add them to the configuration.
        
        Environment variables should be in the format OPSAPI_SECTION_KEY.
        For example, OPSAPI_ARCHER_USERNAME would override config['archer']['username'].
        """
        prefix = 'OPSAPI_'
        
        for env_var, value in os.environ.items():
            if env_var.startswith(prefix):
                # Remove prefix and split by underscore
                parts = env_var[len(prefix):].lower().split('_', 1)
                
                if len(parts) == 2:
                    section, key = parts
                    
                    # Handle multi-part keys (e.g., OPSAPI_OPS_PORTAL_CERT_PEM)
                    if section == 'ops' and key.startswith('portal_'):
                        section = 'ops_portal'
                        key = key[7:]  # Remove 'portal_' prefix
                    
                    # Create section if it doesn't exist
                    if section not in self.config:
                        self.config[section] = {}
                    
                    # Set value
                    self.config[section][key] = value
                    logger.debug(f"Setting config[{section}][{key}] from environment variable")
                    
                    # Also map opsportal section to ops_portal for backward compatibility
                    if section == 'opsportal':
                        if 'ops_portal' not in self.config:
                            self.config['ops_portal'] = {}
                        self.config['ops_portal'][key] = value
                        logger.debug(f"Also setting config[ops_portal][{key}] from environment variable")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section (str): Configuration section
            key (str): Configuration key
            default (Any, optional): Default value if the key doesn't exist
            
        Returns:
            Any: Configuration value or default
        """
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section (str): Configuration section
            
        Returns:
            Dict[str, Any]: Configuration section or empty dict if it doesn't exist
        """
        return self.config.get(section, {})
    
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the entire configuration.
        
        Returns:
            Dict[str, Dict[str, Any]]: Complete configuration
        """
        return self.config
    
    def get_sensitive_keys(self) -> List[str]:
        """
        Get a list of sensitive configuration keys that should not be logged.
        
        Returns:
            List[str]: List of sensitive keys
        """
        return [
            'password', 'secret', 'key', 'token', 'auth', 'credential',
            'client_id', 'client_secret'
        ]


# Create a default configuration instance
default_config = Config()


def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get a configuration instance.
    
    Args:
        config_file (str, optional): Path to the configuration file.
            If None, uses the default configuration instance.
            
    Returns:
        Config: Configuration instance
    """
    if config_file is None:
        return default_config
    else:
        return Config(config_file)

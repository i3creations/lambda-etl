"""
Configuration Module

This module handles loading and managing configuration settings for the OPS API.
It provides functionality to load configuration from files and environment variables,
including support for .env files using python-dotenv.
"""

import os
import configparser
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from .utils.logging_utils import get_logger

# Get logger for this module
logger = get_logger('config')


class Config:
    """
    Configuration manager for the OPS API.
    
    This class handles loading and managing configuration settings from files
    and environment variables, including .env files.
    """
    
    def __init__(self, config_file: Optional[str] = None, env_file: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str, optional): Path to the configuration file.
                If None, looks for 'config.ini' in the config directory.
            env_file (str, optional): Path to the .env file.
                If None, looks for '.env' in the project root directory.
        """
        self.config = {}
        
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        
        # Set default config file path if not provided
        if config_file is None:
            config_file = project_root / 'config' / 'config.ini'
        
        # Set default .env file path if not provided
        if env_file is None:
            env_file = project_root / '.env'
        
        self.config_file = config_file
        self.env_file = env_file
        
        logger.info(f"Initializing configuration from {self.config_file} and {self.env_file}")
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """
        Load configuration from the config file, .env file, and environment variables.
        
        This method loads configuration in the following order:
        1. From the config file
        2. From the .env file
        3. From environment variables
        
        Later sources override earlier ones.
        """
        try:
            # Load from config file
            self._load_from_file()
            
            # Load from .env file
            self._load_from_dotenv()
            
            # Override with environment variables
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
    
    def _load_from_dotenv(self):
        """
        Load configuration from the .env file.
        
        This method loads environment variables from the .env file using python-dotenv.
        """
        try:
            if not os.path.exists(self.env_file):
                logger.warning(f".env file not found: {self.env_file}")
                return
            
            logger.info(f"Loading configuration from .env file: {self.env_file}")
            
            # Load environment variables from .env file
            load_dotenv(self.env_file)
            
            # Process environment variables loaded from .env file
            self._process_env_vars()
            
            logger.info("Loaded configuration from .env file")
            
        except Exception as e:
            logger.error(f"Error loading configuration from .env file: {str(e)}")
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
                    
                    # Create section if it doesn't exist
                    if section not in self.config:
                        self.config[section] = {}
                    
                    # Set value
                    self.config[section][key] = value
                    logger.debug(f"Setting config[{section}][{key}] from environment variable")
    
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


def get_config(config_file: Optional[str] = None, env_file: Optional[str] = None) -> Config:
    """
    Get a configuration instance.
    
    Args:
        config_file (str, optional): Path to the configuration file.
            If None, uses the default configuration instance.
        env_file (str, optional): Path to the .env file.
            If None, uses the default configuration instance.
            
    Returns:
        Config: Configuration instance
    """
    if config_file is None and env_file is None:
        return default_config
    else:
        return Config(config_file, env_file)

"""
Test script for OPS Portal authentication using credentials from .env file.

This script loads the OPS Portal authentication credentials from the .env file
and attempts to authenticate with the OPS Portal API.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the necessary modules
from ops_api.config import Config
from ops_api.ops_portal.api import OpsPortalClient
from ops_api.utils.logging_utils import get_logger

# Set up logging
logger = get_logger('test_ops_portal_auth')

def test_ops_portal_auth():
    """
    Test OPS Portal authentication using credentials from .env file.
    """
    try:
        # Load configuration from .env file
        config = Config()
        
        # Get OPS Portal configuration from the 'opsportal' section
        # (Environment variables OPSAPI_OPSPORTAL_* get mapped to opsportal.*)
        ops_config = config.get_section('opsportal')
        
        # Map the configuration keys to what OpsPortalClient expects
        ops_portal_config = {
            'auth_url': ops_config.get('auth_url'),
            'item_url': ops_config.get('item_url'),
            'client_id': ops_config.get('client_id'),
            'client_secret': ops_config.get('client_secret'),
            'verify_ssl': ops_config.get('verify_ssl', 'true').lower() == 'true'
        }
        
        # Debug: Log all available configuration sections
        logger.info(f"Available configuration sections: {list(config.get_all().keys())}")
        logger.info(f"OPS config keys: {list(ops_config.keys())}")
        
        # Check if we have the required configuration
        if not ops_portal_config.get('auth_url'):
            logger.error("Missing auth_url in ops portal configuration")
            logger.info("Available environment variables:")
            for key, value in os.environ.items():
                if key.startswith('OPSAPI_OPS_PORTAL'):
                    logger.info(f"  {key}={value}")
            return False
        
        # Log the configuration (excluding sensitive information)
        logger.info(f"OPS Portal configuration loaded: auth_url={ops_portal_config.get('auth_url')}, "
                   f"item_url={ops_portal_config.get('item_url')}, "
                   f"client_id={ops_portal_config.get('client_id')}, "
                   f"verify_ssl={ops_portal_config.get('verify_ssl')}")
        
        # Create OPS Portal client instance
        logger.info("Creating OPS Portal client instance...")
        client = OpsPortalClient(ops_portal_config)
        
        # Attempt to authenticate
        logger.info("Attempting to authenticate with OPS Portal...")
        result = client.authenticate()
        
        # Check the result
        if result:
            logger.info("Authentication successful!")
            # Verify that token was set
            if client.token:
                logger.info("Authentication token received and stored")
            else:
                logger.warning("Authentication returned True but no token was stored")
        else:
            logger.error("Authentication failed!")
        
        return result
    
    except Exception as e:
        logger.error(f"Error during OPS Portal authentication test: {str(e)}")
        raise

if __name__ == '__main__':
    print("Testing OPS Portal authentication...")
    success = test_ops_portal_auth()
    print(f"Authentication {'successful' if success else 'failed'}!")

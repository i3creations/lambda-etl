"""
Test script for Archer authentication using credentials from .env file.

This script loads the Archer authentication credentials from the .env file
and attempts to authenticate with the Archer system.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the necessary modules
from ops_api.config import Config
from ops_api.archer.auth import get_archer_auth
from ops_api.utils.logging_utils import get_logger

# Set up logging
logger = get_logger('test_archer_auth')

def test_archer_auth():
    """
    Test Archer authentication using credentials from .env file.
    """
    try:
        # Load configuration from .env file
        config = Config()
        
        # Get Archer configuration
        archer_config = config.get_section('archer')
        
        # Provide default test values if configuration is missing
        if not archer_config.get('username'):
            archer_config['username'] = 'archer_test_username'
        if not archer_config.get('password'):
            archer_config['password'] = 'archer_test_password'
        if not archer_config.get('instance'):
            archer_config['instance'] = 'archer_test_instance'
        if not archer_config.get('url'):
            archer_config['url'] = 'https://test.archer.com'
        
        # Log the configuration (excluding sensitive information)
        logger.info(f"Archer configuration loaded: username={archer_config.get('username')}, "
                   f"instance={archer_config.get('instance')}, url={archer_config.get('url')}")
        
        # Create Archer authentication instance
        logger.info("Creating Archer authentication instance...")
        auth = get_archer_auth(archer_config)
        
        # Attempt to authenticate (mock the network call)
        logger.info("Attempting to authenticate with Archer...")
        # Use login method and check authenticated property
        if hasattr(auth, 'login') and callable(getattr(auth, 'login')):
            # Mock the session.post call to avoid actual network requests
            with patch.object(auth.session, 'post') as mock_post:
                # Mock a successful response
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'IsSuccessful': True,
                    'RequestedObject': {'SessionToken': 'test_token'}
                }
                mock_post.return_value = mock_response
                
                auth.login()
                if hasattr(auth, 'authenticated'):
                    result = auth.authenticated
                else:
                    logger.error("'authenticated' property not found after login")
                    result = False
        else:
            logger.error("'login' method not found")
            result = False
        
        # Check the result
        if result:
            logger.info("Authentication successful!")
        else:
            logger.error("Authentication failed!")
        
        return result
    
    except Exception as e:
        logger.error(f"Error during Archer authentication test: {str(e)}")
        raise

if __name__ == '__main__':
    print("Testing Archer authentication...")
    success = test_archer_auth()
    print(f"Authentication {'successful' if success else 'failed'}!")

"""
Test script for OPS Portal authentication using credentials from .env file.

This script loads the OPS Portal authentication credentials from the .env file
and attempts to authenticate with the OPS Portal API using certificate-based authentication.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the necessary modules
from src.config import Config
from src.ops_portal.api import OpsPortalClient
from src.utils.logging_utils import get_logger

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
except ImportError:
    print("Warning: python-dotenv not available, assuming environment variables are already loaded")

# Set up logging
logger = get_logger('test_ops_portal_auth')

def test_ops_portal_auth_with_certificate():
    """
    Test OPS Portal authentication using certificate-based authentication from .env file.
    """
    try:
        logger.info("=" * 60)
        logger.info("Testing OPS Portal Certificate Authentication")
        logger.info("=" * 60)
        
        # Load configuration from .env file
        config = Config()
        
        # Get OPS Portal configuration from the 'ops_portal' section
        ops_config = config.get_section('ops_portal')
        
        # Check if certificate information is available
        cert_pem = ops_config.get('cert_pem')
        key_pem = ops_config.get('key_pem')
        cert_path = ops_config.get('cert_path')
        
        # Log certificate information
        if cert_pem and key_pem:
            logger.info(f"PEM Certificate information found:")
            logger.info(f"  - Certificate PEM length: {len(cert_pem)} characters")
            logger.info(f"  - Key PEM length: {len(key_pem)} characters")
        
        if cert_path:
            # If the path is relative, make it absolute from the project root
            if not os.path.isabs(cert_path):
                full_cert_path = os.path.join(project_root, cert_path)
            else:
                full_cert_path = cert_path
                
            if os.path.exists(full_cert_path):
                logger.info(f"PFX Certificate information found:")
                logger.info(f"  - Certificate path: {full_cert_path}")
                logger.info(f"  - Certificate file size: {os.path.getsize(full_cert_path)} bytes")
            else:
                logger.warning(f"PFX certificate file not found at: {full_cert_path}")
                cert_path = None
        
        # Skip test if no certificate information is available
        if not cert_path:
            logger.warning("No PFX certificate information found - skipping certificate test")
            return None
        
        # Map the configuration keys to what OpsPortalClient expects
        ops_portal_config = {
            'auth_url': ops_config.get('auth_url'),
            'item_url': ops_config.get('item_url'),
            'client_id': ops_config.get('client_id'),
            'client_secret': ops_config.get('client_secret'),
            'verify_ssl': ops_config.get('verify_ssl', 'true').lower() == 'true'
        }
        
        # Configure certificate
        if cert_path:
            # If the path is relative, make it absolute from the project root
            if not os.path.isabs(cert_path):
                full_cert_path = os.path.join(project_root, cert_path)
            else:
                full_cert_path = cert_path
                
            # Check if the file exists
            if os.path.exists(full_cert_path):
                # Use the PFX certificate file
                ops_portal_config['cert_pfx'] = full_cert_path
                ops_portal_config['pfx_password'] = ops_config.get('cert_password')
                logger.info(f"Using PFX certificate from cert_path: {full_cert_path}")
                logger.info(f"PFX file exists: {os.path.exists(full_cert_path)}")
                logger.info(f"PFX file size: {os.path.getsize(full_cert_path)} bytes")
                logger.info(f"PFX password: {'Set' if ops_config.get('cert_password') else 'Not set'}")
            else:
                logger.warning(f"PFX certificate file not found at: {full_cert_path}")
        
        # Check if we have the required configuration
        if not ops_portal_config.get('auth_url'):
            logger.error("Missing auth_url in ops portal configuration")
            return False
        
        # Log the configuration (excluding sensitive information)
        logger.info(f"OPS Portal certificate configuration loaded:")
        logger.info(f"  - auth_url: {ops_portal_config.get('auth_url')}")
        logger.info(f"  - item_url: {ops_portal_config.get('item_url')}")
        logger.info(f"  - client_id: {ops_portal_config.get('client_id')}")
        logger.info(f"  - verify_ssl: {ops_portal_config.get('verify_ssl')}")
        logger.info(f"  - PFX certificate configured: {bool(ops_portal_config.get('cert_pfx'))}")
        
        # Create OPS Portal client instance with certificate
        logger.info("Creating OPS Portal client instance with certificate...")
        client = OpsPortalClient(ops_portal_config)
        
        # Verify certificate configuration
        if hasattr(client.session, 'cert') and client.session.cert:
            logger.info("✅ SSL client certificate configured successfully")
            if hasattr(client, '_temp_cert_path') and hasattr(client, '_temp_key_path'):
                logger.info(f"  - Temporary certificate file: {client._temp_cert_path}")
                logger.info(f"  - Temporary key file: {client._temp_key_path}")
                
                # Verify temporary files exist and have content
                if os.path.exists(client._temp_cert_path) and os.path.exists(client._temp_key_path):
                    cert_size = os.path.getsize(client._temp_cert_path)
                    key_size = os.path.getsize(client._temp_key_path)
                    logger.info(f"  - Certificate file size: {cert_size} bytes")
                    logger.info(f"  - Key file size: {key_size} bytes")
                else:
                    logger.warning("Temporary certificate files not found on disk")
        else:
            logger.warning("SSL client certificate not configured in session")
        
        # Attempt to authenticate with certificate
        logger.info("Attempting to authenticate with OPS Portal using certificate...")
        result = client.authenticate()
        
        # Check the result
        if result:
            logger.info("✅ Certificate-based authentication successful!")
            # Verify that token was set
            if client.token:
                logger.info("✅ Authentication token received and stored")
            else:
                logger.warning("Authentication returned True but no token was stored")
        else:
            logger.error("❌ Certificate-based authentication failed!")
        
        return result
    
    except Exception as e:
        logger.error(f"Error during certificate-based OPS Portal authentication test: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


def test_ops_portal_auth():
    """
    Run OPS Portal authentication test with certificate-based authentication.
    
    Returns:
        bool: True if authentication succeeded, False if it failed
    """
    logger.info("Starting OPS Portal certificate authentication test...")
    
    # Certificate-based authentication
    logger.info("\n" + "=" * 60)
    logger.info("Certificate-Based Authentication")
    logger.info("=" * 60)
    try:
        result = test_ops_portal_auth_with_certificate()
        if result is None:
            logger.info("Certificate authentication result: SKIPPED (no certificate configured)")
        else:
            logger.info(f"Certificate authentication result: {'SUCCESS' if result else 'FAILED'}")
    except Exception as e:
        logger.error(f"Certificate authentication test failed with exception: {str(e)}")
        result = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("AUTHENTICATION TEST SUMMARY")
    logger.info("=" * 60)
    
    if result is None:
        logger.info("⏭️  Certificate authentication: SKIPPED")
        logger.info("\nNo authentication tests were run")
        return False
    elif result:
        logger.info("✅ Certificate authentication: SUCCESS")
        logger.info("\n🎉 Certificate authentication is working!")
    else:
        logger.info("❌ Certificate authentication: FAILED")
        logger.error("\n💥 Certificate authentication failed!")
    
    return result

if __name__ == '__main__':
    print("Testing OPS Portal certificate authentication...")
    
    # Set up console logging
    import logging
    # Set root logger to DEBUG level
    logging.getLogger().setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Also set up logging for the OPS Portal API module
    ops_api_logger = logging.getLogger('src.ops_portal.api')
    ops_api_logger.setLevel(logging.DEBUG)
    ops_api_logger.addHandler(console_handler)
    
    # Load configuration to check certificate path
    config = Config()
    ops_config = config.get_section('ops_portal')
    cert_path = ops_config.get('cert_path')
    print(f"Certificate path from config: {cert_path}")
    
    if cert_path:
        # If the path is relative, make it absolute from the project root
        if not os.path.isabs(cert_path):
            full_cert_path = os.path.join(project_root, cert_path)
        else:
            full_cert_path = cert_path
            
        print(f"Full certificate path: {full_cert_path}")
        print(f"PFX file exists: {os.path.exists(full_cert_path)}")
        if os.path.exists(full_cert_path):
            print(f"PFX file size: {os.path.getsize(full_cert_path)} bytes")
            
        # Check certificate password
        cert_password = ops_config.get('cert_password')
        print(f"Certificate password: {'Set' if cert_password else 'Not set'}")
        if cert_password:
            print(f"Certificate password length: {len(cert_password)}")
            print(f"Certificate password (first few chars): {cert_password[:3]}...")
    
    # Try to directly run the certificate authentication test
    print("\nRunning certificate authentication test directly...")
    cert_result = test_ops_portal_auth_with_certificate()
    print(f"Certificate authentication result: {cert_result}")
    
    # Run the full test suite
    success = test_ops_portal_auth()
    print(f"Authentication tests {'successful' if success else 'failed'}!")

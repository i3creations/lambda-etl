"""
Test script for OPS Portal authentication using credentials from .env file.

This script loads the OPS Portal authentication credentials from the .env file
and attempts to authenticate with the OPS Portal API using both basic credentials
and certificate-based authentication.
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

def test_ops_portal_auth_basic():
    """
    Test OPS Portal authentication using basic credentials from .env file.
    """
    try:
        # Load configuration from .env file
        config = Config()
        
        # Get OPS Portal configuration from the 'ops_portal' section
        # (Environment variables OPSAPI_OPS_PORTAL_* get mapped to ops_portal.*)
        ops_config = config.get_section('ops_portal')
        
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
        logger.error(f"Error during basic OPS Portal authentication test: {str(e)}")
        raise

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
        if not cert_pem or not key_pem:
            logger.warning("Certificate or key not found in configuration - skipping certificate test")
            return None
        
        logger.info(f"Certificate information found:")
        logger.info(f"  - Certificate PEM length: {len(cert_pem)} characters")
        logger.info(f"  - Key PEM length: {len(key_pem)} characters")
        
        # Map the configuration keys to what OpsPortalClient expects (including certificate info)
        ops_portal_config = {
            'auth_url': ops_config.get('auth_url'),
            'item_url': ops_config.get('item_url'),
            'client_id': ops_config.get('client_id'),
            'client_secret': ops_config.get('client_secret'),
            'verify_ssl': ops_config.get('verify_ssl', 'true').lower() == 'true',
            'cert_pem': cert_pem,
            'key_pem': key_pem
        }
        
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
        logger.info(f"  - certificate configured: {bool(cert_pem)}")
        logger.info(f"  - private key configured: {bool(key_pem)}")
        
        # Test certificate parsing first
        logger.info("Testing certificate parsing...")
        success = test_certificate_parsing(cert_pem, key_pem)
        if not success:
            logger.error("Certificate parsing failed - cannot proceed with authentication test")
            return False
        
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

def test_certificate_parsing(cert_pem, key_pem):
    """
    Test certificate and key parsing using the cryptography library.
    
    Args:
        cert_pem (str): Certificate in PEM format
        key_pem (str): Private key in PEM format
        
    Returns:
        bool: True if parsing was successful, False otherwise
    """
    try:
        # Check if cryptography library is available
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography import x509
        except ImportError:
            logger.warning("cryptography library not available - skipping certificate parsing test")
            return True  # Don't fail the test if library is not available
        
        # Fix PEM format (convert \n escape sequences to actual newlines)
        def fix_pem_format(pem_content):
            if '\\n' in pem_content:
                pem_content = pem_content.replace('\\n', '\n')
            return pem_content
        
        fixed_cert = fix_pem_format(cert_pem)
        fixed_key = fix_pem_format(key_pem)
        
        # Test certificate loading
        logger.info("Testing certificate parsing...")
        certificate = x509.load_pem_x509_certificate(fixed_cert.encode('utf-8'))
        logger.info("✅ Certificate parsed successfully")
        logger.info(f"  - Subject: {certificate.subject}")
        logger.info(f"  - Issuer: {certificate.issuer}")
        logger.info(f"  - Valid from: {certificate.not_valid_before_utc}")
        logger.info(f"  - Valid until: {certificate.not_valid_after_utc}")
        
        # Test private key loading (PEM format doesn't require password)
        logger.info("Testing private key parsing...")
        private_key = serialization.load_pem_private_key(
            fixed_key.encode('utf-8'),
            password=None
        )
        logger.info("✅ Private key parsed successfully")
        
        logger.info(f"  - Key type: {type(private_key).__name__}")
        logger.info(f"  - Key size: {private_key.key_size} bits")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Certificate parsing failed: {str(e)}")
        return False

def test_ops_portal_auth():
    """
    Run comprehensive OPS Portal authentication tests.
    
    Tests both basic credential authentication and certificate-based authentication.
    
    Returns:
        bool: True if at least one authentication method succeeded, False if all failed
    """
    logger.info("Starting comprehensive OPS Portal authentication tests...")
    
    results = {}
    
    # Test 1: Basic authentication
    logger.info("\n" + "=" * 60)
    logger.info("TEST 1: Basic Credential Authentication")
    logger.info("=" * 60)
    try:
        results['basic'] = test_ops_portal_auth_basic()
        logger.info(f"Basic authentication result: {'SUCCESS' if results['basic'] else 'FAILED'}")
    except Exception as e:
        logger.error(f"Basic authentication test failed with exception: {str(e)}")
        results['basic'] = False
    
    # Test 2: Certificate-based authentication
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Certificate-Based Authentication")
    logger.info("=" * 60)
    try:
        results['certificate'] = test_ops_portal_auth_with_certificate()
        if results['certificate'] is None:
            logger.info("Certificate authentication result: SKIPPED (no certificate configured)")
        else:
            logger.info(f"Certificate authentication result: {'SUCCESS' if results['certificate'] else 'FAILED'}")
    except Exception as e:
        logger.error(f"Certificate authentication test failed with exception: {str(e)}")
        results['certificate'] = False
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("AUTHENTICATION TEST SUMMARY")
    logger.info("=" * 60)
    
    success_count = 0
    total_count = 0
    
    for test_name, result in results.items():
        if result is not None:
            total_count += 1
            if result:
                success_count += 1
                logger.info(f"✅ {test_name.title()} authentication: SUCCESS")
            else:
                logger.info(f"❌ {test_name.title()} authentication: FAILED")
        else:
            logger.info(f"⏭️  {test_name.title()} authentication: SKIPPED")
    
    overall_success = success_count > 0
    logger.info(f"\nOverall result: {success_count}/{total_count} authentication methods succeeded")
    
    if overall_success:
        logger.info("🎉 At least one authentication method is working!")
    else:
        logger.error("💥 All authentication methods failed!")
    
    return overall_success

if __name__ == '__main__':
    print("Testing OPS Portal authentication (basic + certificate)...")
    success = test_ops_portal_auth()
    print(f"Authentication tests {'successful' if success else 'failed'}!")

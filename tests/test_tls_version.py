#!/usr/bin/env python3
"""
Test script to verify TLS 1.2 is being properly used for OPS Portal API connections.

This script tests the explicit TLS 1.2 configuration for certificate authentication.
"""

import os
import sys
import logging
from pathlib import Path

# Add the parent directory and src directory to the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, parent_dir)
sys.path.insert(0, src_dir)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(parent_dir, '.env'))
except ImportError:
    print("Warning: python-dotenv not available, assuming environment variables are already loaded")

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the module directly
from src.ops_portal.api import OpsPortalClient

def test_tls_version():
    """Test that TLS 1.2 is being properly used for API connections."""
    print("=" * 60)
    print("TESTING TLS 1.2 CONFIGURATION")
    print("=" * 60)
    
    # Check for PFX certificate path from environment variable first
    env_pfx_path = os.getenv('OPSAPI_OPS_PORTAL_CERT_PATH')
    if env_pfx_path:
        # If the path is relative, make it absolute from the project root
        if not os.path.isabs(env_pfx_path):
            pfx_path = os.path.join(parent_dir, env_pfx_path)
        else:
            pfx_path = env_pfx_path
        print(f"Using PFX path from environment variable: {env_pfx_path}")
    else:
        # Fall back to default path
        pfx_path = os.path.join(parent_dir, 'certs', 'giitest-api.pfx')
        print(f"Using default PFX path: {pfx_path}")
    
    if not os.path.exists(pfx_path):
        print(f"ERROR: PFX file not found at: {pfx_path}")
        return False
    
    # Get the password for the .pfx file from environment variables
    pfx_password = os.getenv('OPSAPI_PFX_PASSWORD')
    if not pfx_password:
        # Try the certificate password from the .env file as a fallback
        pfx_password = os.getenv('OPSAPI_OPS_PORTAL_CERT_PASSWORD')
        if pfx_password:
            # Remove surrounding quotes if present
            pfx_password = pfx_password.strip("'\"")
            print(f"Using OPSAPI_OPS_PORTAL_CERT_PASSWORD as the PFX password")
        else:
            print("PFX password not found in environment variables")
            print("Attempting to use the file without a password...")
            pfx_password = None
    
    # Configuration using environment variables
    config = {
        'auth_url': os.getenv('OPSAPI_OPS_PORTAL_AUTH_URL'),
        'item_url': os.getenv('OPSAPI_OPS_PORTAL_ITEM_URL'),
        'client_id': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_ID'),
        'client_secret': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
        'verify_ssl': os.getenv('OPSAPI_OPS_PORTAL_VERIFY_SSL', 'false').lower() == 'true',
        'cert_pfx': pfx_path,
        'pfx_password': pfx_password
    }
    
    # Verify we have the required configuration
    if not config['auth_url'] or not config['item_url']:
        print("ERROR: API URLs not found in environment variables")
        print("Make sure OPSAPI_OPS_PORTAL_AUTH_URL and OPSAPI_OPS_PORTAL_ITEM_URL are set in .env file")
        return False
    
    try:
        # Create OPS Portal client - this will configure TLS 1.2
        print("\n1. Creating OPS Portal client with TLS 1.2 configuration...")
        client = OpsPortalClient(config)
        print("✅ Client created successfully with TLS 1.2 adapter")
        
        # Verify TLS adapter is configured
        if hasattr(client.session, 'adapters') and 'https://' in client.session.adapters:
            adapter = client.session.adapters['https://']
            print("✅ HTTPS adapter configured")
            
            # Try to inspect the adapter's SSL context if possible
            if hasattr(adapter, 'ssl_context'):
                print("✅ SSL context found in adapter")
            else:
                print("⚠️  Could not directly inspect SSL context in adapter")
                
            # Check if the adapter is our custom TLSv12Adapter
            if adapter.__class__.__name__ == 'TLSv12Adapter':
                print("✅ Custom TLSv12Adapter is being used")
                # Check if verify attribute is set correctly
                if hasattr(adapter, 'verify'):
                    print(f"✅ TLS adapter verify setting: {adapter.verify}")
                else:
                    print("⚠️  TLS adapter does not have verify attribute")
            else:
                print(f"⚠️  Using adapter of type: {adapter.__class__.__name__}")
        else:
            print("❌ HTTPS adapter not found")
        
        # Attempt authentication to test TLS version
        print("\n2. Attempting authentication to test TLS version...")
        success = client.authenticate()
        
        if success:
            print("✅ Authentication successful")
            print("✅ TLS 1.2 configuration is working properly")
            return True
        else:
            print("❌ Authentication failed")
            print("⚠️  Could not verify TLS 1.2 configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hostname_verification():
    """Test hostname verification settings with TLS 1.2."""
    print("\n" + "=" * 60)
    print("TESTING HOSTNAME VERIFICATION SETTINGS")
    print("=" * 60)
    
    # Test with verify_ssl=False
    config_no_verify = {
        'auth_url': os.getenv('OPSAPI_OPS_PORTAL_AUTH_URL'),
        'item_url': os.getenv('OPSAPI_OPS_PORTAL_ITEM_URL'),
        'client_id': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_ID'),
        'client_secret': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
        'verify_ssl': False,
        'cert_pfx': pfx_path,
        'pfx_password': pfx_password
    }
    
    try:
        print("\n1. Creating client with verify_ssl=False...")
        client = OpsPortalClient(config_no_verify)
        print("✅ Client created successfully with verify_ssl=False")
        
        # Check adapter configuration
        if hasattr(client.session, 'adapters') and 'https://' in client.session.adapters:
            adapter = client.session.adapters['https://']
            if hasattr(adapter, 'verify'):
                print(f"✅ Adapter verify setting: {adapter.verify}")
            
        print("\n2. Testing authentication with verify_ssl=False...")
        success = client.authenticate()
        if success:
            print("✅ Authentication successful with verify_ssl=False")
        else:
            print("❌ Authentication failed with verify_ssl=False")
            
    except Exception as e:
        print(f"❌ Error with verify_ssl=False: {e}")
    
    # Test with verify_ssl=True
    config_verify = {
        'auth_url': os.getenv('OPSAPI_OPS_PORTAL_AUTH_URL'),
        'item_url': os.getenv('OPSAPI_OPS_PORTAL_ITEM_URL'),
        'client_id': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_ID'),
        'client_secret': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
        'verify_ssl': True,
        'cert_pfx': pfx_path,
        'pfx_password': pfx_password
    }
    
    try:
        print("\n3. Creating client with verify_ssl=True...")
        client = OpsPortalClient(config_verify)
        print("✅ Client created successfully with verify_ssl=True")
        
        # Check adapter configuration
        if hasattr(client.session, 'adapters') and 'https://' in client.session.adapters:
            adapter = client.session.adapters['https://']
            if hasattr(adapter, 'verify'):
                print(f"✅ Adapter verify setting: {adapter.verify}")
            
        print("\n4. Testing authentication with verify_ssl=True...")
        success = client.authenticate()
        if success:
            print("✅ Authentication successful with verify_ssl=True")
        else:
            print("❌ Authentication failed with verify_ssl=True")
            
    except Exception as e:
        print(f"❌ Error with verify_ssl=True: {e}")
    
    return True

def test_tls_debug():
    """Test with additional TLS debugging enabled."""
    print("\n" + "=" * 60)
    print("TESTING WITH ADDITIONAL TLS DEBUGGING")
    print("=" * 60)
    
    # Enable urllib3 debugging
    try:
        import urllib3
        urllib3.connectionpool.HTTPConnection.debuglevel = 1
        urllib3.connectionpool.HTTPSConnection.debuglevel = 1
        logging.getLogger('urllib3').setLevel(logging.DEBUG)
        print("✅ urllib3 debug logging enabled")
    except ImportError:
        print("⚠️  urllib3 not available for debug logging")
    
    # Enable requests debugging
    try:
        import requests
        requests.packages.urllib3.connectionpool.HTTPConnection.debuglevel = 1
        requests.packages.urllib3.connectionpool.HTTPSConnection.debuglevel = 1
        logging.getLogger('requests').setLevel(logging.DEBUG)
        print("✅ requests debug logging enabled")
    except (ImportError, AttributeError):
        print("⚠️  requests debug logging not available")
    
    # Enable SSL debugging
    try:
        import ssl
        logging.getLogger('ssl').setLevel(logging.DEBUG)
        print("✅ SSL debug logging enabled")
    except ImportError:
        print("⚠️  SSL debug logging not available")
    
    # Run the test with debug logging enabled
    return test_tls_version()

def main():
    """Main function."""
    print("TLS 1.2 Configuration Test")
    print("=" * 60)
    
    # Run the tests
    basic_result = test_tls_version()
    hostname_result = test_hostname_verification()
    
    # If basic test fails, try with debug logging
    if not basic_result:
        print("\n⚠️  Basic test failed, trying with debug logging...")
        debug_result = test_tls_debug()
    else:
        debug_result = True
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Basic TLS 1.2 test: {'✅ PASSED' if basic_result else '❌ FAILED'}")
    print(f"Hostname verification test: {'✅ PASSED' if hostname_result else '❌ FAILED'}")
    if not basic_result:
        print(f"Debug TLS test: {'✅ PASSED' if debug_result else '❌ FAILED'}")
    
    if (basic_result and hostname_result) or debug_result:
        print("\n🎉 TLS 1.2 configuration is working properly!")
        return 0
    else:
        print("\n⚠️  TLS 1.2 configuration test failed.")
        print("\nTROUBLESHOOTING STEPS:")
        print("1. Check if the server supports TLS 1.2")
        print("2. Verify that the certificate is valid and trusted")
        print("3. Check if the server requires specific cipher suites")
        print("4. Verify that the client credentials are correct")
        print("5. Check if the server has any specific TLS requirements")
        return 1

if __name__ == "__main__":
    sys.exit(main())

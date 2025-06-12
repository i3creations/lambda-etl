#!/usr/bin/env python3
"""
Test script to verify the updated OpsPortalClient with PFX certificate support.

This script tests the OpsPortalClient's ability to use a PKCS#12 (.pfx) file
with the complete certificate chain for authentication.
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

# Import the OpsPortalClient
from src.ops_portal.api import OpsPortalClient

def test_pfx_client():
    """
    Test the OpsPortalClient with a PFX certificate.
    """
    print("=" * 60)
    print("TESTING OPSPROTALCLIENT WITH PFX CERTIFICATE")
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
        print(f"❌ PFX file not found at: {pfx_path}")
        return False
    
    print(f"1. Found PFX file: {pfx_path}")
    
    # Get the password for the .pfx file from environment variables
    pfx_password = os.getenv('OPSAPI_PFX_PASSWORD')
    if not pfx_password:
        # Try the certificate password from the .env file as a fallback
        pfx_password = os.getenv('OPSAPI_OPS_PORTAL_CERT_PASSWORD')
        if pfx_password:
            # Remove surrounding quotes if present
            pfx_password = pfx_password.strip("'\"")
            print(f"⚠️  Using OPSAPI_OPS_PORTAL_CERT_PASSWORD as the PFX password")
        else:
            print("⚠️  PFX password not found in environment variables")
            print("   Attempting to use the file without a password...")
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
    
    try:
        # Create the OPS Portal client with PFX certificate
        print("\n2. Creating client with PFX certificate...")
        client = OpsPortalClient(config)
        print("✅ Client created successfully with PFX certificate")
        
        # Log certificate format details
        print("\n3. Logging certificate format details...")
        client.log_certificate_format_details()
        
        # Define the target URL
        target_url = "https://giitest-api.dhs.gov/default.htm"
        print(f"\n4. Preparing to send request to: {target_url}")
        
        # Send a direct request using the configured session
        print("\n5. Sending request with certificate authentication...")
        # Add Accept header to specify acceptable content types
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = client.session.get(
            target_url,
            headers=headers,
            timeout=30  # Add timeout to prevent hanging
        )
        
        # Log the response details
        print(f"\n6. Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        # Log TLS version if available
        if hasattr(response.raw, 'connection') and hasattr(response.raw.connection, 'socket'):
            tls_version = response.raw.connection.socket.version()
            print(f"TLS version used: {tls_version}")
        
        # Check if the request was successful
        if 200 <= response.status_code < 300:
            print("✅ Request successful!")
            print("\nResponse content (first 500 chars):")
            content = response.text
            print(content[:500] + "..." if len(content) > 500 else content)
            return True
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print("\nResponse content (first 500 chars):")
            content = response.text
            print(content[:500] + "..." if len(content) > 500 else content)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pfx_client()

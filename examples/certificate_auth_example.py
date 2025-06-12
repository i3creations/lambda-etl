#!/usr/bin/env python3
"""
Example script demonstrating certificate authentication with TLS 1.2 for OPS Portal API.

This script shows how to properly configure and use certificate authentication
with explicit TLS 1.2 configuration when connecting to the OPS Portal API.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
except ImportError:
    print("Warning: python-dotenv not available, assuming environment variables are already loaded")

# Import the OpsPortalClient
from src.ops_portal.api import OpsPortalClient

def main():
    """
    Main function demonstrating certificate authentication with TLS 1.2.
    """
    print("Certificate Authentication Example with TLS 1.2")
    print("=" * 60)
    
    # Load configuration from environment variables
    config = {
        'auth_url': os.environ.get('OPSAPI_OPS_PORTAL_AUTH_URL'),
        'item_url': os.environ.get('OPSAPI_OPS_PORTAL_ITEM_URL'),
        'client_id': os.environ.get('OPSAPI_OPS_PORTAL_CLIENT_ID'),
        'client_secret': os.environ.get('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
        'verify_ssl': os.environ.get('OPSAPI_OPS_PORTAL_VERIFY_SSL', 'false').lower() == 'true',
    }
    
    # Check for PFX certificate path
    cert_path = os.environ.get('OPSAPI_OPS_PORTAL_CERT_PATH')
    if cert_path:
        # Use the PFX certificate file
        config['cert_pfx'] = cert_path
        config['pfx_password'] = os.environ.get('OPSAPI_OPS_PORTAL_CERT_PASSWORD')
        print(f"Using PFX certificate from OPSAPI_OPS_PORTAL_CERT_PATH: {cert_path}")
    else:
        print("No PFX certificate path found in environment variables")
        print("Please set OPSAPI_OPS_PORTAL_CERT_PATH in .env file")
    
    # Verify required configuration is present
    required_keys = ['auth_url', 'item_url', 'cert_pfx']
    
    missing_config = [key for key in required_keys if key not in config or not config.get(key)]
    
    if missing_config:
        print(f"Error: Missing required configuration: {', '.join(missing_config)}")
        print("Please set the required environment variables in .env file")
        return 1
    
    try:
        # Step 1: Create the OPS Portal client
        # This will automatically configure TLS 1.2 for all HTTPS connections
        print("\n1. Creating OPS Portal client with TLS 1.2 configuration...")
        client = OpsPortalClient(config)
        print("✅ Client created successfully")
        
        # Check if TLS 1.2 adapter is configured
        if hasattr(client.session, 'adapters') and 'https://' in client.session.adapters:
            adapter = client.session.adapters['https://']
            if adapter.__class__.__name__ == 'TLSv12Adapter':
                print("✅ TLS 1.2 adapter configured")
                if hasattr(adapter, 'verify'):
                    print(f"✅ SSL verification setting: {adapter.verify}")
            else:
                print(f"⚠️  Using adapter of type: {adapter.__class__.__name__}")
        
        # Step 2: Authenticate with the API
        print("\n2. Authenticating with OPS Portal API...")
        auth_success = client.authenticate()
        
        if not auth_success:
            print("❌ Authentication failed")
            return 1
            
        print("✅ Authentication successful")
        
        # Step 3: Log TLS version information
        print("\n3. TLS configuration information:")
        print(f"  - SSL verification enabled: {config['verify_ssl']}")
        print(f"  - Certificate configured: {bool(client.session.cert)}")
        print(f"  - Using TLS 1.2 for HTTPS connections")
        
        # Step 4: Send a test record
        print("\n4. Sending a test record...")
        test_record = {
            'tenantItemID': 'test_record_001',
            'title': 'TLS 1.2 Certificate Authentication Test',
            'description': 'This is a test record sent using TLS 1.2 with certificate authentication',
            'status': 'Test',
            'priority': 'Low',
            'category': 'Test',
            'reportedDate': '2025-06-12T20:00:00Z'
        }
        
        status_code, response = client.send_record(test_record)
        
        if 200 <= status_code < 300:
            print(f"✅ Record sent successfully (Status: {status_code})")
            print(f"Response: {response}")
        else:
            print(f"❌ Failed to send record (Status: {status_code})")
            print(f"Error: {response}")
            
        print("\n5. Example completed")
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

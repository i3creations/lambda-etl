#!/usr/bin/env python3
"""
Test script to demonstrate X509 certificate format logging for OPS API.

This script shows how the enhanced logging captures detailed x509 certificate
format information when sending data to the OPS Portal API.
"""

import sys
import os
import logging
from dotenv import load_dotenv

# Add the parent directory and src directory to the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, parent_dir)
sys.path.insert(0, src_dir)

# Load environment variables from .env file
load_dotenv(os.path.join(parent_dir, '.env'))

# Import the module directly to avoid relative import issues
try:
    from src.ops_portal.api import OpsPortalClient
except ImportError:
    # Fallback import method
    import importlib.util
    spec = importlib.util.spec_from_file_location("ops_portal.api", os.path.join(src_dir, "ops_portal", "api.py"))
    ops_api_module = importlib.util.module_from_spec(spec)
    
    # Mock the relative import for logging_utils
    sys.modules['src'] = type(sys)('src')
    sys.modules['src.utils'] = type(sys)('src.utils')
    
    # Create a simple logger function to replace the relative import
    def get_logger(name):
        return logging.getLogger(name)
    
    sys.modules['src.utils.logging_utils'] = type(sys)('src.utils.logging_utils')
    sys.modules['src.utils.logging_utils'].get_logger = get_logger
    
    spec.loader.exec_module(ops_api_module)
    OpsPortalClient = ops_api_module.OpsPortalClient

# Set up logging to see the output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_x509_logging():
    """Test the X509 certificate format logging functionality."""
    
    print("=== Testing X509 Certificate Format Logging ===")
    
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
        return
    
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
    
    try:
        # Create OPS Portal client - this will trigger certificate format logging
        print("\n1. Creating OPS Portal client...")
        client = OpsPortalClient(config)
        
        # Call the log_certificate_format_details method
        print("\n2. Logging certificate format details...")
        client.log_certificate_format_details()
        
        # Example record to send (this will show certificate usage logging)
        test_record = {
            'tenantItemID': 'test_record_001',
            'title': 'Test Record for X509 Logging',
            'description': 'This is a test record to demonstrate X509 certificate logging'
        }
        
        print("\n3. Attempting to send test record (will show certificate usage logging)...")
        # This will show the certificate usage logging in send_record method
        status_code, response = client.send_record(test_record)
        print(f"Response: Status {status_code}, Data: {response}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
        print("This demonstrates the X509 certificate logging functionality!")

if __name__ == "__main__":
    test_x509_logging()

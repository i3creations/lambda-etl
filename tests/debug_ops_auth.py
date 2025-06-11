#!/usr/bin/env python3
"""
Debug script for OPS Portal authentication issues.
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
    load_dotenv(project_root / '.env')
except ImportError:
    print("Warning: python-dotenv not available, assuming environment variables are already loaded")

# Set up logging
logger = get_logger('debug_ops_auth')

def debug_configuration():
    """Debug the configuration loading."""
    print("=" * 60)
    print("CONFIGURATION DEBUG")
    print("=" * 60)
    
    # Load configuration
    config = Config()
    ops_config = config.get_section('ops_portal')
    
    print(f"Available configuration sections: {list(config.get_all().keys())}")
    print(f"OPS Portal config keys: {list(ops_config.keys())}")
    
    # Check required fields
    required_fields = ['auth_url', 'item_url', 'client_id', 'client_secret']
    for field in required_fields:
        value = ops_config.get(field)
        if value:
            if field in ['client_secret']:
                print(f"✅ {field}: {value[:8]}... (truncated)")
            else:
                print(f"✅ {field}: {value}")
        else:
            print(f"❌ {field}: MISSING")
    
    # Check certificate fields
    cert_fields = ['cert_pem', 'key_pem']
    for field in cert_fields:
        value = ops_config.get(field)
        if value:
            print(f"✅ {field}: {len(value)} characters")
        else:
            print(f"❌ {field}: MISSING")
    
    # Check SSL verification
    verify_ssl = ops_config.get('verify_ssl', 'true').lower() == 'true'
    print(f"✅ verify_ssl: {verify_ssl}")
    
    return ops_config

def debug_certificate():
    """Debug certificate parsing."""
    print("\n" + "=" * 60)
    print("CERTIFICATE DEBUG")
    print("=" * 60)
    
    config = Config()
    ops_config = config.get_section('ops_portal')
    
    cert_pem = ops_config.get('cert_pem')
    key_pem = ops_config.get('key_pem')
    
    if not cert_pem or not key_pem:
        print("❌ Certificate or key not found in configuration")
        return False
    
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography import x509
        
        # Fix PEM format
        def fix_pem_format(pem_content):
            if '\\n' in pem_content:
                pem_content = pem_content.replace('\\n', '\n')
            return pem_content
        
        fixed_cert = fix_pem_format(cert_pem)
        fixed_key = fix_pem_format(key_pem)
        
        # Test certificate loading
        print("Testing certificate parsing...")
        certificate = x509.load_pem_x509_certificate(fixed_cert.encode('utf-8'))
        print("✅ Certificate parsed successfully")
        print(f"  - Subject: {certificate.subject}")
        print(f"  - Issuer: {certificate.issuer}")
        print(f"  - Valid from: {certificate.not_valid_before_utc}")
        print(f"  - Valid until: {certificate.not_valid_after_utc}")
        
        # Check if certificate is expired
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if now < certificate.not_valid_before_utc:
            print("⚠️  Certificate is not yet valid")
        elif now > certificate.not_valid_after_utc:
            print("❌ Certificate has expired")
        else:
            print("✅ Certificate is currently valid")
        
        # Test private key loading (PEM format doesn't require password)
        print("Testing private key parsing...")
        private_key = serialization.load_pem_private_key(
            fixed_key.encode('utf-8'),
            password=None
        )
        print("✅ Private key parsed successfully")
        
        print(f"  - Key type: {type(private_key).__name__}")
        print(f"  - Key size: {private_key.key_size} bits")
        
        return True
        
    except ImportError:
        print("❌ cryptography library not available")
        return False
    except Exception as e:
        print(f"❌ Certificate parsing failed: {str(e)}")
        return False

def debug_network_connectivity():
    """Debug network connectivity to the OPS Portal."""
    print("\n" + "=" * 60)
    print("NETWORK CONNECTIVITY DEBUG")
    print("=" * 60)
    
    config = Config()
    ops_config = config.get_section('ops_portal')
    auth_url = ops_config.get('auth_url')
    
    if not auth_url:
        print("❌ No auth_url configured")
        return False
    
    print(f"Testing connectivity to: {auth_url}")
    
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        # Test basic connectivity (without authentication)
        response = requests.get(auth_url.replace('/api/auth/token', '/'), 
                              verify=False, timeout=10)
        print(f"✅ Basic connectivity successful (HTTP {response.status_code})")
        
        # Test the auth endpoint specifically
        response = requests.post(auth_url, 
                               json={'clientId': 'test', 'clientSecret': 'test'},
                               verify=False, timeout=10)
        print(f"✅ Auth endpoint reachable (HTTP {response.status_code})")
        
        if response.status_code == 401:
            print("  - Expected 401 for invalid credentials")
        elif response.status_code == 403:
            print("  - 403 Forbidden - may require client certificate")
        elif response.status_code >= 500:
            print("  - Server error - service may be down")
        
        return True
        
    except requests.exceptions.ConnectTimeout:
        print("❌ Connection timeout - service may be down")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        return False

def debug_authentication():
    """Debug the authentication process step by step."""
    print("\n" + "=" * 60)
    print("AUTHENTICATION DEBUG")
    print("=" * 60)
    
    config = Config()
    ops_config = config.get_section('ops_portal')
    
    # Map the configuration keys to what OpsPortalClient expects
    ops_portal_config = {
        'auth_url': ops_config.get('auth_url'),
        'item_url': ops_config.get('item_url'),
        'client_id': ops_config.get('client_id'),
        'client_secret': ops_config.get('client_secret'),
        'verify_ssl': ops_config.get('verify_ssl', 'true').lower() == 'true',
        'cert_pem': ops_config.get('cert_pem'),
        'key_pem': ops_config.get('key_pem')
    }
    
    print("Creating OPS Portal client...")
    try:
        client = OpsPortalClient(ops_portal_config)
        print("✅ Client created successfully")
        
        # Check if certificate is configured
        if hasattr(client.session, 'cert') and client.session.cert:
            print("✅ SSL client certificate configured")
        else:
            print("⚠️  No SSL client certificate configured")
        
        print("Attempting authentication...")
        result = client.authenticate()
        
        if result:
            print("✅ Authentication successful!")
            if client.token:
                print(f"✅ Token received (length: {len(str(client.token))})")
            else:
                print("⚠️  Authentication returned True but no token stored")
        else:
            print("❌ Authentication failed")
        
        return result
        
    except Exception as e:
        print(f"❌ Authentication debug failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Main debug function."""
    print("OPS Portal Authentication Debug Tool")
    print("=" * 60)
    
    # Step 1: Debug configuration
    ops_config = debug_configuration()
    
    # Step 2: Debug certificate
    cert_ok = debug_certificate()
    
    # Step 3: Debug network connectivity
    network_ok = debug_network_connectivity()
    
    # Step 4: Debug authentication
    auth_ok = debug_authentication()
    
    # Summary
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY")
    print("=" * 60)
    print(f"Configuration: {'✅ OK' if ops_config else '❌ FAILED'}")
    print(f"Certificate: {'✅ OK' if cert_ok else '❌ FAILED'}")
    print(f"Network: {'✅ OK' if network_ok else '❌ FAILED'}")
    print(f"Authentication: {'✅ OK' if auth_ok else '❌ FAILED'}")
    
    if not auth_ok:
        print("\n🔍 TROUBLESHOOTING SUGGESTIONS:")
        if not cert_ok:
            print("- Fix certificate configuration issues")
        if not network_ok:
            print("- Check network connectivity to OPS Portal")
        print("- Verify client credentials are correct")
        print("- Check if the service requires specific certificate authentication")
        print("- Confirm the auth_url is correct and accessible")

if __name__ == '__main__':
    main()

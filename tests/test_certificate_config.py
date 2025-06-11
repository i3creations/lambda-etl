#!/usr/bin/env python3
"""
Test script to verify certificate configuration is working properly.

This script tests the certificate handling implementation across different environments.
"""

import os
import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import get_config
from src.ops_portal.api import OpsPortalClient
from src.utils.logging_utils import setup_logging

def test_development_config():
    """Test certificate configuration in development environment."""
    print("=" * 60)
    print("Testing Development Environment Configuration")
    print("=" * 60)
    
    # Load .env file
    from dotenv import load_dotenv
    load_dotenv('.env')
    
    # Get configuration
    config = get_config()
    ops_portal_config = config.get_section('ops_portal')
    
    print(f"Configuration loaded:")
    print(f"  - auth_url: {ops_portal_config.get('auth_url')}")
    print(f"  - item_url: {ops_portal_config.get('item_url')}")
    print(f"  - client_id: {ops_portal_config.get('client_id')}")
    print(f"  - verify_ssl: {ops_portal_config.get('verify_ssl')}")
    print(f"  - cert_pem present: {'cert_pem' in ops_portal_config and bool(ops_portal_config.get('cert_pem'))}")
    print(f"  - key_pem present: {'key_pem' in ops_portal_config and bool(ops_portal_config.get('key_pem'))}")
    print(f"  - cert_password present: {'cert_password' in ops_portal_config and bool(ops_portal_config.get('cert_password'))}")
    
    # Test OpsPortalClient initialization
    try:
        client = OpsPortalClient(ops_portal_config)
        print("✅ OpsPortalClient initialized successfully")
        print(f"  - Certificate configured: {hasattr(client.session, 'cert') and client.session.cert is not None}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize OpsPortalClient: {str(e)}")
        return False

def test_aws_secrets_config():
    """Test certificate configuration with AWS Secrets Manager format."""
    print("\n" + "=" * 60)
    print("Testing AWS Secrets Manager Configuration Format")
    print("=" * 60)
    
    # Simulate AWS Secrets Manager configuration
    from src.utils.secrets_manager import load_config_from_secrets
    
    # Mock configuration that would come from AWS Secrets
    mock_config = {
        'ops_portal': {
            'auth_url': 'https://giitest-api.dhs.gov/dhsopsportal.api/api/auth/token',
            'item_url': 'https://giitest-api.dhs.gov/dhsopsportal.api/api/Item',
            'client_id': 'test-client-id',
            'client_secret': 'test-client-secret',
            'verify_ssl': True,
            'cert_pem': os.environ.get('OPSAPI_OPS_PORTAL_CERT_PEM', ''),
            'key_pem': os.environ.get('OPSAPI_OPS_PORTAL_KEY_PEM', ''),
            'cert_password': os.environ.get('OPSAPI_OPS_PORTAL_CERT_PASSWORD', '')
        }
    }
    
    ops_portal_config = mock_config['ops_portal']
    
    print(f"Mock AWS Secrets configuration:")
    print(f"  - auth_url: {ops_portal_config.get('auth_url')}")
    print(f"  - item_url: {ops_portal_config.get('item_url')}")
    print(f"  - client_id: {ops_portal_config.get('client_id')}")
    print(f"  - verify_ssl: {ops_portal_config.get('verify_ssl')}")
    print(f"  - cert_pem present: {bool(ops_portal_config.get('cert_pem'))}")
    print(f"  - key_pem present: {bool(ops_portal_config.get('key_pem'))}")
    print(f"  - cert_password present: {bool(ops_portal_config.get('cert_password'))}")
    
    # Test OpsPortalClient initialization
    try:
        client = OpsPortalClient(ops_portal_config)
        print("✅ OpsPortalClient initialized successfully with AWS Secrets format")
        print(f"  - Certificate configured: {hasattr(client.session, 'cert') and client.session.cert is not None}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize OpsPortalClient with AWS Secrets format: {str(e)}")
        return False

def test_certificate_password_handling():
    """Test certificate password handling specifically."""
    print("\n" + "=" * 60)
    print("Testing Certificate Password Handling")
    print("=" * 60)
    
    cert_pem = os.environ.get('OPSAPI_OPS_PORTAL_CERT_PEM', '')
    key_pem = os.environ.get('OPSAPI_OPS_PORTAL_KEY_PEM', '')
    cert_password = os.environ.get('OPSAPI_OPS_PORTAL_CERT_PASSWORD', '')
    
    if not cert_pem or not key_pem:
        print("⚠️  Certificate or key not found in environment variables")
        return False
    
    print(f"Certificate details:")
    print(f"  - Certificate length: {len(cert_pem)} characters")
    print(f"  - Key length: {len(key_pem)} characters")
    print(f"  - Password provided: {bool(cert_password)}")
    
    # Test with cryptography library
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography import x509
        
        # Try to load the certificate
        cert_bytes = cert_pem.encode('utf-8')
        certificate = x509.load_pem_x509_certificate(cert_bytes)
        print("✅ Certificate loaded successfully")
        print(f"  - Subject: {certificate.subject}")
        print(f"  - Issuer: {certificate.issuer}")
        
        # Try to load the private key
        if cert_password:
            try:
                private_key = serialization.load_pem_private_key(
                    key_pem.encode('utf-8'),
                    password=cert_password.encode('utf-8')
                )
                print("✅ Private key loaded successfully with password")
            except Exception as e:
                print(f"❌ Failed to load private key with password: {str(e)}")
                # Try without password
                try:
                    private_key = serialization.load_pem_private_key(
                        key_pem.encode('utf-8'),
                        password=None
                    )
                    print("✅ Private key loaded successfully without password")
                except Exception as e2:
                    print(f"❌ Failed to load private key without password: {str(e2)}")
                    return False
        else:
            private_key = serialization.load_pem_private_key(
                key_pem.encode('utf-8'),
                password=None
            )
            print("✅ Private key loaded successfully (no password)")
        
        return True
        
    except ImportError:
        print("❌ cryptography library not available")
        return False
    except Exception as e:
        print(f"❌ Failed to load certificate/key: {str(e)}")
        return False

def main():
    """Main test function."""
    print("Certificate Configuration Test Suite")
    print("=" * 60)
    
    # Set up logging
    setup_logging(log_level=logging.INFO)
    
    # Run tests
    results = []
    
    results.append(test_development_config())
    results.append(test_aws_secrets_config())
    results.append(test_certificate_password_handling())
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Certificate configuration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

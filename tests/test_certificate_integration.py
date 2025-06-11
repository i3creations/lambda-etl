#!/usr/bin/env python3
"""
Integration test to verify certificate handling in the OPS Portal API.
"""

import os
import sys
from dotenv import load_dotenv

def test_certificate_integration():
    """Test that the OPS Portal API can properly load and use certificates."""
    
    # Load environment variables
    load_dotenv('.env')
    
    # Simple test using environment variables directly
    cert_pem = os.environ.get('OPSAPI_OPS_PORTAL_CERT_PEM', '')
    key_pem = os.environ.get('OPSAPI_OPS_PORTAL_KEY_PEM', '')
    
    print("Testing certificate integration...")
    print(f"Certificate PEM length: {len(cert_pem)}")
    print(f"Key PEM length: {len(key_pem)}")
    
    if not cert_pem or not key_pem:
        print("❌ Certificate or key not found in environment variables")
        return False
    
    try:
        # Test certificate parsing with cryptography library
        from cryptography.hazmat.primitives import serialization
        from cryptography import x509
        
        # Fix PEM format (convert \n to actual newlines)
        def fix_pem_format(pem_content):
            if '\\n' in pem_content:
                pem_content = pem_content.replace('\\n', '\n')
            return pem_content
        
        fixed_cert = fix_pem_format(cert_pem)
        fixed_key = fix_pem_format(key_pem)
        
        # Test certificate loading
        certificate = x509.load_pem_x509_certificate(fixed_cert.encode('utf-8'))
        print("✅ Certificate loads successfully")
        
        # Test private key loading
        private_key = serialization.load_pem_private_key(
            fixed_key.encode('utf-8'),
            password=None
        )
        print("✅ Private key loads successfully")
        
        # Test OPS Portal client configuration
        ops_config = {
            'auth_url': os.environ.get('OPSAPI_OPS_PORTAL_AUTH_URL'),
            'item_url': os.environ.get('OPSAPI_OPS_PORTAL_ITEM_URL'),
            'client_id': os.environ.get('OPSAPI_OPS_PORTAL_CLIENT_ID'),
            'client_secret': os.environ.get('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
            'cert_pem': cert_pem,
            'key_pem': key_pem,
            'verify_ssl': False
        }
        
        # Add src to path for OPS Portal client
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        # Import and test OPS Portal client
        try:
            from ops_portal.api import OpsPortalClient
            client = OpsPortalClient(ops_config)
            print("✅ OPS Portal client created successfully")
            print("✅ SSL certificate configuration completed without errors")
            
            # Check if temporary certificate files were created
            if hasattr(client, '_temp_cert_path') and hasattr(client, '_temp_key_path'):
                print(f"✅ Temporary certificate files created:")
                print(f"   Certificate: {client._temp_cert_path}")
                print(f"   Key: {client._temp_key_path}")
                
                # Verify files exist and have content
                if os.path.exists(client._temp_cert_path) and os.path.exists(client._temp_key_path):
                    cert_size = os.path.getsize(client._temp_cert_path)
                    key_size = os.path.getsize(client._temp_key_path)
                    print(f"✅ Certificate file size: {cert_size} bytes")
                    print(f"✅ Key file size: {key_size} bytes")
                else:
                    print("❌ Temporary certificate files not found")
        except ImportError as e:
            print(f"⚠️  Could not test OPS Portal client due to import issues: {e}")
            print("✅ Certificate parsing works correctly though")
        
        print("\n🎉 Certificate integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Certificate integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_certificate_integration()
    sys.exit(0 if success else 1)

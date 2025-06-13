#!/usr/bin/env python3
"""
Test script to verify certificate loading from AWS Secrets Manager.

This script tests the ability to load a PKCS#12 certificate from AWS Secrets Manager
when running in AWS Lambda, and from the file system when running locally.
"""

import os
import sys
import logging
import base64
import tempfile
from pathlib import Path
from unittest import mock

# Add the parent directory and src directory to the path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, parent_dir)
sys.path.insert(0, src_dir)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the modules to test
from src.utils.secrets_manager import load_config_from_secrets
from src.ops_portal.api import OpsPortalClient

def test_aws_secrets_certificate():
    """
    Test loading a certificate from AWS Secrets Manager.
    """
    print("=" * 60)
    print("TESTING CERTIFICATE LOADING FROM AWS SECRETS MANAGER")
    print("=" * 60)
    
    # Mock the SecretsManager.get_secret method to return a mock secret
    with mock.patch('src.utils.secrets_manager.SecretsManager.get_secret') as mock_get_secret:
        # Create a mock certificate
        with tempfile.NamedTemporaryFile(suffix='.pfx', delete=False) as temp_cert:
            temp_cert.write(b'MOCK_CERTIFICATE_DATA')
            temp_cert_path = temp_cert.name
        
        try:
            # Read the mock certificate data
            with open(temp_cert_path, 'rb') as f:
                cert_data = f.read()
            
            # Create a mock secret with the certificate data
            mock_secret = {
                'OPSAPI_OPS_PORTAL_AUTH_URL': 'https://mock-auth-url.example.com',
                'OPSAPI_OPS_PORTAL_ITEM_URL': 'https://mock-item-url.example.com',
                'OPSAPI_OPS_PORTAL_CLIENT_ID': 'mock-client-id',
                'OPSAPI_OPS_PORTAL_CLIENT_SECRET': 'mock-client-secret',
                'OPSAPI_OPS_PORTAL_VERIFY_SSL': 'false',
                'OPSAPI_OPS_PORTAL_CERT_PFX': base64.b64encode(cert_data).decode('utf-8'),
                'OPSAPI_OPS_PORTAL_PFX_PASSWORD': 'mock-password'
            }
            
            # Configure the mock to return our mock secret
            mock_get_secret.return_value = mock_secret
            
            # Set environment variable to simulate AWS Lambda environment
            os.environ['AWS_EXECUTION_ENV'] = 'AWS_Lambda_python3.9'
            os.environ['ENVIRONMENT'] = 'production'
            
            print("\n1. Loading configuration from AWS Secrets Manager...")
            config = load_config_from_secrets()
            
            print("\n2. Verifying certificate data was loaded...")
            assert 'cert_pfx_data' in config['ops_portal'], "Certificate data not found in config"
            assert config['ops_portal']['pfx_password'] == 'mock-password', "Certificate password not found in config"
            
            print("✅ Certificate data loaded from AWS Secrets Manager")
            
            print("\n3. Creating OpsPortalClient with certificate data...")
            # Mock the pkcs12.load_key_and_certificates function to avoid actual certificate parsing
            with mock.patch('cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates') as mock_load:
                # Create mock return values for the load_key_and_certificates function
                mock_private_key = mock.MagicMock()
                mock_certificate = mock.MagicMock()
                mock_certificate.subject = "CN=Mock Certificate"
                mock_certificate.issuer = "CN=Mock Issuer"
                # Configure the public_bytes method to return bytes
                mock_certificate.public_bytes.return_value = b"-----BEGIN CERTIFICATE-----\nMOCK CERTIFICATE\n-----END CERTIFICATE-----\n"
                mock_private_key.private_bytes.return_value = b"-----BEGIN PRIVATE KEY-----\nMOCK PRIVATE KEY\n-----END PRIVATE KEY-----\n"
                mock_additional_certs = []
                if mock_additional_certs:  # This is just to avoid an empty list check
                    mock_additional_cert = mock.MagicMock()
                    mock_additional_cert.subject = "CN=Mock Intermediate"
                    mock_additional_cert.public_bytes.return_value = b"-----BEGIN CERTIFICATE-----\nMOCK INTERMEDIATE\n-----END CERTIFICATE-----\n"
                    mock_additional_certs = [mock_additional_cert]
                
                # Configure the mock to return our mock values
                mock_load.return_value = (mock_private_key, mock_certificate, mock_additional_certs)
                
                # Create the client
                client = OpsPortalClient(config['ops_portal'])
                
                print("✅ OpsPortalClient created successfully with certificate data")
                
                # Verify the client was configured with the certificate
                assert client.cert_pfx_data is not None, "Certificate data not set in client"
                assert client.cert_pfx is None, "Certificate file path should not be set"
                
                print("✅ Client correctly configured with certificate data from AWS Secrets Manager")
                
                return True
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Clean up
            if os.path.exists(temp_cert_path):
                os.unlink(temp_cert_path)
            # Remove environment variables
            if 'AWS_EXECUTION_ENV' in os.environ:
                del os.environ['AWS_EXECUTION_ENV']
            if 'ENVIRONMENT' in os.environ:
                del os.environ['ENVIRONMENT']

def test_local_certificate():
    """
    Test loading a certificate from the file system when running locally.
    """
    print("\n" + "=" * 60)
    print("TESTING CERTIFICATE LOADING FROM FILE SYSTEM")
    print("=" * 60)
    
    # Create a mock certificate file
    with tempfile.NamedTemporaryFile(suffix='.pfx', delete=False) as temp_cert:
        temp_cert.write(b'MOCK_CERTIFICATE_DATA')
        temp_cert_path = temp_cert.name
    
    try:
        # Set environment variables for local development
        os.environ['OPSAPI_OPS_PORTAL_AUTH_URL'] = 'https://mock-auth-url.example.com'
        os.environ['OPSAPI_OPS_PORTAL_ITEM_URL'] = 'https://mock-item-url.example.com'
        os.environ['OPSAPI_OPS_PORTAL_CLIENT_ID'] = 'mock-client-id'
        os.environ['OPSAPI_OPS_PORTAL_CLIENT_SECRET'] = 'mock-client-secret'
        os.environ['OPSAPI_OPS_PORTAL_VERIFY_SSL'] = 'false'
        os.environ['OPSAPI_OPS_PORTAL_CERT_PATH'] = temp_cert_path
        os.environ['OPSAPI_OPS_PORTAL_CERT_PASSWORD'] = 'mock-password'
        
        print("\n1. Loading configuration from environment variables...")
        # Import the config module
        from src.config import get_config
        config = get_config()
        ops_portal_config = config.get_section('ops_portal')
        
        print("\n2. Verifying certificate path was loaded...")
        assert ops_portal_config.get('cert_path') == temp_cert_path, "Certificate path not found in config"
        
        print("✅ Certificate path loaded from environment variables")
        
        print("\n3. Creating OpsPortalClient with certificate path...")
        # Mock the pkcs12.load_key_and_certificates function to avoid actual certificate parsing
        with mock.patch('cryptography.hazmat.primitives.serialization.pkcs12.load_key_and_certificates') as mock_load:
            # Create mock return values for the load_key_and_certificates function
            mock_private_key = mock.MagicMock()
            mock_certificate = mock.MagicMock()
            mock_certificate.subject = "CN=Mock Certificate"
            mock_certificate.issuer = "CN=Mock Issuer"
            # Configure the public_bytes method to return bytes
            mock_certificate.public_bytes.return_value = b"-----BEGIN CERTIFICATE-----\nMOCK CERTIFICATE\n-----END CERTIFICATE-----\n"
            mock_private_key.private_bytes.return_value = b"-----BEGIN PRIVATE KEY-----\nMOCK PRIVATE KEY\n-----END PRIVATE KEY-----\n"
            mock_additional_certs = []
            if mock_additional_certs:  # This is just to avoid an empty list check
                mock_additional_cert = mock.MagicMock()
                mock_additional_cert.subject = "CN=Mock Intermediate"
                mock_additional_cert.public_bytes.return_value = b"-----BEGIN CERTIFICATE-----\nMOCK INTERMEDIATE\n-----END CERTIFICATE-----\n"
                mock_additional_certs = [mock_additional_cert]
            
            # Configure the mock to return our mock values
            mock_load.return_value = (mock_private_key, mock_certificate, mock_additional_certs)
            
            # Create the client
            client = OpsPortalClient(ops_portal_config)
            
            print("✅ OpsPortalClient created successfully with certificate path")
            
            # Verify the client was configured with the certificate
            assert client.cert_pfx == temp_cert_path, "Certificate path not set in client"
            assert client.cert_pfx_data is None, "Certificate data should not be set"
            
            print("✅ Client correctly configured with certificate path from file system")
            
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(temp_cert_path):
            os.unlink(temp_cert_path)
        # Remove environment variables
        for var in [
            'OPSAPI_OPS_PORTAL_AUTH_URL',
            'OPSAPI_OPS_PORTAL_ITEM_URL',
            'OPSAPI_OPS_PORTAL_CLIENT_ID',
            'OPSAPI_OPS_PORTAL_CLIENT_SECRET',
            'OPSAPI_OPS_PORTAL_VERIFY_SSL',
            'OPSAPI_OPS_PORTAL_CERT_PATH',
            'OPSAPI_OPS_PORTAL_CERT_PASSWORD'
        ]:
            if var in os.environ:
                del os.environ[var]

def main():
    """Main function."""
    print("Certificate Loading Test Suite")
    print("=" * 60)
    
    # Run tests
    aws_result = test_aws_secrets_certificate()
    local_result = test_local_certificate()
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"AWS Secrets Manager test: {'✅ PASSED' if aws_result else '❌ FAILED'}")
    print(f"Local file system test: {'✅ PASSED' if local_result else '❌ FAILED'}")
    
    if aws_result and local_result:
        print("\n🎉 All tests passed! Certificate loading works correctly in both environments.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

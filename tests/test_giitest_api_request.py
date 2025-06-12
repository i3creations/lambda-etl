#!/usr/bin/env python3
"""
Test script to send a request to https://giitest-api.dhs.gov/default.htm with certificate authentication.

This test demonstrates how to use certificate authentication with TLS 1.2 to send a request
to the specified DHS API endpoint.
"""

import os
import sys
import logging
import requests
import tempfile
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

def test_giitest_api_request():
    """
    Test sending a request to https://giitest-api.dhs.gov/default.htm with certificate authentication.
    """
    print("=" * 60)
    print("TESTING CERTIFICATE AUTHENTICATION WITH GIITEST API")
    print("=" * 60)
    
    # Check for PFX certificate path from environment variable first
    env_pfx_path = os.getenv('OPSAPI_OPS_PORTAL_CERT_PATH')
    if env_pfx_path:
        # If the path is relative, make it absolute from the project root
        if not os.path.isabs(env_pfx_path):
            pfx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), env_pfx_path)
        else:
            pfx_path = env_pfx_path
        print(f"Using PFX path from environment variable: {env_pfx_path}")
    else:
        # Fall back to default path
        pfx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'certs', 'giitest-api.pfx')
        print(f"Using default PFX path: {pfx_path}")
    
    # Configuration using environment variables
    config = {
        'auth_url': os.getenv('OPSAPI_OPS_PORTAL_AUTH_URL'),  # Not used directly in this test
        'item_url': os.getenv('OPSAPI_OPS_PORTAL_ITEM_URL'),  # Not used directly in this test
        'client_id': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_ID'),
        'client_secret': os.getenv('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
        'verify_ssl': os.getenv('OPSAPI_OPS_PORTAL_VERIFY_SSL', 'false').lower() == 'true'
    }
    
    # Check if PFX file exists
    if not os.path.exists(pfx_path):
        print(f"ERROR: PFX file not found at: {pfx_path}")
        return False
        
    print(f"Found PFX file: {pfx_path}")
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
    
    # Add PFX configuration
    config['cert_pfx'] = pfx_path
    config['pfx_password'] = pfx_password
    print("Using PFX certificate with complete certificate chain")
    
    try:
        # Step 1: Create the OPS Portal client with TLS 1.2 configuration
        print("\n1. Creating client with TLS 1.2 configuration...")
        client = OpsPortalClient(config)
        print("✅ Client created successfully with TLS 1.2 adapter")
        
        # Step 2: Log certificate format details
        print("\n2. Logging certificate format details...")
        client.log_certificate_format_details()
        
        # Step 3: Define the target URL
        target_url = "https://giitest-api.dhs.gov/default.htm"
        print(f"\n3. Preparing to send request to: {target_url}")
        
        # Step 4: Send a direct request using the configured session
        print("\n4. Sending request with certificate authentication...")
        response = client.session.get(
            target_url,
            timeout=30  # Add timeout to prevent hanging
        )
        
        # Step 5: Log the response details
        print(f"\n5. Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        # Log TLS version if available
        if hasattr(response.raw, 'connection') and hasattr(response.raw.connection, 'socket'):
            tls_version = response.raw.connection.socket.version()
            print(f"TLS version used: {tls_version}")
        
        # Step 6: Check if the request was successful
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
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        
        # Provide more detailed error information
        if hasattr(e, 'response') and e.response is not None:
            print(f"Status code: {e.response.status_code}")
            print(f"Response headers: {e.response.headers}")
            print(f"Response content: {e.response.text[:500]}...")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_pfx_certificate():
    """
    Test using the .pfx file in the certs folder.
    
    This test uses the PKCS#12 (.pfx) certificate file to authenticate with the API.
    """
    print("\n" + "=" * 60)
    print("TESTING WITH PFX CERTIFICATE")
    print("=" * 60)
    
    # Check for PFX certificate path from environment variable first
    env_pfx_path = os.getenv('OPSAPI_OPS_PORTAL_CERT_PATH')
    if env_pfx_path:
        # If the path is relative, make it absolute from the project root
        if not os.path.isabs(env_pfx_path):
            pfx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), env_pfx_path)
        else:
            pfx_path = env_pfx_path
        print(f"Using PFX path from environment variable: {env_pfx_path}")
    else:
        # Fall back to default path
        pfx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'certs', 'giitest-api.pfx')
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
    
    try:
        # Import the cryptography library for handling PKCS#12 files
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        except ImportError:
            print("❌ cryptography library not available - required for PKCS#12 handling")
            return False
        
        # Read the .pfx file
        with open(pfx_path, 'rb') as pfx_file:
            pfx_data = pfx_file.read()
        
        print("2. Successfully read PFX file")
        
        # Try to parse the PKCS#12 data
        try:
            # Convert password to bytes if it's not None
            password_bytes = pfx_password.encode('utf-8') if pfx_password else None
            
            # Load the PKCS#12 data
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data, 
                password_bytes
            )
            
            print("3. Successfully parsed PKCS#12 data")
            print(f"   - Certificate subject: {certificate.subject}")
            print(f"   - Certificate issuer: {certificate.issuer}")
            print(f"   - Additional certificates: {len(additional_certificates) if additional_certificates else 0}")
            
            # Create temporary files for the certificate and key
            cert_fd, cert_path = tempfile.mkstemp(suffix='.pem')
            key_fd, key_path = tempfile.mkstemp(suffix='.key')
            
            try:
                # Write the certificate to a temporary file
                with os.fdopen(cert_fd, 'wb') as cert_file:
                    cert_file.write(certificate.public_bytes(Encoding.PEM))
                
                # Write the private key to a temporary file
                with os.fdopen(key_fd, 'wb') as key_file:
                    key_file.write(private_key.private_bytes(
                        Encoding.PEM,
                        PrivateFormat.PKCS8,
                        NoEncryption()
                    ))
                
                # Set proper file permissions for security
                os.chmod(cert_path, 0o600)
                os.chmod(key_path, 0o600)
                
                print(f"4. Created temporary certificate files:")
                print(f"   - Certificate: {cert_path}")
                print(f"   - Key: {key_path}")
                
                # Create a session with TLS 1.2 adapter
                import ssl
                from requests.adapters import HTTPAdapter
                from urllib3.util import ssl_
                
                # Create a custom TLS 1.2 adapter
                class TLSv12Adapter(HTTPAdapter):
                    def __init__(self, *args, **kwargs):
                        self.verify = kwargs.pop('verify', True)
                        super().__init__(*args, **kwargs)
                        
                    def init_poolmanager(self, *args, **kwargs):
                        context = ssl_.create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1_2)
                        # Disable older protocols
                        context.options |= ssl.OP_NO_SSLv2
                        context.options |= ssl.OP_NO_SSLv3
                        context.options |= ssl.OP_NO_TLSv1
                        context.options |= ssl.OP_NO_TLSv1_1
                        
                        # Handle hostname verification based on verify setting
                        if not self.verify:
                            context.check_hostname = False
                            context.verify_mode = ssl.CERT_NONE
                        
                        kwargs['ssl_context'] = context
                        return super().init_poolmanager(*args, **kwargs)
                
                # Get SSL verification setting from environment
                verify_ssl = os.getenv('OPSAPI_OPS_PORTAL_VERIFY_SSL', 'false').lower() == 'true'
                
                # Create a session with TLS 1.2 adapter
                session = requests.session()
                session.mount('https://', TLSv12Adapter(verify=verify_ssl))
                
                # Configure certificate
                session.cert = (cert_path, key_path)
                session.verify = verify_ssl
                
                if not verify_ssl:
                    # Disable SSL warnings when verification is disabled
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                print("5. Created session with TLS 1.2 adapter and certificate from PFX file")
                
                # Send the request
                target_url = "https://giitest-api.dhs.gov/default.htm"
                print(f"6. Sending request to {target_url}")
                
                # Add proper headers to avoid 406 Not Acceptable error
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = session.get(target_url, headers=headers, timeout=30)
                
                print(f"7. Response status code: {response.status_code}")
                
                # Log TLS version if available
                if hasattr(response.raw, 'connection') and hasattr(response.raw.connection, 'socket'):
                    tls_version = response.raw.connection.socket.version()
                    print(f"TLS version used: {tls_version}")
                
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
                    
            finally:
                # Clean up temporary files
                try:
                    os.unlink(cert_path)
                    os.unlink(key_path)
                    print("8. Cleaned up temporary certificate files")
                except:
                    pass
                
        except Exception as e:
            print(f"❌ Error parsing PKCS#12 data: {e}")
            if "Bad decrypt" in str(e):
                print("   This usually indicates an incorrect password for the PFX file.")
                print("   Make sure the OPSAPI_PFX_PASSWORD environment variable is set correctly.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_certificate_chain():
    """
    Test using the entire certificate chain from the PFX file.
    
    This test extracts all certificates from the PFX file and uses the complete chain
    for authentication, which can help with certificate validation issues.
    """
    print("\n" + "=" * 60)
    print("TESTING WITH COMPLETE CERTIFICATE CHAIN")
    print("=" * 60)
    
    # Check for PFX certificate path from environment variable first
    env_pfx_path = os.getenv('OPSAPI_OPS_PORTAL_CERT_PATH')
    if env_pfx_path:
        # If the path is relative, make it absolute from the project root
        if not os.path.isabs(env_pfx_path):
            pfx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), env_pfx_path)
        else:
            pfx_path = env_pfx_path
        print(f"Using PFX path from environment variable: {env_pfx_path}")
    else:
        # Fall back to default path
        pfx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'certs', 'giitest-api.pfx')
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
    
    try:
        # Import the cryptography library for handling PKCS#12 files
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        except ImportError:
            print("❌ cryptography library not available - required for PKCS#12 handling")
            return False
        
        # Read the .pfx file
        with open(pfx_path, 'rb') as pfx_file:
            pfx_data = pfx_file.read()
        
        print("2. Successfully read PFX file")
        
        # Try to parse the PKCS#12 data
        try:
            # Convert password to bytes if it's not None
            password_bytes = pfx_password.encode('utf-8') if pfx_password else None
            
            # Load the PKCS#12 data
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data, 
                password_bytes
            )
            
            print("3. Successfully parsed PKCS#12 data")
            print(f"   - Certificate subject: {certificate.subject}")
            print(f"   - Certificate issuer: {certificate.issuer}")
            print(f"   - Additional certificates: {len(additional_certificates) if additional_certificates else 0}")
            
            # Create temporary files for the certificate chain and key
            cert_chain_fd, cert_chain_path = tempfile.mkstemp(suffix='.pem')
            key_fd, key_path = tempfile.mkstemp(suffix='.key')
            
            try:
                # Write the certificate chain to a temporary file
                # Start with the end-entity certificate
                with os.fdopen(cert_chain_fd, 'wb') as cert_chain_file:
                    # Write the end-entity certificate
                    cert_chain_file.write(certificate.public_bytes(Encoding.PEM))
                    
                    # Write all additional certificates in the chain
                    if additional_certificates:
                        for i, additional_cert in enumerate(additional_certificates):
                            cert_chain_file.write(additional_cert.public_bytes(Encoding.PEM))
                            print(f"   - Added certificate {i+1} to chain: {additional_cert.subject}")
                
                # Write the private key to a temporary file
                with os.fdopen(key_fd, 'wb') as key_file:
                    key_file.write(private_key.private_bytes(
                        Encoding.PEM,
                        PrivateFormat.PKCS8,
                        NoEncryption()
                    ))
                
                # Set proper file permissions for security
                os.chmod(cert_chain_path, 0o600)
                os.chmod(key_path, 0o600)
                
                print(f"4. Created temporary certificate files:")
                print(f"   - Certificate chain: {cert_chain_path}")
                print(f"   - Key: {key_path}")
                
                # Create a session with TLS 1.2 adapter
                import ssl
                from requests.adapters import HTTPAdapter
                from urllib3.util import ssl_
                
                # Create a custom TLS 1.2 adapter
                class TLSv12Adapter(HTTPAdapter):
                    def __init__(self, *args, **kwargs):
                        self.verify = kwargs.pop('verify', True)
                        super().__init__(*args, **kwargs)
                        
                    def init_poolmanager(self, *args, **kwargs):
                        context = ssl_.create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1_2)
                        # Disable older protocols
                        context.options |= ssl.OP_NO_SSLv2
                        context.options |= ssl.OP_NO_SSLv3
                        context.options |= ssl.OP_NO_TLSv1
                        context.options |= ssl.OP_NO_TLSv1_1
                        
                        # Handle hostname verification based on verify setting
                        if not self.verify:
                            context.check_hostname = False
                            context.verify_mode = ssl.CERT_NONE
                        
                        kwargs['ssl_context'] = context
                        return super().init_poolmanager(*args, **kwargs)
                
                # Get SSL verification setting from environment
                verify_ssl = os.getenv('OPSAPI_OPS_PORTAL_VERIFY_SSL', 'false').lower() == 'true'
                
                # Create a session with TLS 1.2 adapter
                session = requests.session()
                session.mount('https://', TLSv12Adapter(verify=verify_ssl))
                
                # Configure certificate chain
                session.cert = (cert_chain_path, key_path)
                session.verify = verify_ssl
                
                if not verify_ssl:
                    # Disable SSL warnings when verification is disabled
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                print("5. Created session with TLS 1.2 adapter and certificate chain")
                
                # Send the request
                target_url = "https://giitest-api.dhs.gov/default.htm"
                print(f"6. Sending request to {target_url}")
                
                response = session.get(target_url, timeout=30)
                
                print(f"7. Response status code: {response.status_code}")
                
                # Log TLS version if available
                if hasattr(response.raw, 'connection') and hasattr(response.raw.connection, 'socket'):
                    tls_version = response.raw.connection.socket.version()
                    print(f"TLS version used: {tls_version}")
                
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
                    
            finally:
                # Clean up temporary files
                try:
                    os.unlink(cert_chain_path)
                    os.unlink(key_path)
                    print("8. Cleaned up temporary certificate files")
                except:
                    pass
                
        except Exception as e:
            print(f"❌ Error parsing PKCS#12 data: {e}")
            if "Bad decrypt" in str(e):
                print("   This usually indicates an incorrect password for the PFX file.")
                print("   Make sure the OPSAPI_PFX_PASSWORD environment variable is set correctly.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run the tests."""
    print("Certificate Authentication Test for GIITEST API")
    print("=" * 60)
    
    # Run the main test
    client_result = test_giitest_api_request()
    
    # If the client test fails, try with PFX certificate
    if not client_result:
        print("\n⚠️  Client test failed, trying with PFX certificate...")
        pfx_result = test_with_pfx_certificate()
    else:
        pfx_result = False  # Skip PFX test if client test passes
        
    # If both tests fail, try with certificate chain
    if not client_result and not pfx_result:
        print("\n⚠️  Both tests failed, trying with complete certificate chain...")
        chain_result = test_with_certificate_chain()
    else:
        chain_result = False  # Skip chain test if any other test passes
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"OpsPortalClient test: {'✅ PASSED' if client_result else '❌ FAILED'}")
    if not client_result:
        print(f"PFX certificate test: {'✅ PASSED' if pfx_result else '❌ FAILED'}")
    if not client_result and not pfx_result:
        print(f"Certificate chain test: {'✅ PASSED' if chain_result else '❌ FAILED'}")
    
    if client_result or pfx_result or chain_result:
        print("\n🎉 Successfully sent request to GIITEST API with certificate authentication!")
        return 0
    else:
        print("\n⚠️  Failed to send request to GIITEST API.")
        print("\nTROUBLESHOOTING STEPS:")
        print("1. Verify that the certificate and key are valid")
        print("2. Check if the server requires specific TLS settings")
        print("3. Verify that the server is accessible from your network")
        print("4. Check if the URL is correct")
        print("5. Try with different SSL verification settings")
        print("6. Check if the server requires specific HTTP headers")
        return 1

if __name__ == "__main__":
    sys.exit(main())

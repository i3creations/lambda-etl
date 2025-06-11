#!/usr/bin/env python3
"""
Detailed debug script for OPS Portal authentication issues.
This script will examine the exact HTTP request and response.
"""

import os
import sys
import requests
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the necessary modules
from src.config import Config

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / '.env')
except ImportError:
    print("Warning: python-dotenv not available, assuming environment variables are already loaded")

def test_detailed_authentication():
    """Test authentication with detailed request/response logging."""
    print("=" * 60)
    print("DETAILED AUTHENTICATION TEST")
    print("=" * 60)
    
    # Load configuration
    config = Config()
    ops_config = config.get_section('ops_portal')
    
    auth_url = ops_config.get('auth_url')
    client_id = ops_config.get('client_id')
    client_secret = ops_config.get('client_secret')
    cert_pem = ops_config.get('cert_pem')
    key_pem = ops_config.get('key_pem')
    verify_ssl = ops_config.get('verify_ssl', 'true').lower() == 'true'
    
    print(f"Auth URL: {auth_url}")
    print(f"Client ID: {client_id}")
    print(f"SSL Verification: {verify_ssl}")
    print(f"Certificate configured: {bool(cert_pem and key_pem)}")
    
    # Prepare certificate files
    cert_path = None
    key_path = None
    
    if cert_pem and key_pem:
        # Fix PEM format
        def fix_pem_format(pem_content):
            if '\\n' in pem_content:
                pem_content = pem_content.replace('\\n', '\n')
            return pem_content
        
        fixed_cert = fix_pem_format(cert_pem)
        fixed_key = fix_pem_format(key_pem)
        
        # Create temporary files
        cert_fd, cert_path = tempfile.mkstemp(suffix='.pem')
        key_fd, key_path = tempfile.mkstemp(suffix='.key')
        
        try:
            with os.fdopen(cert_fd, 'w') as cert_file:
                cert_file.write(fixed_cert)
            with os.fdopen(key_fd, 'w') as key_file:
                key_file.write(fixed_key)
            
            os.chmod(cert_path, 0o600)
            os.chmod(key_path, 0o600)
            
            print(f"Certificate file: {cert_path}")
            print(f"Key file: {key_path}")
            
        except Exception as e:
            print(f"Error creating certificate files: {e}")
            return False
    
    # Test different authentication approaches
    test_cases = [
        {
            'name': 'Basic Authentication (no certificate)',
            'use_cert': False,
            'verify_ssl': False
        },
        {
            'name': 'Certificate Authentication (SSL verification disabled)',
            'use_cert': True,
            'verify_ssl': False
        },
        {
            'name': 'Certificate Authentication (SSL verification enabled)',
            'use_cert': True,
            'verify_ssl': True
        }
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        # Create session
        session = requests.Session()
        
        # Configure SSL verification
        session.verify = test_case['verify_ssl']
        if not test_case['verify_ssl']:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Configure certificate
        if test_case['use_cert'] and cert_path and key_path:
            session.cert = (cert_path, key_path)
            print("✅ Client certificate configured")
        else:
            print("⚠️  No client certificate")
        
        # Set headers
        session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'OPS-Portal-Debug/1.0 (Python/requests)',
            'Cache-Control': 'no-cache'
        })
        
        # Prepare authentication payload
        auth_payload = {
            'clientId': client_id,
            'clientSecret': client_secret
        }
        
        print(f"Request URL: {auth_url}")
        print(f"Request Headers: {dict(session.headers)}")
        print(f"Request Payload: {{'clientId': '{client_id[:8]}...', 'clientSecret': '[REDACTED]'}}")
        print(f"SSL Verification: {session.verify}")
        print(f"Client Certificate: {bool(session.cert)}")
        
        try:
            # Make the request
            response = session.post(
                auth_url,
                json=auth_payload,
                timeout=30
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            # Try to get response content
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    response_data = response.json()
                    print(f"Response JSON: {response_data}")
                else:
                    response_text = response.text
                    if len(response_text) > 1000:
                        print(f"Response Text (truncated): {response_text[:1000]}...")
                    else:
                        print(f"Response Text: {response_text}")
            except Exception as e:
                print(f"Error reading response: {e}")
            
            # Check if successful
            if 200 <= response.status_code < 300:
                print("✅ Authentication successful!")
                return True
            else:
                print(f"❌ Authentication failed with status {response.status_code}")
                
                # Analyze specific error codes
                if response.status_code == 403:
                    print("  - 403 Forbidden: Server is rejecting the request")
                    print("  - This could indicate:")
                    print("    * Invalid client credentials")
                    print("    * Missing or invalid client certificate")
                    print("    * IP address not whitelisted")
                    print("    * Service configuration issue")
                elif response.status_code == 401:
                    print("  - 401 Unauthorized: Invalid credentials")
                elif response.status_code == 404:
                    print("  - 404 Not Found: Endpoint doesn't exist")
                elif response.status_code >= 500:
                    print("  - Server error: Service may be down or misconfigured")
                
        except requests.exceptions.SSLError as e:
            print(f"❌ SSL Error: {e}")
            print("  - This indicates a certificate or SSL configuration issue")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection Error: {e}")
            print("  - This indicates a network connectivity issue")
        except requests.exceptions.Timeout as e:
            print(f"❌ Timeout Error: {e}")
            print("  - The server is not responding within the timeout period")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
    
    # Clean up temporary files
    if cert_path and os.path.exists(cert_path):
        os.unlink(cert_path)
    if key_path and os.path.exists(key_path):
        os.unlink(key_path)
    
    return False

def test_certificate_validation():
    """Test if the certificate is properly configured for the target domain."""
    print("\n" + "=" * 60)
    print("CERTIFICATE DOMAIN VALIDATION")
    print("=" * 60)
    
    config = Config()
    ops_config = config.get_section('ops_portal')
    
    cert_pem = ops_config.get('cert_pem')
    auth_url = ops_config.get('auth_url')
    
    if not cert_pem:
        print("❌ No certificate configured")
        return False
    
    try:
        from cryptography import x509
        from urllib.parse import urlparse
        
        # Fix PEM format
        def fix_pem_format(pem_content):
            if '\\n' in pem_content:
                pem_content = pem_content.replace('\\n', '\n')
            return pem_content
        
        fixed_cert = fix_pem_format(cert_pem)
        certificate = x509.load_pem_x509_certificate(fixed_cert.encode('utf-8'))
        
        # Extract domain from auth URL
        parsed_url = urlparse(auth_url)
        target_domain = parsed_url.hostname
        
        print(f"Target domain: {target_domain}")
        print(f"Certificate subject: {certificate.subject}")
        
        # Check Subject Alternative Names (SAN)
        try:
            san_extension = certificate.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            san_names = san_extension.value.get_values_for_type(x509.DNSName)
            print(f"Certificate SAN names: {san_names}")
            
            # Check if target domain matches any SAN name
            domain_match = any(
                target_domain.lower() == san_name.lower() or 
                (san_name.startswith('*.') and target_domain.lower().endswith(san_name[2:].lower()))
                for san_name in san_names
            )
            
            if domain_match:
                print("✅ Certificate domain matches target domain")
            else:
                print("⚠️  Certificate domain does not match target domain")
                print("  - This might cause SSL validation issues")
                
        except x509.ExtensionNotFound:
            print("⚠️  No Subject Alternative Names found in certificate")
            
            # Check Common Name (CN) in subject
            cn_attributes = [attr for attr in certificate.subject if attr.oid == x509.oid.NameOID.COMMON_NAME]
            if cn_attributes:
                cn_value = cn_attributes[0].value
                print(f"Certificate Common Name: {cn_value}")
                
                if target_domain.lower() == cn_value.lower():
                    print("✅ Certificate Common Name matches target domain")
                else:
                    print("⚠️  Certificate Common Name does not match target domain")
            else:
                print("❌ No Common Name found in certificate")
        
        return True
        
    except Exception as e:
        print(f"❌ Certificate validation failed: {e}")
        return False

def main():
    """Main function."""
    print("OPS Portal Detailed Authentication Debug")
    print("=" * 60)
    
    # Test certificate domain validation
    cert_valid = test_certificate_validation()
    
    # Test detailed authentication
    auth_success = test_detailed_authentication()
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Certificate validation: {'✅ PASSED' if cert_valid else '❌ FAILED'}")
    print(f"Authentication test: {'✅ PASSED' if auth_success else '❌ FAILED'}")
    
    if not auth_success:
        print("\n🔍 NEXT STEPS:")
        print("1. Verify that the client credentials are correct and active")
        print("2. Check if the certificate is properly installed and trusted by the server")
        print("3. Confirm that your IP address is whitelisted for API access")
        print("4. Contact the OPS Portal API administrator to verify service status")
        print("5. Check if there are any firewall or network restrictions")

if __name__ == '__main__':
    main()

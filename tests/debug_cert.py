#!/usr/bin/env python3
"""
Debug script to check certificate format issues.
"""

import os
from dotenv import load_dotenv

# Load environment variables
print("Loading .env file...")
env_loaded = load_dotenv('.env')
print(f"Environment loaded: {env_loaded}")

# Also try loading from parent directory as fallback
if not env_loaded:
    print("Trying parent directory...")
    env_loaded = load_dotenv('../.env')
    print(f"Parent directory loaded: {env_loaded}")

cert_pem = os.environ.get('OPSAPI_OPS_PORTAL_CERT_PEM', '')
key_pem = os.environ.get('OPSAPI_OPS_PORTAL_KEY_PEM', '')

print("Certificate format check:")
print(f"Certificate length: {len(cert_pem)}")
print(f"Certificate starts with: {cert_pem[:50]}...")
print(f"Certificate ends with: ...{cert_pem[-50:]}")
has_cert_newlines = '\\n' in cert_pem
print(f"Certificate has newlines: {has_cert_newlines}")
print(f"Raw certificate (first 100 chars): {repr(cert_pem[:100])}")
print()

print("Private key format check:")
print(f"Key length: {len(key_pem)}")
print(f"Key starts with: {key_pem[:50]}...")
print(f"Key ends with: ...{key_pem[-50:]}")
has_key_newlines = '\\n' in key_pem
print(f"Key has newlines: {has_key_newlines}")
print(f"Raw key (first 100 chars): {repr(key_pem[:100])}")
print()

# Try to fix the format by adding proper line breaks
def fix_pem_format(pem_content):
    """Fix PEM format by ensuring proper line breaks."""
    if not pem_content:
        return pem_content
        
    # Remove any existing quotes that might be wrapping the content
    pem_content = pem_content.strip('"\'')
    
    if '\\n' in pem_content:
        # Replace literal \n with actual newlines
        pem_content = pem_content.replace('\\n', '\n')
    
    # If still no newlines, it might be all on one line
    if '\n' not in pem_content:
        # Split into 64-character lines (standard PEM format)
        lines = []
        if pem_content.startswith('-----BEGIN'):
            # Find the header end
            header_end = pem_content.find('-----', 5) + 5
            header = pem_content[:header_end]
            
            # Find the footer start
            footer_start = pem_content.rfind('-----END')
            if footer_start == -1:
                # Fallback: look for any footer
                footer_start = pem_content.rfind('-----', header_end)
            
            if footer_start > header_end:
                footer = pem_content[footer_start:]
                # Get the content between header and footer
                content = pem_content[header_end:footer_start]
                
                # Split content into 64-character lines
                lines.append(header)
                for i in range(0, len(content), 64):
                    line = content[i:i+64]
                    if line.strip():  # Only add non-empty lines
                        lines.append(line)
                lines.append(footer)
                
                pem_content = '\n'.join(lines)
            else:
                # Malformed PEM, return as-is
                return pem_content
    
    return pem_content

print("Attempting to fix certificate format...")
fixed_cert = fix_pem_format(cert_pem)
print(f"Fixed certificate preview:\n{fixed_cert[:300]}...")

print("\nAttempting to fix key format...")
fixed_key = fix_pem_format(key_pem)
print(f"Fixed key preview:\n{fixed_key[:300]}...")

print("\n" + "="*50)
print("PROPERLY FORMATTED CERTIFICATES FOR .env FILE:")
print("="*50)
print("\nCertificate (copy this to OPSAPI_OPS_PORTAL_CERT_PEM):")
print('OPSAPI_OPS_PORTAL_CERT_PEM="' + fixed_cert.replace('\n', '\\n') + '"')

print("\nPrivate Key (copy this to OPSAPI_OPS_PORTAL_KEY_PEM):")
print('OPSAPI_OPS_PORTAL_KEY_PEM="' + fixed_key.replace('\n', '\\n') + '"')
print("="*50)

# Test with cryptography library
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography import x509
    
    print("\nTesting fixed certificate...")
    try:
        certificate = x509.load_pem_x509_certificate(fixed_cert.encode('utf-8'))
        print("✅ Fixed certificate loads successfully!")
    except Exception as e:
        print(f"❌ Fixed certificate failed: {e}")
    
    print("\nTesting fixed private key...")
    try:
        private_key = serialization.load_pem_private_key(
            fixed_key.encode('utf-8'),
            password=None
        )
        print("✅ Fixed private key loads successfully!")
    except Exception as e:
        print(f"❌ Fixed private key failed: {e}")
        
except ImportError:
    print("❌ cryptography library not available")

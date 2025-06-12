# TLS Certificate Authentication Guide

This document provides guidance on using TLS 1.2 with certificate authentication for the OPS Portal API.

## Overview

When using certificate authentication (mutual TLS) with the OPS Portal API, explicitly configuring TLS 1.2 can help resolve certificate rejection issues. This guide explains how the implementation works and how to test it.

## Implementation Details

The `OpsPortalClient` class has been enhanced to explicitly use TLS 1.2 for all HTTPS connections. This is implemented through:

1. A custom `TLSv12Adapter` class that enforces TLS 1.2 as the minimum protocol version
2. Disabling older, less secure protocols (SSLv2, SSLv3, TLS 1.0, TLS 1.1)
3. Mounting this adapter to handle all HTTPS requests

```python
def _configure_tls_version(self):
    """
    Configure the TLS version for the session.
    
    This method creates a custom SSL context that explicitly sets TLS 1.2
    as the minimum version to use for the HTTPS connection.
    """
    try:
        # Create a custom SSL context with TLS 1.2
        class TLSv12Adapter(HTTPAdapter):
            def __init__(self, *args, **kwargs):
                # Store verify setting from the session
                self.verify = kwargs.pop('verify', True)
                super().__init__(*args, **kwargs)
                
            def init_poolmanager(self, *args, **kwargs):
                context = ssl_.create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1_2)
                # Disable older protocols
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3
                context.options |= ssl.OP_NO_TLSv1
                context.options |= ssl.OP_NO_TLSv1_1
                
                # Handle hostname verification based on verify_ssl setting
                if not self.verify:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                
                kwargs['ssl_context'] = context
                return super().init_poolmanager(*args, **kwargs)
            
            def proxy_manager_for(self, *args, **kwargs):
                context = ssl_.create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1_2)
                # Disable older protocols
                context.options |= ssl.OP_NO_SSLv2
                context.options |= ssl.OP_NO_SSLv3
                context.options |= ssl.OP_NO_TLSv1
                context.options |= ssl.OP_NO_TLSv1_1
                
                # Handle hostname verification based on verify_ssl setting
                if not self.verify:
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                
                kwargs['ssl_context'] = context
                return super().proxy_manager_for(*args, **kwargs)
        
        # Mount the adapter for all HTTPS requests with verify setting
        self.session.mount('https://', TLSv12Adapter(verify=self.verify_ssl))
        logger.info("TLS 1.2 explicitly configured for HTTPS connections")
        
    except Exception as e:
        logger.error(f"Failed to configure TLS version: {str(e)}")
        logger.warning("Using default TLS version configuration")
```

## Why TLS 1.2?

TLS 1.2 offers several advantages for certificate authentication:

1. **Better Security**: TLS 1.2 addresses vulnerabilities found in earlier versions
2. **Stronger Cipher Suites**: Supports more secure cipher suites
3. **Better Certificate Handling**: Improved certificate validation and handling
4. **Wider Compatibility**: Many modern APIs require TLS 1.2 or higher
5. **Compliance**: Many security standards (PCI DSS, HIPAA, etc.) require TLS 1.2 or higher

## Common Certificate Authentication Issues

When a certificate is rejected by an endpoint, it could be due to:

1. **Protocol Version Mismatch**: The server requires a specific TLS version
2. **Certificate Trust Issues**: The server doesn't trust the certificate's issuer
3. **Certificate Validation Errors**: Expired certificate, wrong domain, etc.
4. **Cipher Suite Incompatibility**: The server requires specific cipher suites
5. **Certificate Format Issues**: Incorrect format or encoding
6. **Hostname Verification Issues**: When SSL verification is disabled but hostname verification is still enabled

The implementation addresses both protocol version mismatch and hostname verification issues, which are common causes of certificate rejection.

Explicitly setting TLS 1.2 addresses the protocol version mismatch issue, which is a common cause of certificate rejection.

## Testing TLS 1.2 Configuration

A test script (`tests/test_tls_version.py`) is provided to verify that TLS 1.2 is being properly used:

```bash
python tests/test_tls_version.py
```

This script:
1. Creates an `OpsPortalClient` with TLS 1.2 configuration
2. Verifies the HTTPS adapter is properly configured
3. Attempts authentication to test the TLS configuration
4. Logs the TLS version used for the connection

## Troubleshooting

If certificate authentication still fails after configuring TLS 1.2:

1. **Check Certificate Validity**: Ensure the certificate is valid and not expired
2. **Verify Domain Match**: The certificate's domain should match the API endpoint
3. **Check Certificate Chain**: Ensure the full certificate chain is trusted
4. **Inspect Server Requirements**: The server might have specific TLS requirements
5. **Enable Debug Logging**: Use the debug mode in the test script for detailed logs

## Advanced Configuration

For more complex scenarios, you might need to:

1. **Configure Specific Cipher Suites**:
   ```python
   context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK')
   ```

2. **Use PKCS#12 Format**:
   If the server expects a different certificate format, consider converting to PKCS#12

3. **Include Intermediate Certificates**:
   Ensure the full certificate chain is provided if required

## References

- [Python Requests Documentation](https://docs.python-requests.org/)
- [Python SSL Module Documentation](https://docs.python.org/3/library/ssl.html)
- [TLS 1.2 Specification (RFC 5246)](https://tools.ietf.org/html/rfc5246)
- [X.509 Certificate Authentication](https://en.wikipedia.org/wiki/X.509)

# TLS 1.2 Certificate Authentication for OPS Portal API

This repository includes an implementation of TLS 1.2 certificate authentication for the OPS Portal API. This README provides an overview of the implementation and how to use it.

## Overview

When using certificate authentication (mutual TLS) with the OPS Portal API, explicitly configuring TLS 1.2 can help resolve certificate rejection issues. This implementation enhances the `OpsPortalClient` class to explicitly use TLS 1.2 for all HTTPS connections.

## Files Modified/Added

- **Modified**: `src/ops_portal/api.py` - Added TLS 1.2 configuration
- **Added**: `tests/test_tls_version.py` - Test script for TLS 1.2 configuration
- **Added**: `docs/tls_certificate_authentication.md` - Documentation for TLS 1.2 certificate authentication
- **Added**: `examples/certificate_auth_example.py` - Example script demonstrating TLS 1.2 certificate authentication

## Key Features

1. **Explicit TLS 1.2 Configuration**: Forces the use of TLS 1.2 for all HTTPS connections
2. **Disabled Older Protocols**: Disables SSLv2, SSLv3, TLS 1.0, and TLS 1.1
3. **TLS Version Logging**: Logs the TLS version used for each connection
4. **Comprehensive Testing**: Includes a test script to verify TLS 1.2 is being used
5. **Detailed Documentation**: Provides documentation on TLS 1.2 certificate authentication

## How to Use

### Basic Usage

```python
from src.ops_portal.api import OpsPortalClient

# Configure the client
config = {
    'auth_url': 'https://api.example.com/auth',
    'item_url': 'https://api.example.com/items',
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret',
    'verify_ssl': True,
    'cert_pem': '-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----',
    'key_pem': '-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----'
}

# Create the client - TLS 1.2 is automatically configured
client = OpsPortalClient(config)

# Authenticate with the API
success = client.authenticate()

# Send a record
record = {
    'tenantItemID': 'record_001',
    'title': 'Test Record',
    'description': 'This is a test record'
}
status_code, response = client.send_record(record)
```

### Running the Example

```bash
# Make sure environment variables are set in .env file
python examples/certificate_auth_example.py
```

### Testing TLS 1.2 Configuration

```bash
python tests/test_tls_version.py
```

## Troubleshooting

If certificate authentication still fails after configuring TLS 1.2:

1. **Check Certificate Validity**: Ensure the certificate is valid and not expired
2. **Verify Domain Match**: The certificate's domain should match the API endpoint
3. **Check Certificate Chain**: Ensure the full certificate chain is trusted
4. **Inspect Server Requirements**: The server might have specific TLS requirements
5. **Enable Debug Logging**: Use the debug mode in the test script for detailed logs

## Advanced Configuration

For more complex scenarios, refer to the detailed documentation in `docs/tls_certificate_authentication.md`.

## References

- [Python Requests Documentation](https://docs.python-requests.org/)
- [Python SSL Module Documentation](https://docs.python.org/3/library/ssl.html)
- [TLS 1.2 Specification (RFC 5246)](https://tools.ietf.org/html/rfc5246)
- [X.509 Certificate Authentication](https://en.wikipedia.org/wiki/X.509)

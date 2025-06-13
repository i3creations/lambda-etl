"""
OPS Portal API Module

This module handles authentication with the DHS OPS Portal API and sending data records.
It provides functionality to authenticate with the API and send records to the OPS Portal.
"""

import requests
import logging
import ssl
import tempfile
import os
from typing import Dict, List, Tuple, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util import ssl_
from ..utils.logging_utils import get_logger

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# Get logger for this module
logger = get_logger('ops_portal.api')


class OpsPortalClient:
    """
    Client for interacting with the DHS OPS Portal API.
    
    This class handles authentication and sending data to the OPS Portal API.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OPS Portal API client.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing API settings
                Required keys:
                - auth_url: URL for authentication
                - item_url: URL for sending items
                - client_id: Client ID for authentication
                - client_secret: Client secret for authentication
                - verify_ssl: Whether to verify SSL certificates (default: True)
                Optional keys:
                - cert_pfx: Path to PKCS#12 (.pfx) certificate file
                - pfx_password: Password for the PKCS#12 file
                - cert_pfx_data: Binary PKCS#12 certificate data from AWS Secrets Manager
        """
        self.auth_url = config.get('auth_url')
        self.item_url = config.get('item_url')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.verify_ssl = config.get('verify_ssl', True)
        # Support both cert_pfx and cert_path for the PKCS#12 certificate file
        self.cert_pfx = config.get('cert_pfx') or config.get('cert_path')
        self.pfx_password = config.get('pfx_password')
        # Certificate data from AWS Secrets Manager
        self.cert_pfx_data = config.get('cert_pfx_data')
        
        # Validate required configuration
        if not self.auth_url:
            raise ValueError("Missing required configuration: auth_url")
        if not self.item_url:
            raise ValueError("Missing required configuration: item_url")
        
        # Set up session
        self.session = requests.session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': 'OPS-Portal-Client/1.0 (Python/requests)',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive'
        })
        
        # Configure SSL verification
        if self.verify_ssl:
            self.session.verify = True
        else:
            self.session.verify = False
            # Disable SSL warnings when verification is disabled
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Configure TLS version and SSL certificate
        self._configure_tls_version()
        self._configure_ssl_certificate()
        
        # Token will be set during authentication
        self.token = None
    
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
    
    
    def log_certificate_format_details(self):
        """
        Log detailed information about the x509 certificate format being used.
        This method can be called to get comprehensive certificate format information.
        """
        if not self.session.cert:
            logger.info("No X.509 client certificate configured")
            return
        
        logger.info("=== Current X509 Certificate Configuration ===")
        logger.info("Certificate Type: X.509 Client Certificate")
        logger.info("Usage: Mutual TLS (mTLS) authentication with OPS Portal API")
        logger.info("Transport: TLS/SSL layer during HTTPS requests")
        
        if isinstance(self.session.cert, tuple) and len(self.session.cert) == 2:
            cert_path, key_path = self.session.cert
            logger.info(f"Certificate file: {cert_path}")
            logger.info(f"Private key file: {key_path}")
            
            # Try to read and analyze the certificate file if it exists
            try:
                if os.path.exists(cert_path):
                    with open(cert_path, 'r') as f:
                        cert_content = f.read()
                    
                    if CRYPTOGRAPHY_AVAILABLE:
                        from cryptography import x509
                        from cryptography.hazmat.primitives import hashes
                        certificate = x509.load_pem_x509_certificate(cert_content.encode('utf-8'))
                        logger.info(f"Certificate Subject: {certificate.subject}")
                        logger.info(f"Certificate Issuer: {certificate.issuer}")
                        logger.info(f"Certificate Serial: {certificate.serial_number}")
                        logger.info(f"Certificate Valid Until: {certificate.not_valid_after_utc}")
                        
                        # Log certificate fingerprint for identification
                        sha256_fingerprint = certificate.fingerprint(hashes.SHA256()).hex()
                        logger.info(f"Certificate SHA256 Fingerprint: {sha256_fingerprint}")
                        
            except Exception as e:
                logger.warning(f"Could not analyze certificate file: {e}")
        
        logger.info("=== End X509 Certificate Configuration ===")
    
    def _configure_ssl_certificate(self):
        """
        Configure SSL client certificate for the session.
        
        Uses PKCS#12 (.pfx) file format which contains the complete
        certificate chain, which is required for successful authentication.
        
        Supports both file system and AWS Secrets Manager as certificate sources.
        """
        try:
            if self.cert_pfx_data:
                logger.info("Using PKCS#12 certificate data from AWS Secrets Manager")
                self._configure_pfx_certificate()
            elif self.cert_pfx:
                logger.info("Using PKCS#12 (.pfx) certificate from file system")
                self._configure_pfx_certificate()
            else:
                logger.warning("No certificate configuration provided")
                
        except Exception as e:
            logger.error(f"Failed to configure SSL certificate: {str(e)}")
            raise
    
    
    def _configure_pfx_certificate(self):
        """
        Configure SSL certificate from PKCS#12 (.pfx) file or data.
        
        This method extracts the certificate, private key, and the entire certificate chain
        from a PKCS#12 (.pfx) file or binary data and configures them for use with the session.
        
        It supports two sources:
        1. File system: Using self.cert_pfx path to load the certificate from a file
        2. AWS Secrets Manager: Using self.cert_pfx_data binary data directly
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.error("cryptography library not available - cannot handle PKCS#12 certificates")
            raise ImportError("cryptography library required for PKCS#12 certificate handling")
        
        try:
            # Get the password for the .pfx file
            pfx_password = getattr(self, 'pfx_password', None)
            if pfx_password:
                # Remove surrounding quotes if present
                pfx_password = pfx_password.strip("'\"")
            
            # Convert password to bytes if it's not None
            password_bytes = pfx_password.encode('utf-8') if pfx_password else None
            
            # Determine the source of the certificate (file or binary data)
            if self.cert_pfx_data:
                # Use binary data directly from AWS Secrets Manager
                pfx_data = self.cert_pfx_data
                logger.info("Using PKCS#12 certificate data from AWS Secrets Manager")
            elif self.cert_pfx:
                # Read the .pfx file from the file system
                with open(self.cert_pfx, 'rb') as pfx_file:
                    pfx_data = pfx_file.read()
                logger.info(f"Reading PKCS#12 file from file system: {self.cert_pfx}")
            else:
                logger.error("No PKCS#12 certificate source available")
                raise ValueError("No PKCS#12 certificate source available")
            
            # Load the PKCS#12 data
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data, 
                password_bytes
            )
            
            logger.info("Successfully parsed PKCS#12 data")
            logger.info(f"Certificate subject: {certificate.subject}")
            logger.info(f"Certificate issuer: {certificate.issuer}")
            logger.info(f"Additional certificates in chain: {len(additional_certificates) if additional_certificates else 0}")
            
            # Create temporary files for the certificate chain and key
            cert_chain_fd, cert_chain_path = tempfile.mkstemp(suffix='.pem')
            key_fd, key_path = tempfile.mkstemp(suffix='.key')
            
            try:
                # Write the certificate chain to a temporary file
                # Start with the end-entity certificate
                with os.fdopen(cert_chain_fd, 'wb') as cert_chain_file:
                    # Write the end-entity certificate
                    cert_chain_file.write(certificate.public_bytes(serialization.Encoding.PEM))
                    
                    # Write all additional certificates in the chain
                    if additional_certificates:
                        for i, additional_cert in enumerate(additional_certificates):
                            cert_chain_file.write(additional_cert.public_bytes(serialization.Encoding.PEM))
                            logger.info(f"Added certificate {i+1} to chain: {additional_cert.subject}")
                
                # Write the private key to a temporary file
                with os.fdopen(key_fd, 'wb') as key_file:
                    key_file.write(private_key.private_bytes(
                        serialization.Encoding.PEM,
                        serialization.PrivateFormat.PKCS8,
                        serialization.NoEncryption()
                    ))
                
                # Set proper file permissions for security
                os.chmod(cert_chain_path, 0o600)
                os.chmod(key_path, 0o600)
                
                # Configure the session with the temporary files
                self.session.cert = (cert_chain_path, key_path)
                logger.info("SSL client certificate configured from PKCS#12 file with complete certificate chain")
                logger.info(f"Certificate chain file: {cert_chain_path}")
                logger.info(f"Key file: {key_path}")
                
                # Store paths for cleanup (if needed)
                self._temp_cert_path = cert_chain_path
                self._temp_key_path = key_path
                
            except Exception as e:
                # Clean up temporary files on error
                try:
                    os.unlink(cert_chain_path)
                    os.unlink(key_path)
                except:
                    pass
                raise e
                
        except Exception as e:
            logger.error(f"Failed to configure PKCS#12 certificate: {str(e)}")
            raise
    

    def authenticate(self) -> bool:
        """
        Authenticate with the OPS Portal API.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            logger.info(f"Authenticating with OPS Portal API at {self.auth_url}")
            logger.info(f"SSL verification enabled: {self.verify_ssl}")
            logger.info(f"Client certificate configured: {bool(self.session.cert)}")
            
            # Log x509 certificate usage for OPS API
            if self.session.cert:
                logger.info("=== X509 Certificate Usage for OPS API ===")
                logger.info("Using X.509 client certificate for mutual TLS authentication")
                if isinstance(self.session.cert, tuple) and len(self.session.cert) == 2:
                    cert_path, key_path = self.session.cert
                    logger.info(f"Certificate file path: {cert_path}")
                    logger.info(f"Private key file path: {key_path}")
                logger.info("Certificate will be sent to OPS Portal API for client authentication")
                logger.info("=== End X509 Certificate Usage ===")
            
            # Use lowercase field names as shown in the reference example
            creds = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret
            }
            
            if self.client_id:
                logger.debug(f"Authentication payload: clientId={self.client_id[:8]}...")
            else:
                logger.debug("Authentication payload: clientId=<empty>")
            
            response = self.session.post(
                self.auth_url,
                json=creds,
                timeout=30  # Add timeout to prevent hanging
            )
            
            logger.info(f"Authentication response status: {response.status_code}")
            logger.debug(f"TLS version used: {response.raw.connection.socket.version() if hasattr(response.raw, 'connection') and hasattr(response.raw.connection, 'socket') else 'Unknown'}")
            
            response.raise_for_status()
            
            # The response should contain the token directly
            # Store the token string, not the entire response
            token_response = response.json()
            
            # Handle both string token and object response formats
            if isinstance(token_response, str):
                self.token = token_response
            elif isinstance(token_response, dict) and 'token' in token_response:
                self.token = token_response['token']
            elif isinstance(token_response, dict) and 'access_token' in token_response:
                self.token = token_response['access_token']
            else:
                # If response is not a string, treat the whole response as the token
                # This matches the reference example behavior
                self.token = token_response
            
            # Update session headers with the authorization token
            self.session.headers.update(
                {'Authorization': f'Bearer {self.token}'}
            )
            
            logger.info("Authentication successful")
            logger.debug(f"Token type: {type(self.token)}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            
            # Handle specific error cases
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                
                # Check for service downtime indicators
                if status_code >= 500:
                    logger.error(f"OPS Portal service appears to be down (HTTP {status_code})")
                    
                    # Check for specific ASP.NET Core startup errors
                    if 'ASP.NET Core app failed to start' in e.response.text:
                        logger.error("Service startup failure detected - ASP.NET Core app failed to start within timeout")
                        logger.warning("This is a server-side issue. The service may be undergoing maintenance or experiencing technical difficulties.")
                    elif 'Internal Server Error' in e.response.text:
                        logger.error("Internal server error detected - service may be temporarily unavailable")
                    else:
                        logger.error(f"Server error {status_code} - service may be experiencing issues")
                        
                elif status_code == 404:
                    logger.error("Authentication endpoint not found - check if the auth_url is correct")
                elif status_code == 403:
                    logger.error("Access forbidden - check client credentials or SSL certificate")
                elif status_code == 401:
                    logger.error("Authentication failed - invalid client credentials")
                else:
                    logger.error(f"HTTP {status_code} error during authentication")
                
                # Log response details for debugging
                try:
                    error_detail = e.response.json()
                    logger.debug(f"Error response JSON: {error_detail}")
                except:
                    # For HTML error pages (like the ASP.NET error), just log a snippet
                    response_text = e.response.text
                    if len(response_text) > 500:
                        logger.debug(f"Error response text (truncated): {response_text[:500]}...")
                    else:
                        logger.debug(f"Error response text: {response_text}")
            else:
                # Network-level errors (connection timeout, DNS issues, etc.)
                logger.error("Network error during authentication - check connectivity to OPS Portal service")
                
            return False
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return False
    
    def send_record(self, record: Dict[str, Any]) -> Tuple[int, Any]:
        """
        Send a single record to the OPS Portal API.
        
        Args:
            record (Dict[str, Any]): Record data to send
            
        Returns:
            Tuple[int, Any]: Tuple containing (status_code, response_data)
        """
        record_id = record.get('tenantItemID', 'unknown')
        
        try:
            # Log x509 certificate usage for this API call
            if self.session.cert:
                logger.debug(f"Sending record {record_id} to OPS API using X.509 client certificate authentication")
                logger.debug("X.509 certificate format: PEM-encoded, will be presented during TLS handshake")
            
            # Log the complete JSON payload for troubleshooting
            logger.debug(f"Sending record {record_id} to OPS API with payload: {record}")
            
            response = self.session.post(
                self.item_url,
                json=record
            )
            
            status_code = response.status_code
            
            # Log TLS version used for this request if available
            if hasattr(response.raw, 'connection') and hasattr(response.raw.connection, 'socket'):
                tls_version = response.raw.connection.socket.version()
                logger.debug(f"TLS version used for API call: {tls_version}")
            
            # Handle different response types
            try:
                response_data = response.json()
            except ValueError:
                # Response is not JSON (e.g., HTML error page)
                response_data = response.text
            
            # Log the complete response data for troubleshooting
            logger.debug(f"Response for record {record_id}: {response_data}")
            
            if 200 <= status_code < 300:
                logger.info(f"Successfully sent record {record_id}")
            else:
                # Log specific error details for failed submissions
                if status_code >= 500:
                    logger.error(f"Server error {status_code} when sending record {record_id} - service may be down")
                    if 'ASP.NET Core app failed to start' in str(response_data):
                        logger.error(f"Service startup failure detected while sending record {record_id}")
                elif status_code == 401:
                    logger.error(f"Authentication failed when sending record {record_id} - token may have expired")
                elif status_code == 403:
                    logger.error(f"Access forbidden when sending record {record_id} - check permissions")
                elif status_code == 404:
                    logger.error(f"Item endpoint not found when sending record {record_id} - check item_url")
                else:
                    logger.warning(
                        f"Failed to send record {record_id}: "
                        f"Status {status_code}, Response: {response_data}"
                    )
            
            return status_code, response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending record {record_id}: {str(e)}")
            
            # Check if this is a service downtime issue
            if hasattr(e, 'response') and e.response is not None and e.response.status_code >= 500:
                logger.error(f"OPS Portal service appears to be down when sending record {record_id}")
            
            return 0, str(e)
        except Exception as e:
            logger.error(f"Unexpected error sending record {record_id}: {str(e)}")
            return 0, str(e)
    
    def send_records(self, records: List[Dict[str, Any]]) -> Dict[str, Tuple[int, Any]]:
        """
        Send multiple records to the OPS Portal API.
        
        Args:
            records (List[Dict[str, Any]]): List of record data to send
            
        Returns:
            Dict[str, Tuple[int, Any]]: Dictionary mapping record IDs to (status_code, response_data) tuples
        """
        if not self.token:
            success = self.authenticate()
            if not success:
                logger.error("Cannot send records: Authentication failed")
                return {record.get('tenantItemID', f'unknown_{i}'): (0, "Authentication failed") 
                        for i, record in enumerate(records)}
        
        logger.info(f"Sending {len(records)} records to OPS Portal API")
        
        responses = {}
        for record in records:
            record_id = record.get('tenantItemID', 'unknown')
            status_code, response_data = self.send_record(record)
            responses[record_id] = (status_code, response_data)
        
        # Log summary
        success_count = sum(1 for status, _ in responses.values() if 200 <= status < 300)
        logger.info(f"Successfully sent {success_count} of {len(records)} records")
        
        return responses


def send(data: List[Dict[str, Any]], config: Optional[Dict[str, Any]] = None) -> Dict[str, Tuple[int, Any]]:
    """
    Send data records to the OPS Portal API.
    
    This is a convenience function that creates an OpsPortalClient and sends the records.
    This function matches the interface of the reference example in 'OPS API Example/send.py'.
    
    Args:
        data (List[Dict[str, Any]]): List of record data to send
        config (Dict[str, Any], optional): Configuration dictionary. If None, uses default values.
        
    Returns:
        Dict[str, Tuple[int, Any]]: Dictionary mapping record IDs to (status_code, response_data) tuples
    """
    # Use default configuration if none provided
    if config is None:
        config = {
            'auth_url': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/auth/token',
            'item_url': 'https://gii-dev.ardentmc.net/dhsopsportal.api/api/Item',
            'client_id': '',
            'client_secret': '',
            'verify_ssl': False,  # Default to False for backward compatibility
            'cert_pfx': None,     # Path to PKCS#12 (.pfx) certificate file
            'pfx_password': None  # Password for the PKCS#12 file
        }
    
    client = OpsPortalClient(config)
    return client.send_records(data)

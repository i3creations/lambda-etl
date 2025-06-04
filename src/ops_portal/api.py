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
from ..utils.logging_utils import get_logger

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
        """
        self.auth_url = config.get('auth_url')
        self.item_url = config.get('item_url')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.verify_ssl = config.get('verify_ssl', True)
        self.cert_file = config.get('cert_file')
        self.key_file = config.get('key_file')
        self.cert_data = config.get('cert_data')  # For certificate data as string
        
        # Validate required configuration
        if not self.auth_url:
            raise ValueError("Missing required configuration: auth_url")
        if not self.item_url:
            raise ValueError("Missing required configuration: item_url")
        
        # Set up session
        self.session = requests.session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self.session.verify = self.verify_ssl
        
        # Configure SSL certificate if provided
        if self.cert_file and self.key_file:
            self.session.cert = (self.cert_file, self.key_file)
            logger.info("SSL client certificate configured from files")
        elif self.cert_data:
            # Handle certificate data as string (for Lambda environments)
            try:
                # Create temporary files for certificate data
                cert_fd, cert_path = tempfile.mkstemp(suffix='.pem')
                key_fd, key_path = tempfile.mkstemp(suffix='.key')
                
                # Write certificate data to temporary files
                with os.fdopen(cert_fd, 'w') as cert_file:
                    cert_file.write(self.cert_data.get('cert', ''))
                with os.fdopen(key_fd, 'w') as key_file:
                    key_file.write(self.cert_data.get('key', ''))
                
                self.session.cert = (cert_path, key_path)
                logger.info("SSL client certificate configured from data")
            except Exception as e:
                logger.error(f"Failed to configure SSL certificate from data: {str(e)}")
                # Clean up temporary files on error
                try:
                    os.unlink(cert_path)
                    os.unlink(key_path)
                except:
                    pass
        
        # Token will be set during authentication
        self.token = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with the OPS Portal API.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            logger.info(f"Authenticating with OPS Portal API at {self.auth_url}")
            
            # Use lowercase field names as shown in the reference example
            creds = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret
            }
            
            response = self.session.post(
                self.auth_url,
                json=creds
            )
            
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
            response = self.session.post(
                self.item_url,
                json=record
            )
            
            status_code = response.status_code
            
            # Handle different response types
            try:
                response_data = response.json()
            except ValueError:
                # Response is not JSON (e.g., HTML error page)
                response_data = response.text
            
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
            'verify_ssl': False  # Default to False for backward compatibility
        }
    
    client = OpsPortalClient(config)
    return client.send_records(data)

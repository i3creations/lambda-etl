"""
OPS Portal API Module

This module handles authentication with the DHS OPS Portal API and sending data records.
It provides functionality to authenticate with the API and send records to the OPS Portal.
"""

import requests
import logging
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
            
            creds = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret
            }
            
            response = self.session.post(
                self.auth_url,
                json=creds
            )
            
            response.raise_for_status()
            
            self.token = response.json()
            self.session.headers.update(
                {'Authorization': f'Bearer {self.token}'}
            )
            
            logger.info("Authentication successful")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    
    def send_record(self, record: Dict[str, Any]) -> Tuple[int, Any]:
        """
        Send a single record to the OPS Portal API.
        
        Args:
            record (Dict[str, Any]): Record data to send
            
        Returns:
            Tuple[int, Any]: Tuple containing (status_code, response_data)
        """
        try:
            response = self.session.post(
                self.item_url,
                json=record
            )
            
            status_code = response.status_code
            response_data = response.json()
            
            if 200 <= status_code < 300:
                logger.info(f"Successfully sent record {record.get('tenantItemID', 'unknown')}")
            else:
                logger.warning(
                    f"Failed to send record {record.get('tenantItemID', 'unknown')}: "
                    f"Status {status_code}, Response: {response_data}"
                )
            
            return status_code, response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending record {record.get('tenantItemID', 'unknown')}: {str(e)}")
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

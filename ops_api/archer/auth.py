"""
Archer Authentication Module

This module provides functionality to authenticate with the USCIS Archer system
and retrieve Significant Incident Report (SIR) data.

This module uses the ArcherAuth class from the uscis-opts package, which can be
installed via pip: `pip install uscis-opts`.
"""

from typing import Dict, List, Any, Optional
from ..utils.logging_utils import get_logger

# Get logger for this module
logger = get_logger('archer.auth')

# Import the ArcherAuth class from the uscis-opts package
try:
    from opts.ArcherAuth import ArcherAuth
    logger.info("Successfully imported ArcherAuth from uscis-opts package")
except ImportError:
    logger.error(
        "Could not import ArcherAuth from uscis-opts package. "
        "Please install it using: pip install uscis-opts"
    )
    
    # Define a fallback ArcherAuth class for development/testing
    class ArcherAuth:
        """
        Fallback implementation of ArcherAuth for development/testing.
        
        This class provides the same interface as the real ArcherAuth class
        but does not actually connect to the Archer system.
        """
        
        def __init__(self, username: str, password: str, instance: str, url: str = None):
            """
            Initialize the Archer authentication client.
            
            Args:
                username (str): Username for Archer authentication
                password (str): Password for Archer authentication
                instance (str): Archer instance name
                url (str, optional): Archer URL endpoint
            """
            self.username = username
            self.password = password
            self.instance = instance
            self.url = url
            logger.info(f"Initialized fallback ArcherAuth for instance: {instance}, url: {url}")
        
        def authenticate(self) -> bool:
            """
            Authenticate with the Archer system.
            
            Returns:
                bool: True if authentication was successful, False otherwise
            """
            logger.warning("Using fallback ArcherAuth implementation - no actual authentication performed")
            return True
        
        def get_sir_data(self, since_date=None) -> List[Dict[str, Any]]:
            """
            Retrieve Significant Incident Report (SIR) data from Archer.
            
            Args:
                since_date (datetime, optional): If provided, only retrieve SIRs created
                    or modified since this date.
                    
            Returns:
                List[Dict[str, Any]]: List of SIR data records
            """
            logger.warning("Using fallback ArcherAuth implementation - returning empty data")
            return []


def get_archer_auth(config: Dict[str, Any]) -> ArcherAuth:
    """
    Create an ArcherAuth instance from configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary containing Archer settings
            Required keys:
            - username: Username for Archer authentication
            - password: Password for Archer authentication
            - instance: Archer instance name
            - url: Archer URL endpoint
            
    Returns:
        ArcherAuth: Initialized ArcherAuth instance
    """
    username = config.get('username', '')
    password = config.get('password', '')
    instance = config.get('instance', '')
    url = config.get('url', '')
    
    try:
        auth = ArcherAuth(username, password, instance, url)
        logger.info(f"Created ArcherAuth instance for instance: {instance}, url: {url}")
        return auth
    except Exception as e:
        logger.error(f"Error creating ArcherAuth instance: {str(e)}")
        raise

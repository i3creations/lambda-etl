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

# Import the ArcherAuth class from the archer package
try:
    from archer.ArcherAuth import ArcherAuth
    logger.info("Successfully imported ArcherAuth from archer package")
except ImportError:
    logger.error(
        "Could not import ArcherAuth from archer package. "
        "Please ensure the Archer_API package is properly installed"
    )
    
    # Define a fallback ArcherAuth class for development/testing
    class ArcherAuth:
        """
        Fallback implementation of ArcherAuth for development/testing.
        
        This class provides the same interface as the real ArcherAuth class
        but does not actually connect to the Archer system.
        """
        
        def __init__(self, ins: str, usr: str, pwd: str, url: str, dom: str = ''):
            """
            Initialize the Archer authentication client.
            
            Args:
                ins (str): Archer instance name
                usr (str): Username for Archer authentication
                pwd (str): Password for Archer authentication
                url (str): Archer URL endpoint
                dom (str, optional): User domain (usually blank)
            """
            self.ins = ins
            self.usr = usr
            self.pwd = pwd
            self.base_url = url
            self.dom = dom
            self.authenticated = False
            logger.info(f"Initialized fallback ArcherAuth for instance: {ins}, url: {url}")
        
        def login(self) -> None:
            """
            Login to Archer instance with credentials provided during instantiation.
            """
            logger.warning("Using fallback ArcherAuth implementation - no actual authentication performed")
            self.authenticated = True
        
        def logout(self) -> None:
            """
            Logout of Archer instance with signed credentials received during login.
            """
            logger.warning("Using fallback ArcherAuth implementation - no actual logout performed")
            self.authenticated = False
            
        def __enter__(self):
            self.login()
            return self
            
        def __exit__(self, *args, **kwargs):
            self.logout()
            return False
            
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
    domain = config.get('domain', '')
    
    try:
        # Note: Parameter order matches the original ArcherAuth class (ins, usr, pwd, url, dom)
        auth = ArcherAuth(instance, username, password, url, domain)
        logger.info(f"Created ArcherAuth instance for instance: {instance}, url: {url}")
        return auth
    except Exception as e:
        logger.error(f"Error creating ArcherAuth instance: {str(e)}")
        raise

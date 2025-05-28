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
    from archer.ArcherAuth import ArcherAuth as BaseArcherAuth
    logger.info("Successfully imported ArcherAuth from archer package")
    
    # Extend the ArcherAuth class to add the get_sir_data method
    class ArcherAuth(BaseArcherAuth):
        """
        Extended ArcherAuth class that adds the get_sir_data method.
        
        This class extends the base ArcherAuth class from the archer package
        to add functionality specific to retrieving SIR data.
        """
        
        def get_sir_data(self, since_date=None) -> List[Dict[str, Any]]:
            """
            Retrieve Significant Incident Report (SIR) data from Archer.
            
            Args:
                since_date (datetime, optional): If provided, only retrieve SIRs created
                    or modified since this date.
                    
            Returns:
                List[Dict[str, Any]]: List of SIR data records
            """
            # Ensure we're authenticated
            if not self.authenticated:
                self.login()
                
            try:
                # Import the necessary classes
                from archer.content.ContentClient import ContentClient
                
                # Create a ContentClient instance
                client = ContentClient(self)
                
                # Get the endpoints (levels) available in Archer
                endpoints = client.get_endpoints()
                
                # Define the level alias for SIR data
                # Based on the example, it seems SIR data is stored in a level called 'Incidents'
                sir_level_alias = 'Incidents'
                
                # Check if the level alias exists in the available endpoints
                if sir_level_alias not in [endpoint.get('name') for endpoint in endpoints]:
                    logger.warning(f"Level alias '{sir_level_alias}' not found in available endpoints")
                    # Try to find a similar level alias
                    for endpoint in endpoints:
                        if 'incident' in endpoint.get('name', '').lower():
                            sir_level_alias = endpoint.get('name')
                            logger.info(f"Using level alias '{sir_level_alias}' instead")
                            break
                    else:
                        logger.error(f"Could not find a suitable level alias for SIR data")
                        return []
                
                # Get the metadata for the SIR level
                level_data = client.get_levels_metadata([sir_level_alias])
                
                # Extract the SIR records
                sir_records = level_data.get(sir_level_alias, [])
                
                # If since_date is provided, filter the records
                if since_date and sir_records:
                    # This assumes there's a field in the records that contains the creation/modification date
                    # The field name might be different in the actual data
                    filtered_records = []
                    for record in sir_records:
                        # Try to find a date field in the record
                        record_date = None
                        for field_name, field_value in record.items():
                            if 'date' in field_name.lower() and field_value:
                                try:
                                    from datetime import datetime
                                    # Try to parse the date string
                                    record_date = datetime.fromisoformat(field_value.replace('Z', '+00:00'))
                                    break
                                except (ValueError, AttributeError):
                                    # If parsing fails, continue to the next field
                                    continue
                        
                        # If a valid date was found and it's after since_date, include the record
                        if record_date and record_date >= since_date:
                            filtered_records.append(record)
                    
                    sir_records = filtered_records
                    logger.info(f"Filtered SIR data to {len(sir_records)} records since {since_date}")
                
                logger.info(f"Retrieved {len(sir_records)} SIR records from Archer")
                return sir_records
                
            except Exception as e:
                logger.exception(f"Error retrieving SIR data from Archer: {str(e)}")
                return []
            
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

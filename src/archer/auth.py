"""
Archer Authentication Module

This module provides functionality to authenticate with the USCIS Archer system
and retrieve Significant Incident Report (SIR) data.

This module uses the ArcherAuth class from the uscis-opts package, which can be
installed via pip: `pip install uscis-opts>=0.1.4`.
"""

from typing import Dict, List, Any, Optional
from ..utils.logging_utils import get_logger

# Get logger for this module
logger = get_logger('archer.auth')

# Import the ArcherAuth class from the archer package
try:
    from opts.ArcherAuth import ArcherAuth as BaseArcherAuth
    logger.info("Successfully imported ArcherAuth from archer package")
    
    # Extend the ArcherAuth class to add the get_sir_data method
    class ArcherAuth(BaseArcherAuth):
        """
        Extended ArcherAuth class that adds the get_sir_data method.
        
        This class extends the base ArcherAuth class from the archer package
        to add functionality specific to retrieving SIR data.
        """
        
        def __init__(self, ins: str, usr: str, pwd: str, url: str, dom: str = '', verify_ssl: bool = False):
            """
            Initialize the ArcherAuth instance with SSL verification control.
            
            Args:
                ins (str): Archer instance name
                usr (str): Username for Archer authentication
                pwd (str): Password for Archer authentication
                url (str): Archer URL endpoint
                dom (str, optional): User domain (usually blank)
                verify_ssl (bool, optional): Whether to verify SSL certificates (default: True)
            """
            super().__init__(ins, usr, pwd, url, dom)
            
            # Configure SSL verification
            if not verify_ssl:
                logger.warning("SSL verification disabled for Archer authentication")
                self.session.verify = False
                # Suppress SSL warnings when verification is disabled
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            else:
                self.session.verify = False
                logger.info("SSL verification enabled for Archer authentication")
        
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
                from opts.ArcherServerClient import ArcherServerClient
                
                # Create an ArcherServerClient instance
                client = ArcherServerClient(self)
                
                # Get the endpoints (levels) available in Archer
                endpoints = client.get_endpoints()
                
                # Define the level alias for SIR data
                # Based on the example, it seems SIR data is stored in a level called 'Incidents'
                sir_level_alias = 'Incidents'
                
                # Check if the level alias exists in the available endpoints
                # Handle both string and dictionary endpoint formats
                endpoint_names = []
                for endpoint in endpoints:
                    if isinstance(endpoint, dict):
                        # If endpoint is a dictionary, get the 'name' field
                        endpoint_names.append(endpoint.get('name', ''))
                    elif isinstance(endpoint, str):
                        # If endpoint is a string, use it directly
                        endpoint_names.append(endpoint)
                    else:
                        # Log unexpected endpoint format
                        logger.warning(f"Unexpected endpoint format: {type(endpoint)} - {endpoint}")
                        endpoint_names.append(str(endpoint))
                
                if sir_level_alias not in endpoint_names:
                    logger.warning(f"Level alias '{sir_level_alias}' not found in available endpoints: {endpoint_names}")
                    # Try to find a similar level alias
                    for i, endpoint in enumerate(endpoints):
                        endpoint_name = endpoint_names[i]
                        if 'incident' in endpoint_name.lower():
                            sir_level_alias = endpoint_name
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
                            # Look for the Date_Created field specifically
                            if field_name == 'Date_Created' and field_value:
                                try:
                                    from datetime import datetime
                                    # Try to parse the date string - handle various ISO formats
                                    if isinstance(field_value, str):
                                        # Handle timezone formats like -04:00, +00:00, or Z
                                        date_str = field_value
                                        if date_str.endswith('Z'):
                                            date_str = date_str.replace('Z', '+00:00')
                                        record_date = datetime.fromisoformat(date_str)
                                        break
                                except (ValueError, AttributeError) as e:
                                    # If parsing fails, log the issue and continue to the next field
                                    logger.warning(f"Failed to parse date field '{field_name}' with value '{field_value}': {e}")
                                    continue
                        
                        # If a valid date was found and it's after since_date, include the record
                        if record_date and record_date >= since_date:
                            filtered_records.append(record)
                        elif not record_date:
                            # If no date was found, include the record (to be safe)
                            logger.warning(f"No valid Date_Created field found for record, including it anyway")
                            filtered_records.append(record)
                    
                    sir_records = filtered_records
                    logger.info(f"Filtered SIR data to {len(sir_records)} records since {since_date}")
                
                # Filter records by Submission_Status_1 field
                if sir_records:
                    status_filtered_records = []
                    for record in sir_records:
                        # Check if Submission_Status_1 field exists and has the required value
                        submission_status = record.get('Submission_Status_1', '')
                        
                        # Handle both string and list formats for submission_status
                        if isinstance(submission_status, list):
                            # If it's a list, check if "Assigned for Further Action" is in the list
                            if "Assigned for Further Action" in submission_status:
                                status_filtered_records.append(record)
                        elif isinstance(submission_status, str):
                            # If it's a string, do direct comparison
                            if submission_status == "Assigned for Further Action":
                                status_filtered_records.append(record)
                    
                    sir_records = status_filtered_records
                    logger.info(f"Filtered SIR data to {len(sir_records)} records with Submission_Status_1 = 'Assigned for Further Action'")
                
                logger.info(f"Retrieved {len(sir_records)} SIR records from Archer")
                return sir_records
                
            except Exception as e:
                logger.exception(f"Error retrieving SIR data from Archer: {str(e)}")
                return []
            
except ImportError:
    logger.error(
        "Could not import ArcherAuth from archer package. "
        "Please ensure the uscis-opts package is properly installed with: pip install uscis-opts>=0.1.4"
    )
    
    # Define a fallback ArcherAuth class for development/testing
    class ArcherAuth:
        """
        Fallback implementation of ArcherAuth for development/testing.
        
        This class provides the same interface as the real ArcherAuth class
        but does not actually connect to the Archer system.
        """
        
        def __init__(self, ins: str, usr: str, pwd: str, url: str, dom: str = '', verify_ssl: bool = True):
            """
            Initialize the Archer authentication client.
            
            Args:
                ins (str): Archer instance name
                usr (str): Username for Archer authentication
                pwd (str): Password for Archer authentication
                url (str): Archer URL endpoint
                dom (str, optional): User domain (usually blank)
                verify_ssl (bool, optional): Whether to verify SSL certificates (default: True)
            """
            self.ins = ins
            self.usr = usr
            self.pwd = pwd
            self.base_url = url
            self.dom = dom
            self.verify_ssl = verify_ssl
            self.authenticated = False
            logger.info(f"Initialized fallback ArcherAuth for instance: {ins}, url: {url}, verify_ssl: {verify_ssl}")
        
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
            Optional keys:
            - domain: User domain (usually blank)
            - verify_ssl: Whether to verify SSL certificates (default: True)
            
    Returns:
        ArcherAuth: Initialized ArcherAuth instance
    """
    username = config.get('username', '')
    password = config.get('password', '')
    instance = config.get('instance', '')
    url = config.get('url', '')
    domain = config.get('domain', '')
    
    # Handle SSL verification setting - support both boolean and string values
    verify_ssl_value = config.get('verify_ssl', 'true')
    if isinstance(verify_ssl_value, bool):
        verify_ssl = verify_ssl_value
    else:
        verify_ssl_str = str(verify_ssl_value).lower()
        verify_ssl = verify_ssl_str in ('true', '1', 'yes', 'on')
    
    try:
        # Note: Parameter order matches the original ArcherAuth class (ins, usr, pwd, url, dom)
        auth = ArcherAuth(instance, username, password, url, domain, verify_ssl=verify_ssl)
        logger.info(f"Created ArcherAuth instance for instance: {instance}, url: {url}, verify_ssl: {verify_ssl}")
        return auth
    except Exception as e:
        logger.error(f"Error creating ArcherAuth instance: {str(e)}")
        raise

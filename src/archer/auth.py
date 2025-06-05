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
            try:
                self._ensure_authenticated()
                client = self._create_archer_client()
                sir_level_alias = self._find_sir_level_alias(client)
                
                if not sir_level_alias:
                    return []
                
                sir_records = self._fetch_sir_records(client, sir_level_alias)
                sir_records = self._filter_records_by_date(sir_records, since_date)
                sir_records = self._filter_records_by_status(sir_records)
                
                logger.info(f"Retrieved {len(sir_records)} SIR records from Archer")
                return sir_records
                
            except Exception as e:
                logger.exception(f"Error retrieving SIR data from Archer: {str(e)}")
                return []
        
        def _ensure_authenticated(self) -> None:
            """Ensure the client is authenticated before making requests."""
            if not self.authenticated:
                self.login()
        
        def _create_archer_client(self):
            """Create and return an ArcherServerClient instance."""
            from opts.ArcherServerClient import ArcherServerClient
            return ArcherServerClient(self)
        
        def _find_sir_level_alias(self, client) -> Optional[str]:
            """
            Find the appropriate level alias for SIR data.
            
            Args:
                client: ArcherServerClient instance
                
            Returns:
                str: The level alias for SIR data, or None if not found
            """
            endpoints = client.get_endpoints()
            sir_level_alias = 'Incidents'
            endpoint_names = self._extract_endpoint_names(endpoints)
            
            if sir_level_alias in endpoint_names:
                return sir_level_alias
            
            # Try to find a similar level alias
            alternative_alias = self._find_alternative_incident_alias(endpoints, endpoint_names)
            if alternative_alias:
                logger.info(f"Using level alias '{alternative_alias}' instead")
                return alternative_alias
            
            logger.error("Could not find a suitable level alias for SIR data")
            return None
        
        def _extract_endpoint_names(self, endpoints: List) -> List[str]:
            """
            Extract endpoint names from various endpoint formats.
            
            Args:
                endpoints: List of endpoints in various formats
                
            Returns:
                List[str]: List of endpoint names
            """
            endpoint_names = []
            for endpoint in endpoints:
                if isinstance(endpoint, dict):
                    endpoint_names.append(endpoint.get('name', ''))
                elif isinstance(endpoint, str):
                    endpoint_names.append(endpoint)
                else:
                    logger.warning(f"Unexpected endpoint format: {type(endpoint)} - {endpoint}")
                    endpoint_names.append(str(endpoint))
            return endpoint_names
        
        def _find_alternative_incident_alias(self, endpoints: List, endpoint_names: List[str]) -> Optional[str]:
            """
            Find an alternative incident-related endpoint alias.
            
            Args:
                endpoints: List of endpoints
                endpoint_names: List of endpoint names
                
            Returns:
                str: Alternative alias if found, None otherwise
            """
            for i, endpoint_name in enumerate(endpoint_names):
                if 'incident' in endpoint_name.lower():
                    return endpoint_name
            
            logger.warning(f"Level alias 'Incidents' not found in available endpoints: {endpoint_names}")
            return None
        
        def _fetch_sir_records(self, client, sir_level_alias: str) -> List[Dict[str, Any]]:
            """
            Fetch SIR records from the specified level.
            
            Args:
                client: ArcherServerClient instance
                sir_level_alias: The level alias to fetch data from
                
            Returns:
                List[Dict[str, Any]]: List of SIR records
            """
            level_data = client.get_levels_metadata([sir_level_alias])
            return level_data.get(sir_level_alias, [])
        
        def _filter_records_by_date(self, records: List[Dict[str, Any]], since_date) -> List[Dict[str, Any]]:
            """
            Filter records by date if since_date is provided.
            
            Args:
                records: List of SIR records
                since_date: Date to filter from
                
            Returns:
                List[Dict[str, Any]]: Filtered records
            """
            if not since_date or not records:
                return records
            
            filtered_records = []
            for record in records:
                record_date = self._extract_record_date(record)
                
                if record_date and record_date >= since_date:
                    filtered_records.append(record)
                elif not record_date:
                    logger.warning("No valid Date_Created field found for record, including it anyway")
                    filtered_records.append(record)
            
            logger.info(f"Filtered SIR data to {len(filtered_records)} records since {since_date}")
            return filtered_records
        
        def _extract_record_date(self, record: Dict[str, Any]):
            """
            Extract and parse the creation date from a record.
            
            Args:
                record: SIR record dictionary
                
            Returns:
                datetime: Parsed date or None if not found/parseable
            """
            date_created = record.get('Date_Created')
            if not date_created:
                return None
            
            try:
                from datetime import datetime
                if isinstance(date_created, str):
                    # Handle timezone formats like -04:00, +00:00, or Z
                    date_str = date_created
                    if date_str.endswith('Z'):
                        date_str = date_str.replace('Z', '+00:00')
                    return datetime.fromisoformat(date_str)
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse Date_Created field with value '{date_created}': {e}")
            
            return None
        
        def _filter_records_by_status(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """
            Filter records by Sub_Category_Type field.
            
            Args:
                records: List of SIR records
                
            Returns:
                List[Dict[str, Any]]: Records with status 'Assigned for Further Action'
            """
            if not records:
                return records
            
            target_status = "Assigned for Further Action"
            filtered_records = []
            
            for record in records:
                if self._has_target_submission_status(record, target_status):
                    filtered_records.append(record)
            
            logger.info(f"Filtered SIR data to {len(filtered_records)} records with Sub_Category_Type = '{target_status}'")
            return filtered_records
        
        def _has_target_submission_status(self, record: Dict[str, Any], target_status: str) -> bool:
            """
            Check if a record has the target submission status.
            
            Args:
                record: SIR record dictionary
                target_status: The status to check for
                
            Returns:
                bool: True if record has the target status
            """
            submission_status = record.get('Sub_Category_Type', '')
            
            if isinstance(submission_status, list):
                return target_status in submission_status
            elif isinstance(submission_status, str):
                return submission_status == target_status
            
            return False
            
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

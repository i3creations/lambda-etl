"""
Default Fields Module

This module defines default values for fields that don't have direct mappings
from OPTS to OPS Portal. These default values are used when creating new records
in the OPS Portal.
"""

# Dictionary of default field values for OPS Portal
default_fields = {
    'phase': 'Monitored',
    'dissemination': 'FOUO',
    'trafficLightProtocol': None,
    'authorizedBy': 'Command Center Group',
    'overview': None,
    'initialMedium': 'Government Database',
    'initialOfficialSource': 'USCIS',
    'initialMediaSource': 'Not Provided',
    'archivesOn': 'A-LAN',
    'impactedSectorList': None,
    'impactedSubSectorList': None,
    'intlThreatsIncidents': False,
    'terrorismRelated': False,
    'additionalReporting': None,
    'scheduledDate': None,
    'mediaReportDate': None,
    'officialReportDate': None,
    'tenantAbbreviation': 'USCIS',
    'publishDate': None,
    'openDate': None,
    'approvedBy': 'Command Center Group'
}


def get_default_fields():
    """
    Get the dictionary of default field values.
    
    Returns:
        dict: A dictionary of default field values for OPS Portal
    """
    return default_fields


def get_default_value(field_name):
    """
    Get the default value for a specific field.
    
    Args:
        field_name (str): The name of the field
        
    Returns:
        any: The default value for the field, or None if no default exists
    """
    return default_fields.get(field_name, None)

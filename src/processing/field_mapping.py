"""
Field Mapping Module

This module defines the mapping between OPTS field names and OPS Portal field names.
It provides a dictionary that maps source field names to target field names.
"""

# Dictionary mapping OPTS field names to OPS Portal field names
field_names = {
    'Incident_Id': 'Incident_ID',  # Add mapping for Incident_Id to Incident_ID
    'SIR_': 'tenantItemID',
    'Local_Date_Reported': 'openDate',
    'Facility_Address_HELPER': 'location',
    'Facility_Latitude': 'latitude',
    'Facility_Longitude': 'longitude',
    'Date_SIR_Processed__NT': 'swoDate',
    # Category mapping fields
    'type': 'type',
    'subtype': 'subtype', 
    'sharing': 'sharing',
    # Derived fields
    'title': 'title',
    'incidentReportDetails': 'incidentReportDetails'
}


def get_field_mapping():
    """
    Get the field mapping dictionary.
    
    Returns:
        dict: A dictionary mapping OPTS field names to OPS Portal field names
    """
    return field_names


def map_field_name(field_name):
    """
    Map an OPTS field name to its corresponding OPS Portal field name.
    
    Args:
        field_name (str): The OPTS field name to map
        
    Returns:
        str: The corresponding OPS Portal field name, or the original name if no mapping exists
    """
    return field_names.get(field_name, field_name)

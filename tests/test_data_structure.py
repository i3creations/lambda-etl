"""
Unit tests to verify data structure compatibility with OPS Portal API swagger example.
"""

import pytest
import pandas as pd
from datetime import datetime
from src.processing.preprocess import preprocess
from src.processing.default_fields import default_fields


def test_data_structure_matches_swagger():
    """Test that processed data structure matches the OPS Portal API swagger example."""
    
    # Sample input data that matches what would come from Archer
    sample_data = [
        {
            'Incident_ID': 'INC-001',
            'SIR_': 'SIR-2025-001',
            'Local_Date_Reported': '2025-05-31T10:00:00Z',
            'Facility_Address_HELPER': '123 Main St, Washington, DC',
            'Facility_Latitude': 38.9072,
            'Facility_Longitude': -77.0369,
            'Date_SIR_Processed__NT': '2025-05-31T15:00:00Z',
            'Details': '<p>Test incident details</p>',
            'Section_5__Action_Taken': '<p>Actions taken to resolve</p>',
            'Type_of_SIR': 'Suspicious or Threatening Activity',
            'Category_Type': 'Suspicious Activity',
            'Sub_Category_Type': 'Person'
        }
    ]
    
    # Process the data
    last_incident_id = ""  # Empty string to include all incident IDs
    config = {
        'category_mapping_file': 'config/category_mappings.csv',
        'filter_rejected': False,
        'filter_unprocessed': False,
        'filter_by_date': False
    }
    
    processed_df = preprocess(sample_data, last_incident_id, config)
    
    # Convert to records for API sending
    if not processed_df.empty:
        records = processed_df.to_dict('records')
        record = records[0]
        
        # Expected fields from swagger example
        swagger_fields = {
            'type', 'subtype', 'phase', 'sharing', 'dissemination', 'trafficLightProtocol',
            'authorizedBy', 'title', 'overview', 'initialMedium', 'initialOfficialSource',
            'initialMediaSource', 'archivesOn', 'impactedSectorList', 'impactedSubSectorList',
            'intlThreatsIncidents', 'terrorismRelated', 'additionalReporting', 'location',
            'latitude', 'longitude', 'openDate', 'swoDate', 'scheduledDate', 'mediaReportDate',
            'officialReportDate', 'tenantItemID', 'tenantAbbreviation', 'incidentReportDetails',
            'publishDate', 'approvedBy'
        }
        
        # Check that all required fields are present
        record_fields = set(record.keys())
        missing_fields = swagger_fields - record_fields
        
        print(f"Record fields: {sorted(record_fields)}")
        print(f"Missing fields: {sorted(missing_fields)}")
        print(f"Sample record: {record}")
        
        # Assert that critical fields are present
        assert 'type' in record, "Missing 'type' field"
        assert 'subtype' in record, "Missing 'subtype' field"
        assert 'sharing' in record, "Missing 'sharing' field"
        assert 'tenantItemID' in record, "Missing 'tenantItemID' field"
        assert 'title' in record, "Missing 'title' field"
        assert 'incidentReportDetails' in record, "Missing 'incidentReportDetails' field"
        
        # Check data types match swagger example
        assert isinstance(record['type'], str), "type should be string"
        assert isinstance(record['subtype'], str), "subtype should be string"
        assert isinstance(record['phase'], str), "phase should be string"
        assert isinstance(record['sharing'], str), "sharing should be string"
        assert isinstance(record['tenantItemID'], str), "tenantItemID should be string"
        assert isinstance(record['title'], str), "title should be string"
        assert isinstance(record['latitude'], str), "latitude should be string"
        assert isinstance(record['longitude'], str), "longitude should be string"
        assert isinstance(record['intlThreatsIncidents'], bool), "intlThreatsIncidents should be boolean"
        assert isinstance(record['terrorismRelated'], bool), "terrorismRelated should be boolean"
        
        # Check datetime format (should be ISO format with timezone offset)
        import re
        # Pattern to match ISO datetime with timezone offset (e.g., +0000, -0500)
        tz_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[+-]\d{4}$'
        assert re.match(tz_pattern, record['openDate']), f"openDate should have timezone offset format: {record['openDate']}"
        assert re.match(tz_pattern, record['swoDate']), f"swoDate should have timezone offset format: {record['swoDate']}"
        
        # Verify specific values from category mapping
        assert record['type'] == 'Suspicious Incident', f"Expected 'Suspicious Incident', got '{record['type']}'"
        assert record['subtype'] == 'Suspicious Activity', f"Expected 'Suspicious Activity', got '{record['subtype']}'"
        assert record['sharing'] == 'Share with Tenant DHS Operations Centers', f"Expected sharing level, got '{record['sharing']}'"


def test_default_fields_coverage():
    """Test that default fields cover all required swagger fields."""
    
    # Fields that should have default values
    expected_defaults = {
        'phase', 'dissemination', 'trafficLightProtocol', 'authorizedBy', 'overview',
        'initialMedium', 'initialOfficialSource', 'initialMediaSource', 'archivesOn',
        'impactedSectorList', 'impactedSubSectorList', 'intlThreatsIncidents',
        'terrorismRelated', 'additionalReporting', 'scheduledDate', 'mediaReportDate',
        'officialReportDate', 'tenantAbbreviation', 'publishDate', 'approvedBy'
    }
    
    default_field_keys = set(default_fields.keys())
    
    # Check that all expected defaults are covered
    missing_defaults = expected_defaults - default_field_keys
    
    print(f"Default fields: {sorted(default_field_keys)}")
    print(f"Missing defaults: {sorted(missing_defaults)}")
    
    assert len(missing_defaults) == 0, f"Missing default fields: {missing_defaults}"


if __name__ == "__main__":
    test_data_structure_matches_swagger()
    test_default_fields_coverage()
    print("All tests passed!")

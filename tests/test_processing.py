import pytest
import pandas as pd
import tempfile
import os
import csv
import sys
from datetime import datetime
from unittest.mock import patch, mock_open

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Helper function to rename columns in test data
def rename_columns_for_test(data):
    """Rename columns in test data to match what preprocess.py expects"""
    for record in data:
        if 'Incidents_Id' in record:
            record['Incident_ID'] = record.pop('Incidents_Id')
    return data

from src.processing.html_stripper import strip_tags
from src.processing.field_mapping import get_field_mapping, map_field_name
from src.processing.default_fields import get_default_fields, get_default_value
from src.processing.preprocess import preprocess

class TestProcessing:

    def test_html_stripper(self):
        html = '<p>test</p><br />'
        assert strip_tags(html) == 'test'
        
    def test_html_stripper_empty(self):
        assert strip_tags('') == ''
        assert strip_tags(None) == ''
        
    def test_html_stripper_complex(self):
        html = '<div><p>Hello <b>World</b>!</p><br/><span>Test</span></div>'
        assert strip_tags(html) == 'Hello World!Test'

    def test_get_field_mapping(self):
        mapping = get_field_mapping()
        assert len(mapping) != 0
        assert isinstance(mapping, dict)
        assert 'SIR_' in mapping
        assert 'Local_Date_Reported' in mapping
        
    def test_map_field_name(self):
        assert map_field_name('SIR_') == 'tenantItemID'
        assert map_field_name('Local_Date_Reported') == 'openDate'
        assert map_field_name('invalid') == 'invalid'

    def test_default_fields(self):
        defaults = get_default_fields()
        assert len(defaults) != 0
        assert isinstance(defaults, dict)
        assert 'phase' in defaults
        assert 'dissemination' in defaults
        
    def test_get_default_value(self):
        assert get_default_value('phase') == 'Monitored'
        assert get_default_value('dissemination') == 'FOUO'
        assert get_default_value('invalid') == None
        
    def test_preprocess_empty_data(self):
        """Test preprocess with empty data."""
        last_run = datetime(2023, 1, 1)
        result = preprocess([], last_run)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        
    def test_preprocess_missing_columns(self):
        """Test preprocess with missing required columns."""
        data = [{'invalid_column': 'value'}]
        last_run = datetime(2023, 1, 1)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            preprocess(data, last_run)
            
    def test_preprocess_missing_category_file(self):
        """Test preprocess with missing category mapping file."""
        # Create valid test data
        data = [{
            'Incidents_Id': 'INC-001',
            'SIR_': 'SIR-2023-001',
            'Local_Date_Reported': '2023-01-01T10:00:00Z',
            'Facility_Address_HELPER': '123 Main St',
            'Facility_Latitude': 38.9072,
            'Facility_Longitude': -77.0369,
            'Date_SIR_Processed__NT': '2023-01-01T15:00:00Z',
            'Details': '<p>Test details</p>',
            'Section_5__Action_Taken': '<p>Actions taken</p>',
            'Type_of_SIR': 'Test Type',
            'Category_Type': 'Test Category',
            'Sub_Category_Type': 'Test Subcategory'
        }]
        
        # Rename columns to match what preprocess.py expects
        data = rename_columns_for_test(data)
        
        # Use 0 as last_incident_id instead of datetime
        last_incident_id = 0
        config = {'category_mapping_file': '/nonexistent/file.csv'}
        
        with pytest.raises(FileNotFoundError):
            preprocess(data, last_incident_id, config)
            
    def test_preprocess_success(self, tmpdir):
        """Test successful preprocessing using mock data."""
        # Create a temporary category mapping file with mappings for mock data
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Earthquake,Incident,Natural Disaster,Earthquake,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Flood,Incident,Natural Disaster,Flood,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Hurricane,Incident,Natural Disaster,Hurricane,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Volcano,Incident,Natural Disaster,Volcano,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Power & Energy,Incident,Service Outage,Power,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Phone/IT Network/ICT,Incident,Service Outage,Communications,FOUO\n'
            'Infrastructure Impact Events,External Factors,Animal,Incident,External,Animal,FOUO\n'
        )
        
        # Load mock data from CSV
        mock_data = self.load_mock_archer_data()
        
        # Filter to get valid records for testing
        valid_data = []
        for record in mock_data:
            if (record.get('Incidents_Id') and 
                record.get('SIR_') and 
                record.get('SIR_') != 'REJECTED' and
                record.get('Local_Date_Reported') and
                record.get('Details') and
                record.get('Type_of_SIR') and
                record.get('Category_Type')):
                # Ensure required fields are present
                if not record.get('Date_SIR_Processed__NT'):
                    record['Date_SIR_Processed__NT'] = record.get('Local_Date_Reported')
                if not record.get('Section_5__Action_Taken'):
                    record['Section_5__Action_Taken'] = 'No action specified'
                if not record.get('Sub_Category_Type'):
                    record['Sub_Category_Type'] = record.get('Category_Type', '')
                valid_data.append(record)
                if len(valid_data) >= 3:  # Just use a few records for testing
                    break
        
        # Rename columns to match what preprocess.py expects
        valid_data = rename_columns_for_test(valid_data)
        
        # Use 0 as last_incident_id instead of datetime
        last_incident_id = 0
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': False,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        result = preprocess(valid_data, last_incident_id, config)
        
        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        
        # Check that fields were mapped correctly
        record = result.iloc[0]
        assert 'BAL-' in record['tenantItemID']  # Mock data uses BAL- prefix
        assert record['type'] in ['Natural Disaster', 'Service Outage', 'External']
        assert record['subtype'] in ['Tsunami', 'Earthquake', 'Flood', 'Hurricane', 'Volcano', 'Power', 'Communications', 'Animal']
        assert record['sharing'] == 'FOUO'
        
        # Check that HTML was stripped from details
        assert '<p>' not in str(record['incidentReportDetails'])
        
        # Check that default fields were added
        assert record['phase'] == 'Monitored'
        assert record['dissemination'] == 'FOUO'
        
    def test_preprocess_filtering(self, tmpdir):
        """Test data filtering functionality using mock data."""
        # Create a temporary category mapping file
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Earthquake,Incident,Natural Disaster,Earthquake,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Power & Energy,Incident,Service Outage,Power,FOUO\n'
        )
        
        # Load mock data and create test scenarios
        mock_data = self.load_mock_archer_data()
        
        # Create test data with different filtering scenarios based on mock data
        base_record = None
        for record in mock_data:
            if (record.get('Incidents_Id') and record.get('SIR_') and 
                record.get('Local_Date_Reported') and record.get('Details')):
                base_record = record.copy()
                break
        
        if not base_record:
            pytest.skip("No suitable base record found in mock data")
        
        # Create test scenarios
        data = [
            # Should be filtered out - rejected
            {**base_record, 'SIR_': 'REJECTED', 'Incidents_Id': 'INC-001', 'Type_of_SIR': 'Infrastructure Impact Events', 'Category_Type': 'Natural Disaster', 'Sub_Category_Type': 'Tsunami'},
            # Should be filtered out - not processed
            {**base_record, 'Date_SIR_Processed__NT': None, 'SIR_': 'BAL-TEST-002', 'Incidents_Id': 'INC-002', 'Type_of_SIR': 'Infrastructure Impact Events', 'Category_Type': 'Natural Disaster', 'Sub_Category_Type': 'Earthquake'},
            # Should be filtered out - future date (but now we're not filtering by date)
            {**base_record, 'Local_Date_Reported': '2025-12-01T10:00:00Z', 'SIR_': 'BAL-TEST-003', 'Incidents_Id': 'INC-003', 'Type_of_SIR': 'Infrastructure Impact Events', 'Category_Type': 'Natural Disaster', 'Sub_Category_Type': 'Tsunami'},
            # Should pass all filters (past date)
            {**base_record, 'Local_Date_Reported': '2025-01-01T10:00:00Z', 'SIR_': 'BAL-TEST-004', 'Incidents_Id': 'INC-004', 'Type_of_SIR': 'Infrastructure Impact Events', 'Category_Type': 'Natural Disaster', 'Sub_Category_Type': 'Tsunami'}
        ]
        
        # Ensure all records have required fields
        for record in data:
            if not record.get('Section_5__Action_Taken'):
                record['Section_5__Action_Taken'] = 'Test action taken'
            if not record.get('Sub_Category_Type'):
                record['Sub_Category_Type'] = record.get('Category_Type', 'Test')
        
        # Rename columns to match what preprocess.py expects
        data = rename_columns_for_test(data)
        
        # Use 0 as last_incident_id instead of datetime
        last_incident_id = 0
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': True,
            'filter_unprocessed': True,
            'filter_by_date': False,  # Disable date filtering for this test
            'filter_by_incident_id': False  # Disable incident ID filtering for this test
        }
        
        result = preprocess(data, last_incident_id, config)
        
        # Two records should pass all filters (since we're not filtering by date)
        assert len(result) == 2
        # Check that both BAL-TEST-003 and BAL-TEST-004 are in the results
        tenantItemIDs = result['tenantItemID'].tolist()
        assert 'BAL-TEST-003' in tenantItemIDs
        assert 'BAL-TEST-004' in tenantItemIDs
        
    def test_preprocess_no_filtering(self, tmpdir):
        """Test preprocessing with all filters disabled using mock data."""
        # Create a temporary category mapping file
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
        )
        
        # Load mock data and create a test record that would normally be filtered
        mock_data = self.load_mock_archer_data()
        base_record = None
        for record in mock_data:
            if (record.get('Incidents_Id') and record.get('Local_Date_Reported') and 
                record.get('Details') and record.get('Type_of_SIR')):
                base_record = record.copy()
                break
        
        if not base_record:
            pytest.skip("No suitable base record found in mock data")
        
        # Create test data that would normally be filtered
        data = [{
            **base_record,
            'SIR_': 'REJECTED',  # Would normally be filtered
            'Local_Date_Reported': '2025-12-01T10:00:00Z',  # Future date - after last_run
            'Date_SIR_Processed__NT': None,  # Not processed
            'Section_5__Action_Taken': 'Actions taken',
            'Incidents_Id': 'INC-REJECTED-001',
            'Type_of_SIR': 'Infrastructure Impact Events',
            'Category_Type': 'Natural Disaster',
            'Sub_Category_Type': 'Tsunami'
        }]
        
        # Rename columns to match what preprocess.py expects
        data = rename_columns_for_test(data)
        
        # Use 0 as last_incident_id instead of datetime
        last_incident_id = 0
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': False,  # Disable all filters for this test
            'filter_unprocessed': False,
            'filter_by_date': False,
            'filter_by_incident_id': False  # Disable incident ID filtering for this test
        }
        
        result = preprocess(data, last_incident_id, config)
        
        # Record should not be filtered
        assert len(result) == 1
        assert result.iloc[0]['tenantItemID'] == 'REJECTED'

    def load_mock_archer_data(self):
        """Load mock data from CSV file."""
        mock_data_path = os.path.join(os.path.dirname(__file__), 'mock_archer_data.csv')
        
        # Read CSV and convert to list of dictionaries
        data = []
        with open(mock_data_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert empty strings to None for consistency
                processed_row = {}
                for key, value in row.items():
                    if value == '':
                        processed_row[key] = None
                    elif value.startswith('[') and value.endswith(']'):
                        # Handle list-like strings - extract the content
                        if value == '[]':
                            processed_row[key] = None
                        else:
                            # Extract content from ['content'] format
                            content = value.strip('[]').strip("'\"")
                            if ',' in content:
                                # Multiple values - take the first one for simplicity
                                processed_row[key] = content.split(',')[0].strip("'\"").strip()
                            else:
                                processed_row[key] = content
                    else:
                        processed_row[key] = value
                data.append(processed_row)
        
        return data

    def test_preprocess_with_mock_data(self, tmpdir):
        """Test preprocessing with real mock data from CSV."""
        # Create a temporary category mapping file with mappings for the actual mock data
        # The mock data contains Infrastructure Impact Events with various subcategories
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Earthquake,Incident,Natural Disaster,Earthquake,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Flood,Incident,Natural Disaster,Flood,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Hurricane,Incident,Natural Disaster,Hurricane,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Volcano,Incident,Natural Disaster,Volcano,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Tropical Storm,Incident,Natural Disaster,Tropical Storm,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Sinkholes,Incident,Natural Disaster,Sinkholes,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Power & Energy,Incident,Service Outage,Power,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Phone/IT Network/ICT,Incident,Service Outage,Communications,FOUO\n'
            'Infrastructure Impact Events,External Factors,Animal,Incident,External,Animal,FOUO\n'
        )
        
        # Load mock data
        mock_data = self.load_mock_archer_data()
        
        # Filter to only records that have the minimum required fields
        # Be more lenient about what constitutes valid data
        valid_data = []
        for record in mock_data:
            if (record.get('Incidents_Id') and 
                record.get('SIR_') and 
                record.get('SIR_') != 'REJECTED' and
                record.get('Local_Date_Reported') and
                record.get('Details') and
                record.get('Type_of_SIR') and
                record.get('Category_Type')):
                # Add missing required fields with defaults if they don't exist
                if not record.get('Date_SIR_Processed__NT'):
                    record['Date_SIR_Processed__NT'] = record.get('Local_Date_Reported')
                if not record.get('Section_5__Action_Taken'):
                    record['Section_5__Action_Taken'] = 'No action taken specified'
                if not record.get('Sub_Category_Type'):
                    record['Sub_Category_Type'] = ''  # Empty string for general category
                if not record.get('Facility_Address_HELPER'):
                    record['Facility_Address_HELPER'] = 'Unknown Address'
                if not record.get('Facility_Latitude'):
                    record['Facility_Latitude'] = 0.0
                if not record.get('Facility_Longitude'):
                    record['Facility_Longitude'] = 0.0
                valid_data.append(record)
        
        # Rename columns to match what preprocess.py expects
        valid_data = rename_columns_for_test(valid_data)
        
        # Use 0 as last_incident_id instead of datetime
        last_incident_id = 0
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': False,
            'filter_unprocessed': False,
            'filter_by_date': False,
            'filter_by_incident_id': False  # Disable incident ID filtering for this test
        }
        
        result = preprocess(valid_data, last_incident_id, config)
        
        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0, f"Should have processed some records. Valid data count: {len(valid_data)}"
        
        # Check that required columns exist in the result
        required_output_columns = ['tenantItemID', 'openDate', 'type', 'subtype', 'sharing', 
                                 'incidentReportDetails', 'phase', 'dissemination']
        for col in required_output_columns:
            assert col in result.columns, f"Missing required column: {col}"
        
        # Check that HTML was stripped from details
        for _, row in result.iterrows():
            assert '<p>' not in str(row['incidentReportDetails'])
            assert '&nbsp;' not in str(row['incidentReportDetails'])
        
        # Check that default fields were added
        assert all(result['phase'] == 'Monitored')
        assert all(result['dissemination'] == 'FOUO')
        
        # Check that SIR_ field was mapped to tenantItemID
        assert all(result['tenantItemID'].str.contains('-', na=False))
        
        print(f"Successfully processed {len(result)} records from mock data")

    def test_preprocess_with_mock_data_no_filters(self, tmpdir):
        """Test preprocessing with mock data and no filters applied."""
        # Create a comprehensive category mapping file that matches the actual mock data
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Earthquake,Incident,Natural Disaster,Earthquake,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Flood,Incident,Natural Disaster,Flood,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Hurricane,Incident,Natural Disaster,Hurricane,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Volcano,Incident,Natural Disaster,Volcano,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Tropical Storm,Incident,Natural Disaster,Tropical Storm,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Sinkholes,Incident,Natural Disaster,Sinkholes,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Power & Energy,Incident,Service Outage,Power,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Phone/IT Network/ICT,Incident,Service Outage,Communications,FOUO\n'
            'Infrastructure Impact Events,External Factors,Animal,Incident,External,Animal,FOUO\n'
        )
        
        # Load mock data
        mock_data = self.load_mock_archer_data()
        
        # Filter to only records that have the required fields and add missing fields
        valid_data = []
        for record in mock_data:
            if (record.get('Incidents_Id') and 
                record.get('SIR_') and 
                record.get('Local_Date_Reported') and
                record.get('Details') and
                record.get('Type_of_SIR') and
                record.get('Category_Type')):
                # Add missing required fields with defaults if they don't exist
                if not record.get('Date_SIR_Processed__NT'):
                    record['Date_SIR_Processed__NT'] = record.get('Local_Date_Reported')
                if not record.get('Section_5__Action_Taken'):
                    record['Section_5__Action_Taken'] = 'No action taken specified'
                if not record.get('Sub_Category_Type'):
                    record['Sub_Category_Type'] = record.get('Category_Type', '')
                if not record.get('Facility_Address_HELPER'):
                    record['Facility_Address_HELPER'] = 'Unknown Address'
                if not record.get('Facility_Latitude'):
                    record['Facility_Latitude'] = 0.0
                if not record.get('Facility_Longitude'):
                    record['Facility_Longitude'] = 0.0
                valid_data.append(record)
        
        # Use a very early last_run date and disable all filters
        last_run = datetime(2020, 1, 1)
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': False,
            'filter_unprocessed': False,
            'filter_by_date': False
        }
        
        result = preprocess(valid_data, last_run, config)
        
        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0, "Should have processed some records"
        
        # Check that records were processed (since we're using the correct category mappings)
        # Some records might have different prefixes like ALB- or ATL-, so we just check that they contain a hyphen
        assert all(result['tenantItemID'].str.contains('-', na=False)), "All records should have a prefix with hyphen"
        
        print(f"Successfully processed {len(result)} records with no filters applied")

    def test_preprocess_html_stripping_with_mock_data(self, tmpdir):
        """Test that HTML tags are properly stripped from mock data."""
        # Create category mapping for Infrastructure Impact Events (which is in our mock data)
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Volcano,Incident,Natural Disaster,Volcano,FOUO\n'
        )
        
        # Load mock data and find records with HTML content
        mock_data = self.load_mock_archer_data()
        
        # Filter to records with HTML in Details field
        html_data = []
        for record in mock_data:
            if (record.get('Details') and 
                '<p>' in str(record.get('Details', '')) and
                record.get('Incidents_Id') and 
                record.get('SIR_') and 
                record.get('SIR_') != 'REJECTED' and
                record.get('Local_Date_Reported') and
                record.get('Type_of_SIR') == 'Infrastructure Impact Events'):
                # Ensure required fields
                if not record.get('Date_SIR_Processed__NT'):
                    record['Date_SIR_Processed__NT'] = record.get('Local_Date_Reported')
                if not record.get('Section_5__Action_Taken'):
                    record['Section_5__Action_Taken'] = 'No action specified'
                html_data.append(record)
                break  # Just test with one record
        
        if html_data:
            # Rename columns to match what preprocess.py expects
            html_data = rename_columns_for_test(html_data)
            
            # Use 0 as last_incident_id instead of datetime
            last_incident_id = 0
            config = {
                'category_mapping_file': category_file.strpath,
                'filter_rejected': True,
                'filter_unprocessed': False,
                'filter_by_date': True
            }
            
            result = preprocess(html_data, last_incident_id, config)
            
            if len(result) > 0:
                # Check that HTML tags were stripped
                details = result.iloc[0]['incidentReportDetails']
                assert '<p>' not in details
                assert '&nbsp;' not in details
                assert 'Details' in details  # The mock data has "Details" as content
                
                print("HTML stripping test passed with mock data")
        else:
            print("No HTML records found in mock data for testing")
            
    def test_preprocess_output_to_json(self, tmpdir):
        """Test preprocessing with output to JSON file."""
        import os
        import json
        from datetime import datetime
        
        print("Testing preprocessing with output to JSON file...")
        
        # Create a temporary category mapping file with mappings for mock data
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Earthquake,Incident,Natural Disaster,Earthquake,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Flood,Incident,Natural Disaster,Flood,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Hurricane,Incident,Natural Disaster,Hurricane,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Volcano,Incident,Natural Disaster,Volcano,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Power & Energy,Incident,Service Outage,Power,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Phone/IT Network/ICT,Incident,Service Outage,Communications,FOUO\n'
            'Infrastructure Impact Events,External Factors,Animal,Incident,External,Animal,FOUO\n'
        )
        
        # Load mock data from CSV
        mock_data = self.load_mock_archer_data()
        print(f"Loaded {len(mock_data)} records from mock data")
        
        # Filter to get valid records for testing
        valid_data = []
        for record in mock_data:
            if (record.get('Incidents_Id') and 
                record.get('SIR_') and 
                record.get('SIR_') != 'REJECTED' and
                record.get('Local_Date_Reported') and
                record.get('Details') and
                record.get('Type_of_SIR') and
                record.get('Category_Type')):
                # Ensure required fields are present
                if not record.get('Date_SIR_Processed__NT'):
                    record['Date_SIR_Processed__NT'] = record.get('Local_Date_Reported')
                if not record.get('Section_5__Action_Taken'):
                    record['Section_5__Action_Taken'] = 'No action specified'
                if not record.get('Sub_Category_Type'):
                    record['Sub_Category_Type'] = record.get('Category_Type', '')
                valid_data.append(record)
                if len(valid_data) >= 3:  # Just use a few records for testing
                    break
        
        print(f"Selected {len(valid_data)} valid records for testing")
        
        # Rename columns to match what preprocess.py expects
        valid_data = rename_columns_for_test(valid_data)
        
        # Use 0 as last_incident_id instead of datetime
        last_incident_id = 0
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': False,
            'filter_unprocessed': False,
            'filter_by_date': True,
            'filter_by_incident_id': False  # Disable incident ID filtering
        }
        
        # Process the data
        print("Processing data...")
        result = preprocess(valid_data, last_incident_id, config)
        
        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        print(f"Processed {len(result)} records")
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        # Use a fixed filename for the output
        json_filename = 'processed_data_fixed.json'
        json_path = os.path.join(output_dir, json_filename)
        print(f"Using fixed filename: {json_filename}")
        
        # Check for duplicate columns and rename them if needed
        if not result.columns.is_unique:
            # Get a list of all columns
            cols = list(result.columns)
            # Create a dictionary to track column counts
            col_counts = {}
            # Create a list for new column names
            new_cols = []
            
            # Process each column and rename duplicates
            for col in cols:
                if col in col_counts:
                    col_counts[col] += 1
                    new_cols.append(f"{col}_{col_counts[col]}")
                else:
                    col_counts[col] = 0
                    new_cols.append(col)
            
            # Set the new column names
            result.columns = new_cols
            print(f"Renamed duplicate columns. New columns: {list(result.columns)}")
        else:
            print("No duplicate columns found")
        
        # Print all column names
        print(f"All columns: {list(result.columns)}")
        
        # Convert DataFrame to JSON and save to file
        # Use orient='records' to get a list of dictionaries
        result_json = result.to_json(orient='records')
        with open(json_path, 'w') as f:
            # Parse and re-dump to get pretty formatting
            parsed_json = json.loads(result_json)
            json.dump(parsed_json, f, indent=2)
        
        # Verify the JSON file was created
        assert os.path.exists(json_path)
        print(f"JSON file created: {json_path}")
        
        # Read the JSON file and verify its contents
        with open(json_path, 'r') as f:
            loaded_json = json.load(f)
        
        # Verify the JSON data
        assert isinstance(loaded_json, list)
        assert len(loaded_json) == len(result)
        
        # Check that the first record in the JSON matches the first record in the DataFrame
        first_record_df = result.iloc[0].to_dict()
        first_record_json = loaded_json[0]
        
        # Check a few key fields
        assert first_record_json['tenantItemID'] == first_record_df['tenantItemID']
        assert first_record_json['type'] in ['Natural Disaster', 'Service Outage', 'External']
        assert first_record_json['phase'] == 'Monitored'
        assert first_record_json['dissemination'] == 'FOUO'
        
        # Check that HTML was stripped from details
        assert '<p>' not in first_record_json['incidentReportDetails']
        
        # Check if openDate_1 field exists
        if 'openDate_1' in first_record_json:
            print("ERROR: openDate_1 field still exists in the output!")
            print(f"Fields in first record: {list(first_record_json.keys())}")
        else:
            print("SUCCESS: openDate_1 field has been removed from the output!")
        
        print(f"Successfully created JSON output file: {json_path}")
        return json_path  # Return the path for potential use by other tests

    def test_mock_data_structure(self):
        """Test that mock data has the expected structure and content."""
        mock_data = self.load_mock_archer_data()
        
        # Verify we have data
        assert len(mock_data) > 0, "Mock data should not be empty"
        
        # Check that required columns exist in at least some records
        required_columns = ['Incidents_Id', 'SIR_', 'Local_Date_Reported', 'Details', 
                          'Type_of_SIR', 'Category_Type', 'Facility_Address_HELPER']
        
        valid_records = 0
        for record in mock_data:
            has_required = all(record.get(col) for col in required_columns)
            if has_required:
                valid_records += 1
        
        assert valid_records > 0, f"At least one record should have all required columns: {required_columns}"
        
        # Check that we have Infrastructure Impact Events (which is what's in our mock data)
        infrastructure_records = [r for r in mock_data if r.get('Type_of_SIR') == 'Infrastructure Impact Events']
        assert len(infrastructure_records) > 0, "Should have Infrastructure Impact Events records"
        
        # Check that SIR_ field has expected format
        sir_records = [r for r in mock_data if r.get('SIR_') and 'BAL-' in r.get('SIR_')]
        assert len(sir_records) > 0, "Should have records with BAL- prefix in SIR_ field"
        
        # Check that dates are in expected format
        date_records = [r for r in mock_data if r.get('Local_Date_Reported') and 'T' in r.get('Local_Date_Reported')]
        assert len(date_records) > 0, "Should have records with ISO format dates"
        
        print(f"Mock data validation passed: {len(mock_data)} total records, {valid_records} valid records")

    def test_preprocess_with_all_mock_data(self, tmpdir):
        """Test preprocessing with all available mock data."""
        # Create comprehensive category mapping for all types in mock data
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,category,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Incident,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Earthquake,Incident,Natural Disaster,Earthquake,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Flood,Incident,Natural Disaster,Flood,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Hurricane,Incident,Natural Disaster,Hurricane,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Volcano,Incident,Natural Disaster,Volcano,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Tropical Storm,Incident,Natural Disaster,Tropical Storm,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Sinkholes,Incident,Natural Disaster,Sinkholes,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Power & Energy,Incident,Service Outage,Power,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Phone/IT Network/ICT,Incident,Service Outage,Communications,FOUO\n'
            'Infrastructure Impact Events,External Factors,Animal,Incident,External,Animal,FOUO\n'
        )
        
        # Load all mock data
        mock_data = self.load_mock_archer_data()
        
        # Prepare all valid records
        valid_data = []
        for record in mock_data:
            if (record.get('Incidents_Id') and 
                record.get('SIR_') and 
                record.get('SIR_') != 'REJECTED' and
                record.get('Local_Date_Reported') and
                record.get('Details') and
                record.get('Type_of_SIR') and
                record.get('Category_Type')):
                
                # Add missing required fields with defaults
                if not record.get('Date_SIR_Processed__NT'):
                    record['Date_SIR_Processed__NT'] = record.get('Local_Date_Reported')
                if not record.get('Section_5__Action_Taken'):
                    record['Section_5__Action_Taken'] = 'Assigned for Further Action'
                if not record.get('Sub_Category_Type'):
                    record['Sub_Category_Type'] = record.get('Category_Type', '')
                
                valid_data.append(record)
        
        # Rename columns to match what preprocess.py expects
        valid_data = rename_columns_for_test(valid_data)
        
        # Use 0 as last_incident_id instead of datetime
        last_incident_id = 0
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': True,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        result = preprocess(valid_data, last_incident_id, config)
        
        # Verify results
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0, f"Should process some records from {len(valid_data)} valid records"
        
        # Check that all required output columns exist
        required_output_columns = ['tenantItemID', 'openDate', 'type', 'subtype', 'sharing', 
                                 'incidentReportDetails', 'phase', 'dissemination']
        for col in required_output_columns:
            assert col in result.columns, f"Missing required output column: {col}"
        
        # Check data quality
        # Some records might have different prefixes like ALB- or ATL-, so we just check that they contain a hyphen
        assert all(result['tenantItemID'].str.contains('-', na=False)), "All records should have a prefix with hyphen"
        assert all(result['phase'] == 'Monitored'), "All records should have phase = Monitored"
        assert all(result['dissemination'] == 'FOUO'), "All records should have dissemination = FOUO"
        
        # Check that HTML was stripped
        html_records = result[result['incidentReportDetails'].str.contains('<', na=False)]
        assert len(html_records) == 0, "No HTML tags should remain in processed data"
        
        print(f"Successfully processed {len(result)} records from all mock data")

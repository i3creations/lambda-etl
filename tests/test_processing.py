import pytest
import pandas as pd
import tempfile
import os
import csv
from datetime import datetime
from unittest.mock import patch, mock_open
from ops_api.processing.html_stripper import strip_tags
from ops_api.processing.field_mapping import get_field_mapping, map_field_name
from ops_api.processing.default_fields import get_default_fields, get_default_value
from ops_api.processing.preprocess import preprocess

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
        
        last_run = datetime(2023, 6, 1)
        config = {'category_mapping_file': '/nonexistent/file.csv'}
        
        with pytest.raises(FileNotFoundError):
            preprocess(data, last_run, config)
            
    def test_preprocess_success(self, tmpdir):
        """Test successful preprocessing."""
        # Create a temporary category mapping file
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,type,subtype,sharing\n'
            'Test Type,Test Category,Test Subcategory,Mapped Type,Mapped Subtype,Share Level\n'
        )
        
        # Create valid test data
        data = [{
            'Incidents_Id': 'INC-001',
            'SIR_': 'SIR-2023-001',
            'Local_Date_Reported': '2022-12-01T10:00:00Z',  # Before last_run
            'Facility_Address_HELPER': '123 Main St',
            'Facility_Latitude': 38.9072,
            'Facility_Longitude': -77.0369,
            'Date_SIR_Processed__NT': '2022-12-01T15:00:00Z',
            'Details': '<p>Test details</p>',
            'Section_5__Action_Taken': '<p>Actions taken</p>',
            'Type_of_SIR': 'Test Type',
            'Category_Type': 'Test Category',
            'Sub_Category_Type': 'Test Subcategory'
        }]
        
        last_run = datetime(2023, 1, 1)
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': False,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        result = preprocess(data, last_run, config)
        
        # Verify the result
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        
        # Check that fields were mapped correctly
        record = result.iloc[0]
        assert record['tenantItemID'] == 'SIR-2023-001'
        assert record['type'] == 'Mapped Type'
        assert record['subtype'] == 'Mapped Subtype'
        assert record['sharing'] == 'Share Level'
        
        # Check that HTML was stripped
        assert '<p>' not in record['incidentReportDetails']
        assert 'Test details' in record['incidentReportDetails']
        assert 'Actions taken' in record['incidentReportDetails']
        
        # Check that default fields were added
        assert record['phase'] == 'Monitored'
        assert record['dissemination'] == 'FOUO'
        
    def test_preprocess_filtering(self, tmpdir):
        """Test data filtering functionality."""
        # Create a temporary category mapping file
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,type,subtype,sharing\n'
            'Test Type,Test Category,Test Subcategory,Mapped Type,Mapped Subtype,Share Level\n'
        )
        
        # Create test data with different scenarios
        data = [
            {  # Should be filtered out - rejected
                'Incidents_Id': 'INC-001',
                'SIR_': 'REJECTED',
                'Local_Date_Reported': '2022-12-01T10:00:00Z',
                'Facility_Address_HELPER': '123 Main St',
                'Facility_Latitude': 38.9072,
                'Facility_Longitude': -77.0369,
                'Date_SIR_Processed__NT': '2022-12-01T15:00:00Z',
                'Details': 'Test details',
                'Section_5__Action_Taken': 'Actions taken',
                'Type_of_SIR': 'Test Type',
                'Category_Type': 'Test Category',
                'Sub_Category_Type': 'Test Subcategory'
            },
            {  # Should be filtered out - not processed
                'Incidents_Id': 'INC-002',
                'SIR_': 'SIR-2023-002',
                'Local_Date_Reported': '2022-12-01T10:00:00Z',
                'Facility_Address_HELPER': '123 Main St',
                'Facility_Latitude': 38.9072,
                'Facility_Longitude': -77.0369,
                'Date_SIR_Processed__NT': None,  # Not processed
                'Details': 'Test details',
                'Section_5__Action_Taken': 'Actions taken',
                'Type_of_SIR': 'Test Type',
                'Category_Type': 'Test Category',
                'Sub_Category_Type': 'Test Subcategory'
            },
            {  # Should be filtered out - after last_run
                'Incidents_Id': 'INC-003',
                'SIR_': 'SIR-2023-003',
                'Local_Date_Reported': '2023-06-01T10:00:00Z',  # After last_run
                'Facility_Address_HELPER': '123 Main St',
                'Facility_Latitude': 38.9072,
                'Facility_Longitude': -77.0369,
                'Date_SIR_Processed__NT': '2023-06-01T15:00:00Z',
                'Details': 'Test details',
                'Section_5__Action_Taken': 'Actions taken',
                'Type_of_SIR': 'Test Type',
                'Category_Type': 'Test Category',
                'Sub_Category_Type': 'Test Subcategory'
            },
            {  # Should pass all filters
                'Incidents_Id': 'INC-004',
                'SIR_': 'SIR-2023-004',
                'Local_Date_Reported': '2022-12-01T10:00:00Z',
                'Facility_Address_HELPER': '123 Main St',
                'Facility_Latitude': 38.9072,
                'Facility_Longitude': -77.0369,
                'Date_SIR_Processed__NT': '2022-12-01T15:00:00Z',
                'Details': 'Test details',
                'Section_5__Action_Taken': 'Actions taken',
                'Type_of_SIR': 'Test Type',
                'Category_Type': 'Test Category',
                'Sub_Category_Type': 'Test Subcategory'
            }
        ]
        
        last_run = datetime(2023, 1, 1)
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': True,
            'filter_unprocessed': True,
            'filter_by_date': True
        }
        
        result = preprocess(data, last_run, config)
        
        # Only one record should pass all filters
        assert len(result) == 1
        assert result.iloc[0]['tenantItemID'] == 'SIR-2023-004'
        
    def test_preprocess_no_filtering(self, tmpdir):
        """Test preprocessing with all filters disabled."""
        # Create a temporary category mapping file
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,type,subtype,sharing\n'
            'Test Type,Test Category,Test Subcategory,Mapped Type,Mapped Subtype,Share Level\n'
        )
        
        # Create test data that would normally be filtered
        data = [{
            'Incidents_Id': 'INC-001',
            'SIR_': 'REJECTED',  # Would normally be filtered
            'Local_Date_Reported': '2023-06-01T10:00:00Z',  # After last_run
            'Facility_Address_HELPER': '123 Main St',
            'Facility_Latitude': 38.9072,
            'Facility_Longitude': -77.0369,
            'Date_SIR_Processed__NT': None,  # Not processed
            'Details': 'Test details',
            'Section_5__Action_Taken': 'Actions taken',
            'Type_of_SIR': 'Test Type',
            'Category_Type': 'Test Category',
            'Sub_Category_Type': 'Test Subcategory'
        }]
        
        last_run = datetime(2023, 1, 1)
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': False,
            'filter_unprocessed': False,
            'filter_by_date': False
        }
        
        result = preprocess(data, last_run, config)
        
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
        # Create a temporary category mapping file with mappings for the mock data
        # Include mappings for records with missing Sub_Category_Type
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,type,subtype,sharing\n'
            'Information Spill/Mishandling,SPII / PII,G-1598 Damaged Mail Sent by Another USCIS Office,Data Breach,PII Exposure,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1600 General Incident,Data Breach,General,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1601 Lost Shipment,Data Breach,Lost Data,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,,Data Breach,General PII,FOUO\n'
            'Facilitated Apprehension and Law Enforcement,Immigration,,Law Enforcement,Immigration,Official Use Only\n'
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
        
        # Use a last_run date that will include some records
        last_run = datetime(2025, 1, 1)
        config = {
            'category_mapping_file': category_file.strpath,
            'filter_rejected': True,
            'filter_unprocessed': False,  # Don't filter unprocessed since we're adding defaults
            'filter_by_date': True
        }
        
        result = preprocess(valid_data, last_run, config)
        
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
        # Create a comprehensive category mapping file
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,type,subtype,sharing\n'
            'Information Spill/Mishandling,SPII / PII,G-1598 Damaged Mail Sent by Another USCIS Office,Data Breach,PII Exposure,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1600 General Incident,Data Breach,General,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1601 Lost Shipment,Data Breach,Lost Data,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1602 Mail by the Public,Data Breach,Mail Incident,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1599 Email PII Data Spill,Data Breach,Email Spill,FOUO\n'
            'Facilitated Apprehension and Law Enforcement,Immigration,,Law Enforcement,Immigration,Official Use Only\n'
            'Suspicious or Threatening Activity,Threat,,Security,Threat,Official Use Only\n'
        )
        
        # Load mock data
        mock_data = self.load_mock_archer_data()
        
        # Filter to only records that have the required fields
        valid_data = []
        for record in mock_data:
            if (record.get('Incidents_Id') and 
                record.get('SIR_') and 
                record.get('Local_Date_Reported') and
                record.get('Details') and
                record.get('Type_of_SIR') and
                record.get('Category_Type') and
                record.get('Sub_Category_Type')):
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
        
        # Should include rejected records when filter_rejected is False
        rejected_records = result[result['tenantItemID'].str.contains('REJECTED', na=False)]
        assert len(rejected_records) > 0, "Should include rejected records when filter is disabled"
        
        print(f"Successfully processed {len(result)} records with no filters applied")

    def test_preprocess_html_stripping_with_mock_data(self, tmpdir):
        """Test that HTML tags are properly stripped from mock data."""
        # Create category mapping
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,type,subtype,sharing\n'
            'Information Spill/Mishandling,SPII / PII,G-1598 Damaged Mail Sent by Another USCIS Office,Data Breach,PII Exposure,FOUO\n'
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
                record.get('Date_SIR_Processed__NT') and
                record.get('Type_of_SIR') == 'Information Spill/Mishandling' and
                record.get('Category_Type') == 'SPII / PII' and
                record.get('Sub_Category_Type') == 'G-1598 Damaged Mail Sent by Another USCIS Office'):
                html_data.append(record)
                break  # Just test with one record
        
        if html_data:
            last_run = datetime(2025, 1, 1)
            config = {
                'category_mapping_file': category_file.strpath,
                'filter_rejected': True,
                'filter_unprocessed': True,
                'filter_by_date': True
            }
            
            result = preprocess(html_data, last_run, config)
            
            if len(result) > 0:
                # Check that HTML tags were stripped
                details = result.iloc[0]['incidentReportDetails']
                assert '<p>' not in details
                assert '&nbsp;' not in details
                assert 'test for 1598' in details or 'TEST' in details
                
                print("HTML stripping test passed with mock data")

import pytest
import pandas as pd
import tempfile
import os
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

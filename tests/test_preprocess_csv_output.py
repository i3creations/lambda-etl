"""
Test for preprocess.py that outputs preprocessed data as CSV file.

This test validates the preprocessing functionality and saves the output
to a CSV file in the tests/output folder for inspection and validation.
"""

import pytest
import pandas as pd
import os
import csv
from datetime import datetime, timezone
from pathlib import Path
from src.processing.preprocess import preprocess


class TestPreprocessCSVOutput:
    """Test class for preprocessing with CSV output functionality."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Ensure output directory exists
        self.output_dir = Path("tests/output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for unique filenames
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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

    def create_category_mapping_file(self, tmpdir):
        """Create a comprehensive category mapping file for testing."""
        category_file = tmpdir.join('category_mappings.csv')
        category_file.write(
            'Type_of_SIR,Category_Type,Sub_Category_Type,type,subtype,sharing\n'
            'Infrastructure Impact Events,Natural Disaster,Tsunami,Natural Disaster,Tsunami,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Earthquake,Natural Disaster,Earthquake,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Flood,Natural Disaster,Flood,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Hurricane,Natural Disaster,Hurricane,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Volcano,Natural Disaster,Volcano,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Tropical Storm,Natural Disaster,Tropical Storm,FOUO\n'
            'Infrastructure Impact Events,Natural Disaster,Sinkholes,Natural Disaster,Sinkholes,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Power & Energy,Service Outage,Power,FOUO\n'
            'Infrastructure Impact Events,Loss of Essential Services,Phone/IT Network/ICT,Service Outage,Communications,FOUO\n'
            'Infrastructure Impact Events,External Factors,Animal,External,Animal,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1598 Damaged Mail Sent by Another USCIS Office,Data Breach,PII Exposure,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1600 General Incident,Data Breach,General,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,G-1601 Lost Shipment,Data Breach,Lost Data,FOUO\n'
            'Information Spill/Mishandling,SPII / PII,,Data Breach,General PII,FOUO\n'
            'Facilitated Apprehension and Law Enforcement,Immigration,,Law Enforcement,Immigration,Official Use Only\n'
            'Suspicious or Threatening Activity,Threat,,Security,Threat,Official Use Only\n'
        )
        return category_file.strpath

    def prepare_valid_data(self, mock_data, max_records=None):
        """Prepare valid data records from mock data."""
        valid_data = []
        for record in mock_data:
            if (record.get('Incident_ID') and 
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
                if not record.get('Facility_Address_HELPER'):
                    record['Facility_Address_HELPER'] = 'Unknown Address'
                if not record.get('Facility_Latitude'):
                    record['Facility_Latitude'] = 0.0
                if not record.get('Facility_Longitude'):
                    record['Facility_Longitude'] = 0.0
                
                valid_data.append(record)
                
                if max_records and len(valid_data) >= max_records:
                    break
        
        return valid_data

    def test_preprocess_with_csv_output_basic(self, tmpdir):
        """Test basic preprocessing functionality with CSV output."""
        # Create category mapping file
        category_mapping_file = self.create_category_mapping_file(tmpdir)
        
        # Load and prepare mock data
        mock_data = self.load_mock_archer_data()
        valid_data = self.prepare_valid_data(mock_data, max_records=5)
        
        if not valid_data:
            pytest.skip("No valid data found in mock data for testing")
        
        # Configure preprocessing
        last_run = datetime(2025, 7, 1, tzinfo=timezone.utc)
        config = {
            'category_mapping_file': category_mapping_file,
            'filter_rejected': True,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        # Run preprocessing
        result = preprocess(valid_data, last_run, config)
        
        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0, "Should have processed some records"
        
        # Save to CSV file
        output_filename = f"preprocessed_data_basic_{self.timestamp}.csv"
        output_path = self.output_dir / output_filename
        result.to_csv(output_path, index=False)
        
        # Verify file was created and has content
        assert output_path.exists(), f"Output file should exist: {output_path}"
        
        # Read back and verify content
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(result), "Saved CSV should have same number of records"
        
        # Verify required columns exist
        required_columns = ['tenantItemID', 'openDate', 'type', 'subtype', 'sharing', 
                          'incidentReportDetails', 'phase', 'dissemination']
        for col in required_columns:
            assert col in saved_df.columns, f"Missing required column: {col}"
        
        print(f"✓ Basic preprocessing test completed. Output saved to: {output_path}")
        print(f"  - Processed {len(result)} records")
        print(f"  - File size: {output_path.stat().st_size} bytes")

    def test_preprocess_with_csv_output_comprehensive(self, tmpdir):
        """Test comprehensive preprocessing with all available mock data."""
        # Create category mapping file
        category_mapping_file = self.create_category_mapping_file(tmpdir)
        
        # Load all mock data
        mock_data = self.load_mock_archer_data()
        valid_data = self.prepare_valid_data(mock_data)
        
        if not valid_data:
            pytest.skip("No valid data found in mock data for testing")
        
        # Configure preprocessing with minimal filtering
        last_run = datetime(2025, 7, 1, tzinfo=timezone.utc)
        config = {
            'category_mapping_file': category_mapping_file,
            'filter_rejected': True,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        # Run preprocessing
        result = preprocess(valid_data, last_run, config)
        
        # Verify result
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0, "Should have processed some records"
        
        # Save to CSV file
        output_filename = f"preprocessed_data_comprehensive_{self.timestamp}.csv"
        output_path = self.output_dir / output_filename
        result.to_csv(output_path, index=False)
        
        # Verify file was created
        assert output_path.exists(), f"Output file should exist: {output_path}"
        
        # Read back and perform detailed validation
        saved_df = pd.read_csv(output_path)
        
        # Validate data quality
        assert len(saved_df) == len(result), "Saved CSV should have same number of records"
        assert all(saved_df['tenantItemID'].str.contains('BAL-', na=False)), "All records should have BAL- prefix"
        assert all(saved_df['phase'] == 'Monitored'), "All records should have phase = Monitored"
        assert all(saved_df['dissemination'] == 'FOUO'), "All records should have dissemination = FOUO"
        
        # Check that HTML was stripped from details
        html_records = saved_df[saved_df['incidentReportDetails'].str.contains('<', na=False)]
        assert len(html_records) == 0, "No HTML tags should remain in processed data"
        
        # Validate date formatting
        for _, row in saved_df.iterrows():
            open_date = row['openDate']
            assert 'T' in open_date and 'Z' in open_date, f"Date should be in ISO format: {open_date}"
        
        # Validate category mappings
        unique_types = saved_df['type'].unique()
        expected_types = ['Natural Disaster', 'Service Outage', 'External']
        for utype in unique_types:
            assert utype in expected_types, f"Unexpected type: {utype}"
        
        print(f"✓ Comprehensive preprocessing test completed. Output saved to: {output_path}")
        print(f"  - Processed {len(result)} records from {len(valid_data)} valid input records")
        print(f"  - File size: {output_path.stat().st_size} bytes")
        print(f"  - Unique types: {list(unique_types)}")
        print(f"  - Unique subtypes: {list(saved_df['subtype'].unique())}")

    def test_preprocess_with_csv_output_filtered_vs_unfiltered(self, tmpdir):
        """Test preprocessing with different filter configurations and compare outputs."""
        # Create category mapping file
        category_mapping_file = self.create_category_mapping_file(tmpdir)
        
        # Load mock data
        mock_data = self.load_mock_archer_data()
        valid_data = self.prepare_valid_data(mock_data)
        
        if not valid_data:
            pytest.skip("No valid data found in mock data for testing")
        
        # Test with filters enabled
        last_run = datetime(2025, 6, 1, tzinfo=timezone.utc)  # Earlier date to filter more records
        config_filtered = {
            'category_mapping_file': category_mapping_file,
            'filter_rejected': True,
            'filter_unprocessed': True,
            'filter_by_date': True
        }
        
        result_filtered = preprocess(valid_data, last_run, config_filtered)
        
        # Test with filters disabled
        config_unfiltered = {
            'category_mapping_file': category_mapping_file,
            'filter_rejected': False,
            'filter_unprocessed': False,
            'filter_by_date': False
        }
        
        result_unfiltered = preprocess(valid_data, last_run, config_unfiltered)
        
        # Save both results
        filtered_filename = f"preprocessed_data_filtered_{self.timestamp}.csv"
        unfiltered_filename = f"preprocessed_data_unfiltered_{self.timestamp}.csv"
        
        filtered_path = self.output_dir / filtered_filename
        unfiltered_path = self.output_dir / unfiltered_filename
        
        result_filtered.to_csv(filtered_path, index=False)
        result_unfiltered.to_csv(unfiltered_path, index=False)
        
        # Verify both files exist
        assert filtered_path.exists(), f"Filtered output file should exist: {filtered_path}"
        assert unfiltered_path.exists(), f"Unfiltered output file should exist: {unfiltered_path}"
        
        # Compare results
        assert len(result_unfiltered) >= len(result_filtered), "Unfiltered should have same or more records"
        
        print(f"✓ Filter comparison test completed:")
        print(f"  - Filtered output: {filtered_path} ({len(result_filtered)} records)")
        print(f"  - Unfiltered output: {unfiltered_path} ({len(result_unfiltered)} records)")
        print(f"  - Difference: {len(result_unfiltered) - len(result_filtered)} records filtered out")

    def test_preprocess_with_csv_output_error_handling(self, tmpdir):
        """Test preprocessing error handling and edge cases with CSV output."""
        # Test with empty data
        last_run = datetime(2025, 6, 1, tzinfo=timezone.utc)
        result_empty = preprocess([], last_run)
        
        # Save empty result
        empty_filename = f"preprocessed_data_empty_{self.timestamp}.csv"
        empty_path = self.output_dir / empty_filename
        result_empty.to_csv(empty_path, index=False)
        
        assert empty_path.exists(), "Empty result file should be created"
        
        # Read back and verify it's empty
        saved_empty = pd.read_csv(empty_path)
        assert len(saved_empty) == 0, "Empty result should remain empty"
        
        # Test with missing category mapping file
        invalid_config = {
            'category_mapping_file': '/nonexistent/file.csv',
            'filter_rejected': True,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        # Create minimal valid data
        test_data = [{
            'Incident_ID': 'INC-001',
            'SIR_': 'BAL-TEST-001',
            'Local_Date_Reported': '2025-01-01T10:00:00Z',
            'Facility_Address_HELPER': '123 Test St',
            'Facility_Latitude': 38.9072,
            'Facility_Longitude': -77.0369,
            'Date_SIR_Processed__NT': '2025-01-01T15:00:00Z',
            'Details': 'Test details',
            'Section_5__Action_Taken': 'Test action',
            'Type_of_SIR': 'Test Type',
            'Category_Type': 'Test Category',
            'Sub_Category_Type': 'Test Subcategory'
        }]
        
        # This should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            preprocess(test_data, last_run, invalid_config)
        
        print(f"✓ Error handling test completed:")
        print(f"  - Empty data output: {empty_path}")
        print(f"  - FileNotFoundError properly raised for missing category mapping")

    def test_preprocess_data_quality_validation(self, tmpdir):
        """Test data quality validation in preprocessed output."""
        # Create category mapping file
        category_mapping_file = self.create_category_mapping_file(tmpdir)
        
        # Load mock data
        mock_data = self.load_mock_archer_data()
        valid_data = self.prepare_valid_data(mock_data)
        
        if not valid_data:
            pytest.skip("No valid data found in mock data for testing")
        
        # Configure preprocessing
        last_run = datetime(2025, 7, 1, tzinfo=timezone.utc)
        config = {
            'category_mapping_file': category_mapping_file,
            'filter_rejected': True,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        # Run preprocessing
        result = preprocess(valid_data, last_run, config)
        
        # Save to CSV
        output_filename = f"preprocessed_data_quality_{self.timestamp}.csv"
        output_path = self.output_dir / output_filename
        result.to_csv(output_path, index=False)
        
        # Read back for validation
        saved_df = pd.read_csv(output_path)
        
        # Perform comprehensive data quality checks
        quality_report = {
            'total_records': len(saved_df),
            'null_values': {},
            'data_types': {},
            'value_ranges': {},
            'format_validation': {}
        }
        
        # Check for null values in critical fields
        critical_fields = ['tenantItemID', 'openDate', 'type', 'subtype', 'sharing']
        for field in critical_fields:
            null_count = saved_df[field].isnull().sum()
            quality_report['null_values'][field] = null_count
            assert null_count == 0, f"Critical field {field} should not have null values"
        
        # Validate data types and formats
        assert all(saved_df['tenantItemID'].str.startswith('BAL-')), "All tenantItemID should start with BAL-"
        
        # Validate date format
        for date_str in saved_df['openDate']:
            assert 'T' in date_str and 'Z' in date_str, f"Invalid date format: {date_str}"
        
        # Validate sharing levels
        valid_sharing = ['FOUO', 'Official Use Only', 'Unclassified']
        invalid_sharing = saved_df[~saved_df['sharing'].isin(valid_sharing)]
        assert len(invalid_sharing) == 0, f"Invalid sharing levels found: {invalid_sharing['sharing'].unique()}"
        
        # Save quality report
        quality_filename = f"data_quality_report_{self.timestamp}.txt"
        quality_path = self.output_dir / quality_filename
        
        with open(quality_path, 'w') as f:
            f.write("Data Quality Report\n")
            f.write("==================\n\n")
            f.write(f"Total Records: {quality_report['total_records']}\n\n")
            f.write("Null Value Counts:\n")
            for field, count in quality_report['null_values'].items():
                f.write(f"  {field}: {count}\n")
            f.write(f"\nUnique Types: {list(saved_df['type'].unique())}\n")
            f.write(f"Unique Subtypes: {list(saved_df['subtype'].unique())}\n")
            f.write(f"Unique Sharing Levels: {list(saved_df['sharing'].unique())}\n")
        
        print(f"✓ Data quality validation completed:")
        print(f"  - Processed data: {output_path}")
        print(f"  - Quality report: {quality_path}")
        print(f"  - {len(saved_df)} records passed all quality checks")

    def test_preprocess_performance_with_large_dataset(self, tmpdir):
        """Test preprocessing performance with larger dataset."""
        # Create category mapping file
        category_mapping_file = self.create_category_mapping_file(tmpdir)
        
        # Load mock data and replicate it to create a larger dataset
        mock_data = self.load_mock_archer_data()
        valid_data = self.prepare_valid_data(mock_data)
        
        if not valid_data:
            pytest.skip("No valid data found in mock data for testing")
        
        # Replicate data to create larger dataset (modify IDs to avoid duplicates)
        large_dataset = []
        for i in range(10):  # Create 10x the original data
            for record in valid_data:
                new_record = record.copy()
                new_record['Incident_ID'] = f"{record['Incident_ID']}_COPY_{i}"
                new_record['SIR_'] = f"{record['SIR_']}_COPY_{i}"
                large_dataset.append(new_record)
        
        # Configure preprocessing
        last_run = datetime(2025, 7, 1, tzinfo=timezone.utc)
        config = {
            'category_mapping_file': category_mapping_file,
            'filter_rejected': True,
            'filter_unprocessed': False,
            'filter_by_date': True
        }
        
        # Measure processing time
        start_time = datetime.now()
        result = preprocess(large_dataset, last_run, config)
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Save to CSV
        output_filename = f"preprocessed_data_large_{self.timestamp}.csv"
        output_path = self.output_dir / output_filename
        
        csv_start_time = datetime.now()
        result.to_csv(output_path, index=False)
        csv_end_time = datetime.now()
        csv_time = (csv_end_time - csv_start_time).total_seconds()
        
        # Verify results
        assert len(result) > 0, "Should have processed records from large dataset"
        assert output_path.exists(), "Large dataset output file should exist"
        
        # Performance report
        performance_filename = f"performance_report_{self.timestamp}.txt"
        performance_path = self.output_dir / performance_filename
        
        with open(performance_path, 'w') as f:
            f.write("Performance Report\n")
            f.write("=================\n\n")
            f.write(f"Input Records: {len(large_dataset)}\n")
            f.write(f"Output Records: {len(result)}\n")
            f.write(f"Processing Time: {processing_time:.2f} seconds\n")
            f.write(f"CSV Write Time: {csv_time:.2f} seconds\n")
            f.write(f"Total Time: {processing_time + csv_time:.2f} seconds\n")
            f.write(f"Records per Second: {len(large_dataset) / processing_time:.2f}\n")
            f.write(f"Output File Size: {output_path.stat().st_size} bytes\n")
        
        print(f"✓ Performance test completed:")
        print(f"  - Processed {len(large_dataset)} input records → {len(result)} output records")
        print(f"  - Processing time: {processing_time:.2f} seconds")
        print(f"  - Output file: {output_path}")
        print(f"  - Performance report: {performance_path}")

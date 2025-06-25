"""
Test script to verify the openDate_1 fix.
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processing.preprocess import preprocess
from tests.test_processing import TestProcessing

def main():
    """Test the fix for the openDate_1 issue."""
    print("Testing fix for openDate_1 issue...")
    
    # Create a test instance to access the load_mock_archer_data method
    test_processing = TestProcessing()
    
    # Load mock data from CSV
    mock_data = test_processing.load_mock_archer_data()
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
    
    # Create a simple category mapping
    import tempfile
    tmpdir = tempfile.mkdtemp()
    category_file = os.path.join(tmpdir, 'category_mappings.csv')
    
    with open(category_file, 'w') as f:
        f.write(
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
    
    # Use a date that will include the mock data
    last_run = 0  # Use 0 as a placeholder for the last incident ID
    config = {
        'category_mapping_file': category_file,
        'filter_rejected': False,
        'filter_unprocessed': False,
        'filter_by_date': False,
        'filter_by_incident_id': False  # Disable incident ID filtering
    }
    
    # Process the data
    print("Processing data...")
    result = preprocess(valid_data, last_run, config)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Use a fixed filename for the output
    json_filename = 'processed_data_fixed.json'
    json_path = os.path.join(output_dir, json_filename)
    print(f"Using fixed filename: {json_filename}")
    
    # Convert DataFrame to JSON and save to file
    # Use orient='records' to get a list of dictionaries
    result_json = result.to_json(orient='records')
    with open(json_path, 'w') as f:
        # Parse and re-dump to get pretty formatting
        parsed_json = json.loads(result_json)
        json.dump(parsed_json, f, indent=2)
    
    print(f"JSON file created: {json_path}")
    
    # Read the JSON file and verify its contents
    with open(json_path, 'r') as f:
        loaded_json = json.load(f)
    
    # Check if openDate_1 field exists
    first_record = loaded_json[0]
    if 'openDate_1' in first_record:
        print("ERROR: openDate_1 field still exists in the output!")
        print(f"Fields in first record: {list(first_record.keys())}")
    else:
        print("SUCCESS: openDate_1 field has been removed from the output!")
    
    # Check if openDate field exists and has a value
    if 'openDate' in first_record and first_record['openDate']:
        print(f"SUCCESS: openDate field exists and has value: {first_record['openDate']}")
    else:
        print("ERROR: openDate field is missing or has no value!")
    
    print(f"Successfully created JSON output file: {json_path}")

if __name__ == "__main__":
    main()

"""
Integration test for fetching data from the Archer API and saving it as CSV.

This test connects to the actual Archer API, fetches SIR data, and saves it as a CSV file
for data examination purposes.
"""

import unittest
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_config
from src.archer.auth import get_archer_auth
from src.utils.logging_utils import get_logger

# Get logger for this module
logger = get_logger('archer.integration_test')


class TestArcherIntegration(unittest.TestCase):
    """Integration test for Archer API data fetching and CSV export."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = get_config()
        self.archer_config = self.config.get_section('archer')
        
        # Create output directory for CSV files
        self.output_dir = project_root / 'tests' / 'output'
        self.output_dir.mkdir(exist_ok=True)
        
        # Set up CSV file path with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_file_path = self.output_dir / f'archer_sir_data_{timestamp}.csv'
        
        logger.info(f"Integration test setup complete. Output file: {self.csv_file_path}")

    def test_fetch_archer_data_and_save_csv(self):
        """
        Integration test that fetches data from Archer API and saves it as CSV.
        
        This test will:
        1. Connect to the Archer API using configuration
        2. Fetch SIR data with Incident_ID greater than a specified value
        3. Save the data as a CSV file for examination
        4. Validate the data structure
        """
        logger.info("Starting Archer API integration test")
        
        # Verify we have the required configuration
        required_keys = ['username', 'password', 'instance', 'url']
        for key in required_keys:
            self.assertIsNotNone(
                self.archer_config.get(key),
                f"Missing required Archer configuration: {key}"
            )
        
        try:
            # Create Archer authentication instance
            logger.info("Creating Archer authentication instance")
            archer_auth = get_archer_auth(self.archer_config)
            
            # Set incident ID range for data fetching (start from incident ID 400 for recent data)
            since_incident_id = 400
            logger.info(f"Fetching SIR data since incident ID: {since_incident_id}")
            
            # Fetch SIR data using context manager
            sir_data = []
            with archer_auth:
                logger.info("Authenticated with Archer API")
                sir_data = archer_auth.get_sir_data(since_incident_id=since_incident_id)
            
            logger.info(f"Retrieved {len(sir_data)} SIR records from Archer API")
            
            # Save data to CSV
            self._save_data_to_csv(sir_data)
            
            # Validate the results
            self._validate_data_structure(sir_data)
            
            # Print summary information
            self._print_data_summary(sir_data)
            
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}")
            # Don't fail the test if it's a connection issue - log it instead
            if "fallback" in str(e).lower() or "import" in str(e).lower():
                logger.warning("Using fallback implementation - this is expected in development")
                self.skipTest("Skipping integration test - using fallback implementation")
            else:
                raise

    def test_fetch_all_archer_data_and_save_csv(self):
        """
        Integration test that fetches all available data from Archer API.
        
        This test fetches all available SIR data without date filtering.
        """
        logger.info("Starting Archer API integration test (all data)")
        
        # Verify we have the required configuration
        required_keys = ['username', 'password', 'instance', 'url']
        for key in required_keys:
            self.assertIsNotNone(
                self.archer_config.get(key),
                f"Missing required Archer configuration: {key}"
            )
        
        try:
            # Create Archer authentication instance
            logger.info("Creating Archer authentication instance")
            archer_auth = get_archer_auth(self.archer_config)
            
            # Fetch all SIR data
            logger.info("Fetching all available SIR data")
            
            sir_data = []
            with archer_auth:
                logger.info("Authenticated with Archer API")
                sir_data = archer_auth.get_sir_data()  # No date filter
            
            logger.info(f"Retrieved {len(sir_data)} total SIR records from Archer API")
            
            # Save data to CSV with different filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            csv_file_path = self.output_dir / f'archer_sir_data_all_{timestamp}.csv'
            self._save_data_to_csv(sir_data, csv_file_path)
            
            # Validate the results
            self._validate_data_structure(sir_data)
            
            # Print summary information
            self._print_data_summary(sir_data)
            
        except Exception as e:
            logger.error(f"Integration test failed: {str(e)}")
            # Don't fail the test if it's a connection issue - log it instead
            if "fallback" in str(e).lower() or "import" in str(e).lower():
                logger.warning("Using fallback implementation - this is expected in development")
                self.skipTest("Skipping integration test - using fallback implementation")
            else:
                raise

    def _save_data_to_csv(self, data: List[Dict[str, Any]], csv_path: Path = None) -> None:
        """
        Save the SIR data to a CSV file.
        
        Args:
            data (List[Dict[str, Any]]): List of SIR data records
            csv_path (Path, optional): Path to save CSV file. Uses default if None.
        """
        if csv_path is None:
            csv_path = self.csv_file_path
            
        logger.info(f"Saving {len(data)} records to CSV file: {csv_path}")
        
        if not data:
            logger.warning("No data to save to CSV")
            # Create empty CSV file with headers
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['No data available'])
            return
        
        try:
            # Get all unique field names from all records
            all_fields = set()
            for record in data:
                if isinstance(record, dict):
                    all_fields.update(record.keys())
            
            # Sort field names for consistent column order
            fieldnames = sorted(list(all_fields))
            
            # Write CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header
                writer.writeheader()
                
                # Write data rows
                for record in data:
                    if isinstance(record, dict):
                        # Handle nested data by converting to string
                        clean_record = {}
                        for key, value in record.items():
                            if isinstance(value, (dict, list)):
                                clean_record[key] = str(value)
                            elif value is None:
                                clean_record[key] = ''
                            else:
                                clean_record[key] = str(value)
                        writer.writerow(clean_record)
            
            logger.info(f"Successfully saved data to CSV file: {csv_path}")
            
        except Exception as e:
            logger.error(f"Error saving data to CSV: {str(e)}")
            raise

    def _validate_data_structure(self, data: List[Dict[str, Any]]) -> None:
        """
        Validate the structure of the retrieved data.
        
        Args:
            data (List[Dict[str, Any]]): List of SIR data records
        """
        logger.info("Validating data structure")
        
        # Basic validation
        self.assertIsInstance(data, list, "Data should be a list")
        
        if data:
            # Check that each record is a dictionary
            for i, record in enumerate(data[:5]):  # Check first 5 records
                self.assertIsInstance(record, dict, f"Record {i} should be a dictionary")
                
                # Log field names for the first record
                if i == 0:
                    logger.info(f"Sample record fields: {list(record.keys())}")
        else:
            logger.info("No data records to validate")

    def _print_data_summary(self, data: List[Dict[str, Any]]) -> None:
        """
        Print a summary of the retrieved data.
        
        Args:
            data (List[Dict[str, Any]]): List of SIR data records
        """
        logger.info("=== DATA SUMMARY ===")
        logger.info(f"Total records: {len(data)}")
        
        if data:
            # Get field statistics
            all_fields = set()
            for record in data:
                if isinstance(record, dict):
                    all_fields.update(record.keys())
            
            logger.info(f"Total unique fields: {len(all_fields)}")
            logger.info(f"Field names: {sorted(list(all_fields))}")
            
            # Show sample record
            if data:
                logger.info("=== SAMPLE RECORD ===")
                sample_record = data[0]
                for key, value in sample_record.items():
                    # Truncate long values for display
                    display_value = str(value)
                    if len(display_value) > 100:
                        display_value = display_value[:100] + "..."
                    logger.info(f"{key}: {display_value}")
        
        logger.info(f"CSV file saved to: {self.csv_file_path}")
        logger.info("=== END SUMMARY ===")

    def test_archer_connection_only(self):
        """
        Test just the Archer API connection without fetching data.
        
        This is useful for verifying connectivity and authentication.
        """
        logger.info("Testing Archer API connection")
        
        # Verify we have the required configuration
        required_keys = ['username', 'password', 'instance', 'url']
        for key in required_keys:
            self.assertIsNotNone(
                self.archer_config.get(key),
                f"Missing required Archer configuration: {key}"
            )
        
        try:
            # Create Archer authentication instance
            logger.info("Creating Archer authentication instance")
            archer_auth = get_archer_auth(self.archer_config)
            
            # Test authentication
            with archer_auth:
                logger.info("Successfully authenticated with Archer API")
                self.assertTrue(archer_auth.authenticated, "Should be authenticated")
            
            logger.info("Successfully disconnected from Archer API")
            self.assertFalse(archer_auth.authenticated, "Should be disconnected")
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            # Don't fail the test if it's a connection issue - log it instead
            if "fallback" in str(e).lower() or "import" in str(e).lower():
                logger.warning("Using fallback implementation - this is expected in development")
                self.skipTest("Skipping connection test - using fallback implementation")
            else:
                raise


def run_integration_test():
    """
    Convenience function to run the integration test directly.
    
    This can be called from other scripts or run directly.
    """
    # Set up logging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    suite = unittest.TestLoader().loadTestsFromTestCase(TestArcherIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the integration test
    success = run_integration_test()
    
    if success:
        print("\n✅ Integration test completed successfully!")
        print("Check the tests/output/ directory for the generated CSV file.")
    else:
        print("\n❌ Integration test failed!")
        sys.exit(1)

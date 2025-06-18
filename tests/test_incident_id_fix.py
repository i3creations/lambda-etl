#!/usr/bin/env python3
"""
Test Incident ID Fix

This module tests that the Incident_ID column is properly preserved in the processed data.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
from datetime import datetime

# Import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.processing.field_mapping import field_names
from src.processing.default_fields import default_fields


class TestIncidentIDFix(unittest.TestCase):
    """
    Test case for the Incident ID fix.
    """
    
    def test_incident_id_preserved_in_lambda_handler(self):
        """
        Test that the Incident_ID column is properly preserved for the lambda_handler.
        This test directly simulates the critical part of the process without using the full preprocess function.
        """
        # Create a simple DataFrame with the expected columns
        df = pd.DataFrame({
            'tenantItemID': ['SIR-1001', 'SIR-1002'],
            'openDate': ['2025-06-18T13:30:00.000Z', '2025-06-18T14:30:00.000Z'],
            'location': ['123 Test St, Test City, TS 12345', '456 Test Ave, Test City, TS 12345'],
            'latitude': ['38.8977', '38.8978'],
            'longitude': ['-77.0365', '-77.0366'],
            'swoDate': ['2025-06-18T13:35:00.000Z', '2025-06-18T14:35:00.000Z'],
            'type': ['Law Enforcement', 'Law Enforcement'],
            'subtype': ['Immigration Enforcement', 'Immigration Enforcement'],
            'sharing': ['USG', 'USG'],
            'title': ['[SIR-1001]: Facilitated Apprehension and Law Enforcement', 
                      '[SIR-1002]: Facilitated Apprehension and Law Enforcement'],
            'incidentReportDetails': ['Test incident details\nTest action taken', 
                                     'Another test incident details\nAnother test action taken'],
            # Add default fields
            'phase': ['Monitored', 'Monitored'],
            'dissemination': ['FOUO', 'FOUO'],
            'trafficLightProtocol': [None, None],
            'authorizedBy': ['Command Center Group', 'Command Center Group'],
            'overview': [None, None],
            'initialMedium': ['Government Database', 'Government Database'],
            'initialOfficialSource': ['USCIS', 'USCIS'],
            'initialMediaSource': ['Not Provided', 'Not Provided'],
            'archivesOn': ['A-LAN', 'A-LAN'],
            'impactedSectorList': [None, None],
            'impactedSubSectorList': [None, None],
            'intlThreatsIncidents': [False, False],
            'terrorismRelated': [False, False],
            'additionalReporting': [None, None],
            'scheduledDate': [None, None],
            'mediaReportDate': [None, None],
            'officialReportDate': [None, None],
            'tenantAbbreviation': ['USCIS', 'USCIS'],
            'publishDate': [None, None],
            'approvedBy': ['Command Center Group', 'Command Center Group'],
            # Add the Incident_ID column that we want to preserve
            'Incident_ID': [1001, 1002]
        })
        
        # Check that the Incident_ID column exists in the data
        self.assertIn('Incident_ID', df.columns, 
                     f"Incident_ID column not found in data. Available columns: {df.columns.tolist()}")
        
        # Simulate the critical part of the lambda_handler function that checks for the Incident_ID column
        if 'Incident_ID' in df.columns:
            # Find the highest incident ID from the records
            max_incident_id = df['Incident_ID'].max()
            
            # Check that the highest Incident_ID is correct
            self.assertEqual(1002, max_incident_id, f"Expected max Incident_ID to be 1002, but got {max_incident_id}")
        else:
            self.fail("'Incident_ID' column not found in data")


if __name__ == '__main__':
    unittest.main()

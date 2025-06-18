"""
Data Preprocessing Module

This module handles the preprocessing of Significant Incident Report (SIR) data
from the USCIS Archer system before sending it to the DHS OPS Portal.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

import pandas as pd
import numpy as np

from .field_mapping import field_names
from .default_fields import default_fields
from .html_stripper import strip_tags
from ..utils.logging_utils import get_logger

# Get logger for this module
logger = get_logger('processing.preprocess')


def preprocess(data: List[Dict[str, Any]], last_incident_id: int, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Preprocess Significant Incident Report (SIR) data.
    
    This function processes raw SIR data from the Archer system, filters records,
    maps categories, and formats fields according to the DHS OPS Portal requirements.
    
    Args:
        data (List[Dict[str, Any]]): Raw SIR data from the Archer system
        last_incident_id (int): ID of the last processed incident
        config (Dict[str, Any], optional): Configuration dictionary. If None, uses default values.
        
    Returns:
        pd.DataFrame: Processed data ready to be sent to the OPS Portal
        
    Raises:
        ValueError: If the data is empty or invalid
        FileNotFoundError: If the category mapping file is not found
    """
    logger.info("Starting data preprocessing")
    
    # Use default configuration if none provided
    if config is None:
        config = {
            'category_mapping_file': 'config/category_mappings.csv',
            'filter_rejected': True,
            'filter_unprocessed': True,
            'filter_by_incident_id': True
        }
    
    category_mapping_file = config.get('category_mapping_file', 'config/category_mappings.csv')
    filter_rejected = config.get('filter_rejected', True)
    filter_unprocessed = config.get('filter_unprocessed', True)
    filter_by_incident_id = config.get('filter_by_incident_id', True)
    
    try:
        # Check if data is empty
        if not data:
            logger.warning("No data to process")
            # Return empty DataFrame with expected column structure
            expected_columns = list(field_names.values()) + list(default_fields.keys())
            # Remove duplicates while preserving order
            seen = set()
            unique_columns = []
            for col in expected_columns:
                if col not in seen:
                    unique_columns.append(col)
                    seen.add(col)
            return pd.DataFrame(columns=unique_columns)
        
        logger.info(f"Processing {len(data)} records")
        
        # Read data into DataFrame
        try:
            df = pd.DataFrame(data)
            
            # Check if required columns exist
            required_columns = [
                'Incidents_Id', 'SIR_', 'Local_Date_Reported',
                'Facility_Address_HELPER', 'Facility_Latitude', 'Facility_Longitude',
                'Date_SIR_Processed__NT', 'Details', 'Section_5__Action_Taken',
                'Type_of_SIR', 'Category_Type', 'Sub_Category_Type'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Select required columns and set index
            df = df[required_columns].set_index('Incidents_Id')
            
        except Exception as e:
            logger.error(f"Error creating DataFrame: {str(e)}")
            raise ValueError(f"Error creating DataFrame: {str(e)}")
        
        # Apply filters
        original_count = len(df)
        filter_mask = pd.Series([True] * len(df), index=df.index)
        
        if filter_rejected:
            logger.info("Applying filter: excluding rejected SIRs")
            filter_mask = filter_mask & (df['SIR_'] != 'REJECTED')
            
        if filter_unprocessed:
            logger.info("Applying filter: excluding unprocessed SIRs")
            filter_mask = filter_mask & (~df['Date_SIR_Processed__NT'].isnull())
            
        if filter_by_incident_id:
            logger.info(f"Applying filter: excluding records with incident ID <= {last_incident_id}")
            # Filter by incident ID - only include records with ID greater than last processed ID
            filter_mask = filter_mask & (df.index > last_incident_id)
        
        if not filter_mask.all():
            df = df.loc[filter_mask]
            filtered_count = len(df)
            logger.info(f"Filtered {original_count - filtered_count} records, {filtered_count} remaining")
        else:
            logger.info("No records filtered")
        
        # Explode columns with multiple values
        cols_to_explode = ['Type_of_SIR', 'Category_Type', 'Sub_Category_Type']
        
        for col in cols_to_explode:
            df = df.explode(col)
        
        # Map Category/Type/Subtype to OPS Category/Type/Subtype/Sharing Level
        try:
            # Check if the category mapping file exists
            if not os.path.exists(category_mapping_file):
                logger.error(f"Category mapping file not found: {category_mapping_file}")
                raise FileNotFoundError(f"Category mapping file not found: {category_mapping_file}")
            
            logger.info(f"Loading category mappings from {category_mapping_file}")
            category_map = pd.read_csv(category_mapping_file)
            
            # Ensure consistent data types for merge columns
            merge_columns = ['Type_of_SIR', 'Category_Type', 'Sub_Category_Type']
            
            # Convert merge columns to string type and handle NaN/None values
            for col in merge_columns:
                # For the main dataframe
                df[col] = df[col].astype(str).replace('nan', '').replace('None', '')
                # For the category mapping dataframe
                category_map[col] = category_map[col].astype(str).replace('nan', '').replace('None', '')
            
            logger.debug(f"Data types before merge - df: {df[merge_columns].dtypes.to_dict()}")
            logger.debug(f"Data types before merge - category_map: {category_map[merge_columns].dtypes.to_dict()}")
            
            # Merge with category mappings
            original_count = len(df)
            df = pd.merge(
                df,
                category_map,
                on=merge_columns,
                how='inner'
            )
            merged_count = len(df)
            
            logger.info(f"Mapped categories: {merged_count} records matched, {original_count - merged_count} records dropped")
            
        except Exception as e:
            logger.error(f"Error mapping categories: {str(e)}")
            raise
        
        # Strip HTML tags from text fields
        cols_to_strip = ['Details', 'Section_5__Action_Taken']
        
        for col in cols_to_strip:
            logger.debug(f"Stripping HTML tags from {col}")
            df[col] = df[col].apply(strip_tags)
        
        # Add derived columns
        logger.info("Adding derived columns")
        df['title'] = '[' + df['SIR_'] + ']: ' + df['Type_of_SIR']
        df['incidentReportDetails'] = df['Details'] + '\n' + df['Section_5__Action_Taken']
        
        # Add default fields
        logger.info("Adding default fields")
        for key, value in default_fields.items():
            df[key] = value
        
        # Format datetime columns
        cols_to_format = ['Local_Date_Reported', 'Date_SIR_Processed__NT']
        
        for col in cols_to_format:
            logger.debug(f"Formatting datetime column: {col}")
            df[col] = pd.to_datetime(df[col], utc=True).dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        
        # Convert numeric columns to string
        cols_to_convert = ['Facility_Latitude', 'Facility_Longitude']
        
        for col in cols_to_convert:
            logger.debug(f"Converting {col} to string")
            df[col] = df[col].astype(str)
        
        # Rename columns according to field mapping
        logger.info("Renaming columns according to field mapping")
        df = df.reset_index().rename(columns=field_names).replace({np.nan: None})
        
        # Drop unnecessary columns (keep type, subtype, sharing from category mapping)
        cols_to_drop = [
            'index', 'Details', 'Section_5__Action_Taken', 'Type_of_SIR',
            'Category_Type', 'Sub_Category_Type', 'category', 'Incident_ID'
        ]
        
        # Only drop columns that actually exist in the dataframe
        cols_to_drop = [col for col in cols_to_drop if col in df.columns]
        
        logger.info(f"Dropping unnecessary columns: {cols_to_drop}")
        if cols_to_drop:
            df = df.drop(cols_to_drop, axis=1)
        
        logger.info(f"Preprocessing complete: {len(df)} records ready for submission")
        return df
        
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}")
        raise

"""
Main Module

This is the main orchestration script for the OPS API. It handles the entire workflow
of extracting data from the Archer system, preprocessing it, and sending it to the
DHS OPS Portal.
"""

import os
import sys
import argparse
import logging
import boto3
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import get_config
from .archer.auth import get_archer_auth
from .processing.preprocess import preprocess
from .ops_portal.api import send
from .utils.time_utils import log_time
from .utils.logging_utils import setup_logging, get_logger
from .utils.secrets_manager import load_config_from_secrets


def get_last_incident_id_from_ssm() -> int:
    """
    Get the last processed incident ID from AWS Systems Manager Parameter Store.
    
    Returns:
        int: Last processed incident ID, or 0 if none found
    """
    try:
        ssm = boto3.client('ssm')
        parameter_name = '/ops-api/last-incident-id'
        
        try:
            response = ssm.get_parameter(Name=parameter_name)
            incident_id_str = response['Parameter']['Value']
            
            # Parse the incident ID
            incident_id = int(incident_id_str.strip())
            
            return incident_id
            
        except ssm.exceptions.ParameterNotFound:
            # Parameter doesn't exist yet, this is normal for first run
            return 0
            
    except Exception as e:
        print(f"Warning: Error getting last incident ID from SSM: {str(e)}. Starting from 0.")
        return 0


def update_last_incident_id_in_ssm(incident_id: int) -> None:
    """
    Update the last processed incident ID in AWS Systems Manager Parameter Store.
    
    Args:
        incident_id (int): Incident ID to save
    """
    try:
        # Store in AWS Systems Manager Parameter Store
        ssm = boto3.client('ssm')
        parameter_name = '/ops-api/last-incident-id'
        
        ssm.put_parameter(
            Name=parameter_name,
            Value=str(incident_id),
            Type='String',
            Overwrite=True,
            Description='Last processed incident ID for OPS API'
        )
        
    except Exception as e:
        print(f"Error updating last incident ID in SSM: {str(e)}")
        raise


def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='OPS API - Sync SIR data from Archer to OPS Portal')
    
    parser.add_argument(
        '--config',
        help='Path to configuration file',
        default=None
    )
    
    parser.add_argument(
        '--log-level',
        help='Logging level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
    )
    
    parser.add_argument(
        '--log-file',
        help='Path to log file',
        default=None
    )
    
    parser.add_argument(
        '--time-log',
        help='Path to time log file',
        default=None
    )
    
    parser.add_argument(
        '--dry-run',
        help='Process data but do not send to OPS Portal',
        action='store_true'
    )
    
    parser.add_argument(
        '--env-file',
        help='Path to .env file',
        default=None
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for the OPS API.
    
    This function orchestrates the entire workflow:
    1. Parse command line arguments
    2. Set up logging
    3. Load configuration
    4. Get the last run time
    5. Authenticate with Archer and get SIR data
    6. Preprocess the data
    7. Send the processed data to the OPS Portal
    """
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    # If log level is specified in command line, use it; otherwise, use environment variable
    log_level = getattr(logging, args.log_level) if args.log_level else None
    logger = setup_logging(log_level=log_level, log_file=args.log_file)
    
    try:
        logger.info("Starting OPS API")
        
        # Load configuration based on environment
        environment = os.environ.get('ENVIRONMENT', 'development')
        
        if environment in ['preproduction', 'production']:
            # Load configuration from AWS Secrets Manager
            logger.info(f"Loading configuration from AWS Secrets Manager for {environment} environment")
            config_dict = load_config_from_secrets()
            
            # Create a simple config object that mimics the Config class interface
            class SecretsConfig:
                def __init__(self, config_data):
                    self.config_data = config_data
                
                def get_section(self, section):
                    return self.config_data.get(section, {})
            
            config = SecretsConfig(config_dict)
            
            # Update logging configuration with the loaded config
            logger = setup_logging(log_level=None, log_file=args.log_file, config=config_dict)
        else:
            # Load configuration from files and environment variables (development)
            logger.info("Loading configuration from files and environment variables for development")
            
            # Load .env file if specified
            env_file = args.env_file or os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            if env_file and os.path.exists(env_file):
                from dotenv import load_dotenv
                load_dotenv(env_file)
                logger.info(f"Loaded environment variables from {env_file}")
            
            config = get_config(args.config)
            
            # Update logging configuration with environment variables (now loaded from .env)
            logger = setup_logging(log_level=None, log_file=args.log_file)
        
        logger.info(f"Configuration loaded successfully for {environment} environment")
        
        # Get the last processed incident ID from SSM Parameter Store
        last_incident_id = get_last_incident_id_from_ssm()
        logger.info(f"Last processed incident ID: {last_incident_id}")
        
        # Authenticate with Archer and get SIR data
        archer_config = config.get_section('archer')
        archer = get_archer_auth(archer_config)
        
        logger.info("Retrieving SIR data from Archer")
        raw_data = archer.get_sir_data(since_incident_id=last_incident_id)
        logger.info(f"Retrieved {len(raw_data)} records from Archer")
        
        # Preprocess the data
        processing_config = config.get_section('processing')
        processed_data = preprocess(raw_data, last_incident_id, processing_config)
        logger.info(f"Processed {len(processed_data)} records")
        
        # Send the processed data to the OPS Portal
        if not processed_data.empty:
            records = processed_data.to_dict('records')
            
            if args.dry_run:
                logger.info(f"Dry run: Would send {len(records)} records to OPS Portal")
            else:
                logger.info(f"Sending {len(records)} records to OPS Portal")
                ops_portal_config = config.get_section('ops_portal')
                responses = send(records, ops_portal_config)
                
                # Log results
                success_count = sum(1 for status, _ in responses.values() if 200 <= status < 300)
                logger.info(f"Successfully sent {success_count} of {len(records)} records")
                
                # Log failures
                for id, (status, response) in responses.items():
                    if status >= 300:
                        logger.error(f"Failed to send record {id}: {status} - {response}")
        else:
            logger.info("No records to send")
        
        # Update the last processed incident ID if we processed any records
        if not processed_data.empty and 'Incident_ID' in processed_data.columns:
            # Find the highest incident ID from the processed records
            max_incident_id = processed_data['Incident_ID'].max()
            if max_incident_id is not None and max_incident_id > last_incident_id:
                update_last_incident_id_in_ssm(int(max_incident_id))
                logger.info(f"Updated last processed incident ID to: {max_incident_id}")
        
        logger.info("OPS API completed successfully")
        return 0
        
    except Exception as e:
        logger.exception(f"Error in OPS API: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

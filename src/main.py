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
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import get_config
from .archer.auth import get_archer_auth
from .processing.preprocess import preprocess
from .ops_portal.api import send
from .utils.time_utils import log_time
from .utils.logging_utils import setup_logging, get_logger


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
    log_level = getattr(logging, args.log_level)
    logger = setup_logging(log_level=log_level, log_file=args.log_file)
    
    try:
        logger.info("Starting OPS API")
        
        # Load configuration
        env_file = args.env_file or os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        config = get_config(args.config, env_file)
        logger.info(f"Configuration loaded from {args.config or 'default config file'} and {env_file}")
        
        # Get the last run time
        time_log_path = args.time_log or config.get('general', 'time_log_path', 'time_log.txt')
        last_run = log_time(time_log_path)
        logger.info(f"Last run time: {last_run}")
        
        # Authenticate with Archer and get SIR data
        archer_config = config.get_section('archer')
        archer = get_archer_auth(archer_config)
        
        logger.info("Retrieving SIR data from Archer")
        raw_data = archer.get_sir_data(since_date=last_run)
        logger.info(f"Retrieved {len(raw_data)} records from Archer")
        
        # Preprocess the data
        processing_config = config.get_section('processing')
        processed_data = preprocess(raw_data, last_run, processing_config)
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
        
        logger.info("OPS API completed successfully")
        return 0
        
    except Exception as e:
        logger.exception(f"Error in OPS API: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

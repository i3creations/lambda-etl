"""
AWS Lambda Handler Module

This module provides the AWS Lambda handler function for the OPS API.
It adapts the main functionality of the OPS API to run in an AWS Lambda environment.
This version uses AWS Secrets Manager for secure configuration management.
"""

import os
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.config import get_config
from src.archer.auth import get_archer_auth
from src.processing.preprocess import preprocess
from src.ops_portal.api import send
from src.utils.time_utils import get_last_run_time, update_last_run_time
from src.utils.secrets_manager import load_config_from_secrets

# Set up logging
logger = Logger(service="ops-api")


def get_env_variable(name: str, default: str = None) -> str:
    """
    Get an environment variable.
    
    Args:
        name (str): Environment variable name
        default (str, optional): Default value if the environment variable is not set.
        
    Returns:
        str: Environment variable value
    """
    value = os.environ.get(name, default)
    if value is None:
        logger.error(f"Environment variable {name} is not set")
        raise ValueError(f"Environment variable {name} is not set")
    return value


def load_config_from_env() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {}
    
    # Load Archer configuration
    config['archer'] = {
        'username': get_env_variable('OPSAPI_ARCHER_USERNAME'),
        'password': get_env_variable('OPSAPI_ARCHER_PASSWORD'),
        'instance': get_env_variable('OPSAPI_ARCHER_INSTANCE')
    }
    
    # Load OPS Portal configuration
    config['ops_portal'] = {
        'auth_url': get_env_variable('OPSAPI_OPS_PORTAL_AUTH_URL'),
        'item_url': get_env_variable('OPSAPI_OPS_PORTAL_ITEM_URL'),
        'client_id': get_env_variable('OPSAPI_OPS_PORTAL_CLIENT_ID'),
        'client_secret': get_env_variable('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
        'verify_ssl': get_env_variable('OPSAPI_OPS_PORTAL_VERIFY_SSL', 'false').lower() == 'true'
    }
    
    # Add SSL certificate configuration if provided
    cert_file = os.environ.get('OPSAPI_OPS_PORTAL_CERT_FILE')
    key_file = os.environ.get('OPSAPI_OPS_PORTAL_KEY_FILE')
    cert_data = os.environ.get('OPSAPI_OPS_PORTAL_CERT_DATA')
    key_data = os.environ.get('OPSAPI_OPS_PORTAL_KEY_DATA')
    
    if cert_file and key_file:
        config['ops_portal']['cert_file'] = cert_file
        config['ops_portal']['key_file'] = key_file
    elif cert_data and key_data:
        import base64
        config['ops_portal']['cert_data'] = {
            'cert': base64.b64decode(cert_data).decode('utf-8'),
            'key': base64.b64decode(key_data).decode('utf-8')
        }
    
    # Load processing configuration
    config['processing'] = {
        'category_mapping_file': 'config/category_mappings.csv',
        'field_mapping_file': 'config/field_mappings.csv',
        'categories_to_send_file': 'config/categories_to_send.csv',
        'categories_not_to_send_file': 'config/categories_not_to_send.csv',
        'filter_rejected': True,
        'filter_unprocessed': True,
        'filter_by_date': True
    }
    
    return config


def get_time_log_from_env() -> datetime:
    """
    Get the last run time from environment variable.
    
    Returns:
        datetime: Last run time
    """
    try:
        timestamp_str = get_env_variable('OPSAPI_TIME_LOG', datetime.now().isoformat())
        return datetime.fromisoformat(timestamp_str.strip())
    except Exception as e:
        logger.warning(f"Error getting time log from environment: {str(e)}. Using current time.")
        return datetime.now()


def update_time_log_in_env(timestamp: datetime) -> None:
    """
    Update the last run time in environment variable.
    
    Args:
        timestamp (datetime): Timestamp to save
    """
    try:
        # In a container environment, we can't update environment variables at runtime
        # So we just log the new timestamp
        logger.info(f"Would update time log to: {timestamp.isoformat()}")
        # In a real environment, we would need to store this in a persistent storage
        # like a file, database, or SSM parameter
    except Exception as e:
        logger.error(f"Error updating time log: {str(e)}")
        raise


@logger.inject_lambda_context
def lambda_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    AWS Lambda handler function for the OPS API.
    
    Args:
        event (Dict[str, Any]): Lambda event
        context (LambdaContext): Lambda context
        
    Returns:
        Dict[str, Any]: Lambda response
    """
    try:
        logger.info("Starting OPS API Lambda function")
        
        # Get configuration from AWS Secrets Manager
        config = load_config_from_secrets()
        
        # Add processing configuration (non-secret values)
        config['processing'] = {
            'category_mapping_file': 'config/category_mappings.csv',
            'field_mapping_file': 'config/field_mappings.csv',
            'categories_to_send_file': 'config/categories_to_send.csv',
            'categories_not_to_send_file': 'config/categories_not_to_send.csv',
            'filter_rejected': True,
            'filter_unprocessed': True,
            'filter_by_date': True
        }
        
        logger.info("Configuration loaded from AWS Secrets Manager")
        
        # Get the last run time
        last_run = get_time_log_from_env()
        logger.info(f"Last run time: {last_run}")
        
        # Authenticate with Archer and get SIR data
        archer_config = config['archer']
        archer = get_archer_auth(archer_config)
        
        logger.info("Retrieving SIR data from Archer")
        raw_data = archer.get_sir_data(since_date=last_run)
        logger.info(f"Retrieved {len(raw_data)} records from Archer")
        
        # Preprocess the data
        processing_config = config['processing']
        processed_data = preprocess(raw_data, last_run, processing_config)
        logger.info(f"Processed {len(processed_data)} records")
        
        # Send the processed data to the OPS Portal
        results = {
            'processed': len(processed_data),
            'sent': 0,
            'success': 0,
            'failed': 0
        }
        
        if not processed_data.empty:
            records = processed_data.to_dict('records')
            
            # Check if this is a dry run
            dry_run = event.get('dry_run', False)
            
            if dry_run:
                logger.info(f"Dry run: Would send {len(records)} records to OPS Portal")
                results['sent'] = 0
            else:
                logger.info(f"Sending {len(records)} records to OPS Portal")
                ops_portal_config = config['ops_portal']
                responses = send(records, ops_portal_config)
                
                # Log results
                success_count = sum(1 for status, _ in responses.values() if 200 <= status < 300)
                results['sent'] = len(records)
                results['success'] = success_count
                results['failed'] = len(records) - success_count
                
                logger.info(f"Successfully sent {success_count} of {len(records)} records")
                
                # Log failures
                for id, (status, response) in responses.items():
                    if status >= 300:
                        logger.error(f"Failed to send record {id}: {status} - {response}")
        else:
            logger.info("No records to send")
        
        # Update the last run time
        current_time = datetime.now()
        update_time_log_in_env(current_time)
        
        logger.info("OPS API Lambda function completed successfully")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'OPS API Lambda function completed successfully',
                'results': results
            })
        }
        
    except Exception as e:
        logger.exception(f"Error in OPS API Lambda function: {str(e)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error in OPS API Lambda function: {str(e)}'
            })
        }

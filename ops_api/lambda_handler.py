"""
AWS Lambda Handler Module

This module provides the AWS Lambda handler function for the OPS API.
It adapts the main functionality of the OPS API to run in an AWS Lambda environment.
"""

import os
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from .config import get_config
from .archer.auth import get_archer_auth
from .processing.preprocess import preprocess
from .ops_portal.api import send
from .utils.time_utils import get_last_run_time, update_last_run_time

# Set up logging
logger = Logger(service="ops-api")

# Initialize AWS clients
ssm = boto3.client('ssm')


def get_parameter(name: str, decrypt: bool = True) -> str:
    """
    Get a parameter from AWS Systems Manager Parameter Store.
    
    Args:
        name (str): Parameter name
        decrypt (bool, optional): Whether to decrypt the parameter. Defaults to True.
        
    Returns:
        str: Parameter value
    """
    try:
        response = ssm.get_parameter(Name=name, WithDecryption=decrypt)
        return response['Parameter']['Value']
    except Exception as e:
        logger.error(f"Error getting parameter {name}: {str(e)}")
        raise


def load_config_from_ssm() -> Dict[str, Any]:
    """
    Load configuration from AWS Systems Manager Parameter Store.
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {}
    
    # Load Archer configuration
    config['archer'] = {
        'username': get_parameter('/ops-api/archer/username'),
        'password': get_parameter('/ops-api/archer/password'),
        'instance': get_parameter('/ops-api/archer/instance')
    }
    
    # Load OPS Portal configuration
    config['ops_portal'] = {
        'auth_url': get_parameter('/ops-api/ops-portal/auth-url'),
        'item_url': get_parameter('/ops-api/ops-portal/item-url'),
        'client_id': get_parameter('/ops-api/ops-portal/client-id'),
        'client_secret': get_parameter('/ops-api/ops-portal/client-secret'),
        'verify_ssl': get_parameter('/ops-api/ops-portal/verify-ssl').lower() == 'true'
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


def get_time_log_from_ssm(parameter_name: str) -> datetime:
    """
    Get the last run time from SSM Parameter Store.
    
    Args:
        parameter_name (str): SSM parameter name
        
    Returns:
        datetime: Last run time
    """
    try:
        response = ssm.get_parameter(Name=parameter_name)
        timestamp_str = response['Parameter']['Value']
        return datetime.fromisoformat(timestamp_str.strip())
    except Exception as e:
        logger.warning(f"Error getting time log from SSM: {str(e)}. Using current time.")
        return datetime.now()


def update_time_log_in_ssm(parameter_name: str, timestamp: datetime) -> None:
    """
    Update the last run time in SSM Parameter Store.
    
    Args:
        parameter_name (str): SSM parameter name
        timestamp (datetime): Timestamp to save
    """
    try:
        ssm.put_parameter(
            Name=parameter_name,
            Value=timestamp.isoformat(),
            Type='String',
            Overwrite=True
        )
        logger.info(f"Updated time log in SSM: {timestamp.isoformat()}")
    except Exception as e:
        logger.error(f"Error updating time log in SSM: {str(e)}")
        raise


@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
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
        
        # Get configuration
        config = load_config_from_ssm()
        logger.info("Configuration loaded from SSM Parameter Store")
        
        # Get the last run time from SSM
        time_log_parameter = '/ops-api/time-log'
        last_run = get_time_log_from_ssm(time_log_parameter)
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
        
        # Update the last run time in SSM
        current_time = datetime.now()
        update_time_log_in_ssm(time_log_parameter, current_time)
        
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

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
import pytz
import boto3
from datetime import datetime
from typing import Dict, Any

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.config import get_config
from src.archer.auth import get_archer_auth
from src.processing.preprocess import preprocess
from src.ops_portal.api import send
from src.utils.time_utils import get_last_run_time_from_ssm, update_last_run_time_in_ssm, get_current_time
from src.utils.secrets_manager import load_config_from_secrets
from src.utils.logging_utils import get_logging_level_from_env, get_logging_level_from_config

# Set up logging with Eastern timezone
from aws_lambda_powertools.logging.formatter import LambdaPowertoolsFormatter
import json

# Create a custom formatter that uses Eastern timezone
class EasternTimezoneFormatter(LambdaPowertoolsFormatter):
    def format(self, record):
        # Get the original formatted message
        formatted_record = super().format(record)
        
        # Parse the JSON log record
        try:
            log_dict = json.loads(formatted_record)
            
            # Convert timestamp to Eastern timezone
            eastern_tz = pytz.timezone('US/Eastern')
            utc_dt = datetime.fromtimestamp(record.created, tz=pytz.UTC)
            eastern_dt = utc_dt.astimezone(eastern_tz)
            
            # Update the timestamp in the log record
            log_dict['timestamp'] = eastern_dt.strftime('%Y-%m-%d %H:%M:%S,%f')[:-3] + eastern_dt.strftime('%z')
            
            # Return the updated JSON string
            return json.dumps(log_dict)
        except (json.JSONDecodeError, KeyError):
            # If we can't parse or modify the JSON, return the original
            return formatted_record

# Create logger with custom formatter
logger = Logger(service="ops-api")

# Apply the custom formatter to the logger's handlers
for handler in logger.handlers:
    if hasattr(handler, 'setFormatter'):
        handler.setFormatter(EasternTimezoneFormatter())

def configure_logger_level(config=None):
    """
    Configure the logger level based on environment variables or AWS Secrets Manager.
    
    Args:
        config (Dict[str, Any], optional): Configuration dictionary from AWS Secrets Manager
    """
    # Determine the log level (priority: config > environment variable > default)
    log_level = None
    if config:
        log_level = get_logging_level_from_config(config)
    
    if log_level is None:
        log_level = get_logging_level_from_env()
    
    # Set the log level for the Lambda Powertools logger
    logger.setLevel(log_level)
    logger.info(f"Logger level set to: {logging.getLevelName(log_level)}")


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


def get_last_incident_id_from_ssm() -> int:
    """
    Get the last processed incident ID from AWS Systems Manager Parameter Store.
    
    Returns:
        int: Last processed incident ID, or 0 if none found
    """
    try:
        # Get endpoint URL from environment variable if running locally
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        
        # Create SSM client with endpoint URL if provided
        if endpoint_url:
            ssm = boto3.client('ssm', endpoint_url=endpoint_url)
        else:
            ssm = boto3.client('ssm')
            
        parameter_name = '/ops-api/last-incident-id'
        
        try:
            response = ssm.get_parameter(Name=parameter_name)
            incident_id_str = response['Parameter']['Value']
            
            # Parse the incident ID
            incident_id = int(incident_id_str.strip())
            
            logger.info(f"Retrieved last incident ID from SSM: {incident_id}")
            return incident_id
            
        except ssm.exceptions.ParameterNotFound:
            # Parameter doesn't exist yet, this is normal for first run
            logger.info("No previous incident ID found in SSM. Starting from 0")
            return 0
            
    except Exception as e:
        logger.warning(f"Error getting last incident ID from SSM: {str(e)}. Starting from 0.")
        return 0


def update_last_incident_id_in_ssm(incident_id: int) -> None:
    """
    Update the last processed incident ID in AWS Systems Manager Parameter Store.
    
    Args:
        incident_id (int): Incident ID to save
    """
    try:
        # Get endpoint URL from environment variable if running locally
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        
        # Create SSM client with endpoint URL if provided
        if endpoint_url:
            ssm = boto3.client('ssm', endpoint_url=endpoint_url)
        else:
            ssm = boto3.client('ssm')
            
        parameter_name = '/ops-api/last-incident-id'
        
        ssm.put_parameter(
            Name=parameter_name,
            Value=str(incident_id),
            Type='String',
            Overwrite=True,
            Description='Last processed incident ID for OPS API Lambda function'
        )
        
        logger.info(f"Updated last incident ID in SSM: {incident_id}")
        
    except Exception as e:
        logger.error(f"Error updating last incident ID in SSM: {str(e)}")
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
            'filter_by_incident_id': True
        }
        
        # Configure logger level based on the loaded configuration
        configure_logger_level(config)
        
        logger.info("Configuration loaded from AWS Secrets Manager")
        
        # Get the last processed incident ID from SSM Parameter Store
        last_incident_id = get_last_incident_id_from_ssm()
        logger.info(f"Last processed incident ID: {last_incident_id}")
        
        # Get the last run time from SSM Parameter Store
        last_run_time = get_last_run_time_from_ssm()
        logger.info(f"Last run time: {last_run_time}")
        
        # Check if test data is provided in the event
        if 'test_data' in event:
            logger.info("Using test data provided in the event")
            raw_data = event['test_data']
        else:
            # Authenticate with Archer and get SIR data
            archer_config = config['archer']
            archer = get_archer_auth(archer_config)
            
            logger.info("Retrieving SIR data from Archer")
            raw_data = archer.get_sir_data(since_incident_id=last_incident_id)
            
        logger.info(f"Retrieved {len(raw_data)} records from Archer")
        
        # Preprocess the data
        processing_config = config['processing']
        processed_data = preprocess(raw_data, last_incident_id, processing_config)
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
        
        # Update the last processed incident ID if we processed any records
        if not processed_data.empty:
            logger.info(f"Processed data columns: {processed_data.columns.tolist()}")
            
            if 'Incident_ID' in processed_data.columns:
                # Find the highest incident ID from the processed records
                try:
                    max_incident_id = processed_data['Incident_ID'].max()
                    logger.info(f"Max incident ID found: {max_incident_id}, Last incident ID: {last_incident_id}")
                    
                    if max_incident_id is not None and max_incident_id > last_incident_id:
                        try:
                            update_last_incident_id_in_ssm(int(max_incident_id))
                            logger.info(f"Successfully updated last processed incident ID to: {max_incident_id}")
                        except Exception as e:
                            logger.error(f"Failed to update last incident ID in SSM: {str(e)}")
                    else:
                        logger.warning(f"Not updating incident ID: max_incident_id={max_incident_id}, last_incident_id={last_incident_id}")
                except Exception as e:
                    logger.error(f"Error processing Incident_ID column: {str(e)}")
                    # Try to get a sample of the Incident_ID column to debug
                    try:
                        sample = processed_data['Incident_ID'].head().tolist()
                        logger.error(f"Sample of Incident_ID values: {sample}")
                    except Exception as sample_error:
                        logger.error(f"Could not get sample of Incident_ID values: {str(sample_error)}")
            else:
                logger.error("'Incident_ID' column not found in processed data. Available columns: " + 
                             ", ".join(processed_data.columns.tolist()))
                
                # Try to recover by looking for similar column names
                similar_columns = [col for col in processed_data.columns if 'id' in col.lower() or 'incident' in col.lower()]
                if similar_columns:
                    logger.warning(f"Found similar columns that might contain incident IDs: {similar_columns}")
        else:
            logger.info("No records processed, not updating incident ID")
        
        # Update the last run time in SSM Parameter Store
        current_time = get_current_time()
        update_last_run_time_in_ssm(current_time)
        logger.info(f"Updated last run time to: {current_time}")
        
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

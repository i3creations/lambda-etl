"""
AWS Secrets Manager Utility Module

This module provides functionality to retrieve secrets from AWS Secrets Manager
for use in Lambda environments instead of environment variables.
"""

import json
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional
import os

from .logging_utils import get_logger

# Get logger for this module
logger = get_logger('secrets_manager')


class SecretsManager:
    """
    AWS Secrets Manager client for retrieving application secrets.
    """
    
    def __init__(self, region_name: str = None):
        """
        Initialize the Secrets Manager client.
        
        Args:
            region_name (str, optional): AWS region name. If None, uses AWS_DEFAULT_REGION 
                                       environment variable or defaults to us-east-1.
        """
        self.region_name = region_name or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Get endpoint URL from environment variable if running locally
        endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
        
        # Create a Secrets Manager client
        session = boto3.session.Session()
        
        # Create client with endpoint URL if provided
        if endpoint_url:
            self.client = session.client(
                service_name='secretsmanager',
                region_name=self.region_name,
                endpoint_url=endpoint_url
            )
            logger.info(f"Initialized Secrets Manager client for region: {self.region_name} with endpoint URL: {endpoint_url}")
        else:
            self.client = session.client(
                service_name='secretsmanager',
                region_name=self.region_name
            )
            logger.info(f"Initialized Secrets Manager client for region: {self.region_name}")
        
        logger.info(f"Initialized Secrets Manager client for region: {self.region_name}")
    
    def get_secret(self, secret_name: str) -> Dict[str, Any]:
        """
        Retrieve a secret from AWS Secrets Manager.
        
        Args:
            secret_name (str): Name of the secret to retrieve
            
        Returns:
            Dict[str, Any]: Secret data as a dictionary
            
        Raises:
            ClientError: If there's an error retrieving the secret
            json.JSONDecodeError: If the secret is not valid JSON
        """
        try:
            logger.info(f"Retrieving secret: {secret_name}")
            
            get_secret_value_response = self.client.get_secret_value(
                SecretId=secret_name
            )
            
            # Parse the secret string as JSON
            secret_string = get_secret_value_response['SecretString']
            logger.debug(f"Raw secret string length: {len(secret_string)}")
            
            try:
                secret_data = json.loads(secret_string)
            except json.JSONDecodeError as json_error:
                # Log the problematic area around the error position
                error_pos = getattr(json_error, 'pos', 0)
                start_pos = max(0, error_pos - 50)
                end_pos = min(len(secret_string), error_pos + 50)
                context = secret_string[start_pos:end_pos]
                
                logger.error(f"JSON parsing error at position {error_pos}")
                logger.error(f"Context around error: ...{context}...")
                logger.error(f"Full JSON error: {str(json_error)}")
                raise json_error
            
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Error retrieving secret {secret_name}: {error_code} - {str(e)}")
            
            # Handle specific error cases
            if error_code == 'DecryptionFailureException':
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                raise e
            elif error_code == 'InternalServiceErrorException':
                # An error occurred on the server side.
                raise e
            elif error_code == 'InvalidParameterException':
                # You provided an invalid value for a parameter.
                raise e
            elif error_code == 'InvalidRequestException':
                # You provided a parameter value that is not valid for the current state of the resource.
                raise e
            elif error_code == 'ResourceNotFoundException':
                # We can't find the resource that you asked for.
                raise e
            else:
                raise e
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing secret {secret_name} as JSON: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {str(e)}")
            raise e
    
    def get_secret_value(self, secret_name: str, key: str, default: Any = None) -> Any:
        """
        Retrieve a specific value from a secret.
        
        Args:
            secret_name (str): Name of the secret to retrieve
            key (str): Key within the secret to get the value for
            default (Any, optional): Default value if the key doesn't exist
            
        Returns:
            Any: Secret value or default
        """
        try:
            secret_data = self.get_secret(secret_name)
            return secret_data.get(key, default)
        except Exception as e:
            logger.warning(f"Error getting secret value {key} from {secret_name}: {str(e)}")
            return default


def get_secrets_manager(region_name: str = None) -> SecretsManager:
    """
    Get a Secrets Manager instance.
    
    Args:
        region_name (str, optional): AWS region name
        
    Returns:
        SecretsManager: Secrets Manager instance
    """
    return SecretsManager(region_name)


def _parse_boolean_value(value: Any) -> bool:
    """
    Parse a boolean value from either a string or boolean type.
    
    Args:
        value (Any): Value to parse as boolean
        
    Returns:
        bool: Parsed boolean value
    """
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    else:
        return bool(value)


def get_environment_secret_name() -> str:
    """
    Get the secret name based on the current environment.
    
    Returns:
        str: Secret name for the current environment
    """
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    # Map environment to secret names
    secret_names = {
        'development': 'opts-dev-secret',
        'preproduction': 'opts-preprod-secret', 
        'production': 'opts-prod-secret'
    }
    
    return secret_names.get(environment, 'opts-dev-secret')


def load_config_from_secrets() -> Dict[str, Any]:
    """
    Load configuration from AWS Secrets Manager.
    
    Returns:
        Dict[str, Any]: Configuration dictionary loaded from secrets
    """
    try:
        # Get the secret name for the current environment
        secret_name = get_environment_secret_name()
        
        # Get secrets manager instance
        secrets_manager = get_secrets_manager()
        
        # Retrieve the secret
        secret_data = secrets_manager.get_secret(secret_name)
        
        # Structure the configuration data using the same variable names as .env file
        config = {
            'archer': {
                'username': secret_data.get('OPSAPI_ARCHER_USERNAME'),
                'password': secret_data.get('OPSAPI_ARCHER_PASSWORD'),
                'instance': secret_data.get('OPSAPI_ARCHER_INSTANCE'),
                'url': secret_data.get('OPSAPI_ARCHER_URL'),
                'verify_ssl': _parse_boolean_value(secret_data.get('OPSAPI_ARCHER_VERIFY_SSL', 'true'))
            },
            'ops_portal': {
                'auth_url': secret_data.get('OPSAPI_OPS_PORTAL_AUTH_URL'),
                'item_url': secret_data.get('OPSAPI_OPS_PORTAL_ITEM_URL'),
                'client_id': secret_data.get('OPSAPI_OPS_PORTAL_CLIENT_ID'),
                'client_secret': secret_data.get('OPSAPI_OPS_PORTAL_CLIENT_SECRET'),
                'verify_ssl': _parse_boolean_value(secret_data.get('OPSAPI_OPS_PORTAL_VERIFY_SSL', 'false'))
            },
            'logging': {
                'level': secret_data.get('OPSAPI_LOGGING_LEVEL', 'INFO'),
                'file': secret_data.get('OPSAPI_LOGGING_FILE')
            }
        }
        
        # Add SSL certificate configuration if provided
        cert_file = secret_data.get('OPSAPI_OPS_PORTAL_CERT_FILE')
        key_file = secret_data.get('OPSAPI_OPS_PORTAL_KEY_FILE')
        cert_data = secret_data.get('OPSAPI_OPS_PORTAL_CERT_DATA')
        key_data = secret_data.get('OPSAPI_OPS_PORTAL_KEY_DATA')
        cert_pem = secret_data.get('OPSAPI_OPS_PORTAL_CERT_PEM')
        key_pem = secret_data.get('OPSAPI_OPS_PORTAL_KEY_PEM')
        cert_pfx = secret_data.get('OPSAPI_OPS_PORTAL_CERT_PFX')
        pfx_password = secret_data.get('OPSAPI_OPS_PORTAL_PFX_PASSWORD')
        
        if cert_pfx:
            # PKCS#12 certificate data from AWS Secrets Manager
            import base64
            # Store the binary data directly
            config['ops_portal']['cert_pfx_data'] = base64.b64decode(cert_pfx)
            if pfx_password:
                config['ops_portal']['pfx_password'] = pfx_password
            logger.info("PKCS#12 certificate loaded from AWS Secrets Manager")
        elif cert_file and key_file:
            config['ops_portal']['cert_file'] = cert_file
            config['ops_portal']['key_file'] = key_file
        elif cert_pem and key_pem:
            # Direct PEM content (preferred method)
            config['ops_portal']['cert_pem'] = cert_pem
            config['ops_portal']['key_pem'] = key_pem
        elif cert_data and key_data:
            # Base64 encoded certificate data (legacy support)
            import base64
            config['ops_portal']['cert_data'] = {
                'cert': base64.b64decode(cert_data).decode('utf-8'),
                'key': base64.b64decode(key_data).decode('utf-8')
            }
        
        
        logger.info("Configuration loaded successfully from AWS Secrets Manager")
        return config
        
    except Exception as e:
        logger.error(f"Error loading configuration from secrets: {str(e)}")
        raise

#!/usr/bin/env python3
"""
Debug script to check configuration loading
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv('.env')
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not available, assuming environment variables are already loaded")

# Import the necessary modules
from src.config import Config

def debug_config():
    """Debug configuration loading"""
    print("=" * 60)
    print("CONFIGURATION DEBUG")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    ops_env_vars = {k: v for k, v in os.environ.items() if k.startswith('OPSAPI_OPS_PORTAL')}
    for key, value in ops_env_vars.items():
        if 'SECRET' in key.upper() or 'PASSWORD' in key.upper():
            print(f"  {key}=<hidden>")
        elif 'PEM' in key.upper():
            print(f"  {key}=<{len(value)} chars>")
        else:
            print(f"  {key}={value}")
    
    # Load configuration
    print("\n2. Configuration Loading:")
    try:
        config = Config()
        print("✅ Config object created successfully")
        
        # Get all sections
        all_config = config.get_all()
        print(f"Available sections: {list(all_config.keys())}")
        
        # Get OPS Portal section
        ops_config = config.get_section('ops_portal')
        print(f"\n3. OPS Portal Configuration:")
        for key, value in ops_config.items():
            if 'secret' in key.lower() or 'password' in key.lower():
                print(f"  {key}=<hidden>")
            elif 'pem' in key.lower():
                print(f"  {key}=<{len(value) if value else 0} chars>")
            else:
                print(f"  {key}={value}")
        
        # Test OPS Portal client creation
        print(f"\n4. OPS Portal Client Configuration:")
        ops_portal_config = {
            'auth_url': ops_config.get('auth_url'),
            'item_url': ops_config.get('item_url'),
            'client_id': ops_config.get('client_id'),
            'client_secret': ops_config.get('client_secret'),
            'verify_ssl': ops_config.get('verify_ssl', 'true').lower() == 'true',
            'cert_pem': ops_config.get('cert_pem'),
            'key_pem': ops_config.get('key_pem'),
            'cert_password': ops_config.get('cert_password')
        }
        
        for key, value in ops_portal_config.items():
            if 'secret' in key.lower() or 'password' in key.lower():
                print(f"  {key}=<hidden>")
            elif 'pem' in key.lower():
                print(f"  {key}=<{len(value) if value else 0} chars>")
            else:
                print(f"  {key}={value}")
        
        # Check for missing values
        print(f"\n5. Missing Values Check:")
        required_fields = ['auth_url', 'item_url', 'client_id', 'client_secret']
        for field in required_fields:
            value = ops_portal_config.get(field)
            if not value:
                print(f"  ❌ {field} is missing or empty")
            else:
                print(f"  ✅ {field} is present")
        
        # Test client creation
        print(f"\n6. Testing OPS Portal Client Creation:")
        try:
            from src.ops_portal.api import OpsPortalClient
            client = OpsPortalClient(ops_portal_config)
            print("✅ OPS Portal client created successfully")
            print(f"  - auth_url: {client.auth_url}")
            print(f"  - item_url: {client.item_url}")
            print(f"  - client_id: {client.client_id[:8] if client.client_id else '<empty>'}...")
            print(f"  - verify_ssl: {client.verify_ssl}")
            print(f"  - cert configured: {bool(client.session.cert)}")
        except Exception as e:
            print(f"❌ Failed to create OPS Portal client: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_config()

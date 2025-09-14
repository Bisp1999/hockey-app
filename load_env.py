#!/usr/bin/env python3
"""
Environment loader utility for Hockey Pickup Manager
Loads appropriate .env file based on FLASK_ENV environment variable
"""

import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from appropriate .env file"""
    
    # Get current environment
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    # Map environment to .env file
    env_files = {
        'development': '.env.development',
        'testing': '.env.testing',
        'production': '.env.production'
    }
    
    # Load the appropriate .env file
    env_file = env_files.get(flask_env, '.env.development')
    
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
    else:
        print(f"Warning: {env_file} not found, using system environment variables")
    
    # Also try to load .env.local for local overrides (not tracked in git)
    local_env = '.env.local'
    if os.path.exists(local_env):
        load_dotenv(local_env, override=True)
        print(f"Loaded local overrides from {local_env}")

if __name__ == '__main__':
    load_environment()

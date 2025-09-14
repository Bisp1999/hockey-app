#!/usr/bin/env python3
"""
Environment validation script for Hockey Pickup Manager
Validates that all required environment variables are set correctly
"""

import os
import sys
from urllib.parse import urlparse

def validate_database_url(url):
    """Validate database URL format"""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['postgresql', 'sqlite']:
            return False, f"Unsupported database scheme: {parsed.scheme}"
        if parsed.scheme == 'postgresql' and not all([parsed.hostname, parsed.username]):
            return False, "PostgreSQL URL missing hostname or username"
        return True, "Valid"
    except Exception as e:
        return False, str(e)

def validate_email_config():
    """Validate email configuration"""
    mail_server = os.environ.get('MAIL_SERVER')
    mail_port = os.environ.get('MAIL_PORT')
    
    if not mail_server:
        return False, "MAIL_SERVER not set"
    
    try:
        port = int(mail_port) if mail_port else 587
        if port < 1 or port > 65535:
            return False, f"Invalid MAIL_PORT: {port}"
    except ValueError:
        return False, f"MAIL_PORT must be a number: {mail_port}"
    
    return True, "Valid"

def validate_security_config():
    """Validate security configuration"""
    secret_key = os.environ.get('SECRET_KEY')
    
    if not secret_key:
        return False, "SECRET_KEY not set"
    
    if secret_key in ['dev-secret-key-change-in-production', 'your-secret-key']:
        return False, "SECRET_KEY appears to be a placeholder value"
    
    if len(secret_key) < 32:
        return False, "SECRET_KEY should be at least 32 characters long"
    
    return True, "Valid"

def main():
    """Main validation function"""
    print("🔍 Hockey Pickup Manager - Environment Validation")
    print("=" * 50)
    
    errors = []
    warnings = []
    
    # Required environment variables
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'MAIL_SERVER',
        'MAIL_DEFAULT_SENDER'
    ]
    
    # Check required variables
    print("\n📋 Checking required environment variables...")
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            errors.append(f"❌ {var} is not set")
        else:
            print(f"✅ {var} is set")
    
    # Validate database URL
    print("\n🗄️  Validating database configuration...")
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        is_valid, message = validate_database_url(db_url)
        if is_valid:
            print(f"✅ Database URL: {message}")
        else:
            errors.append(f"❌ Database URL: {message}")
    
    # Validate email configuration
    print("\n📧 Validating email configuration...")
    is_valid, message = validate_email_config()
    if is_valid:
        print(f"✅ Email config: {message}")
    else:
        errors.append(f"❌ Email config: {message}")
    
    # Validate security configuration
    print("\n🔒 Validating security configuration...")
    is_valid, message = validate_security_config()
    if is_valid:
        print(f"✅ Security config: {message}")
    else:
        errors.append(f"❌ Security config: {message}")
    
    # Check optional but recommended variables
    print("\n🔧 Checking optional configuration...")
    optional_vars = {
        'UPLOAD_FOLDER': 'uploads',
        'MAX_CONTENT_LENGTH': '16777216',
        'DEFAULT_LANGUAGE': 'en',
        'SUPPORTED_LANGUAGES': 'en,fr'
    }
    
    for var, default in optional_vars.items():
        value = os.environ.get(var)
        if not value:
            warnings.append(f"⚠️  {var} not set, will use default: {default}")
        else:
            print(f"✅ {var} is set: {value}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    if errors:
        print(f"\n❌ {len(errors)} ERROR(S) FOUND:")
        for error in errors:
            print(f"   {error}")
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(S):")
        for warning in warnings:
            print(f"   {warning}")
    
    if not errors and not warnings:
        print("\n🎉 All environment variables are properly configured!")
    elif not errors:
        print("\n✅ Environment is valid (warnings can be ignored)")
    else:
        print(f"\n💥 Environment validation failed with {len(errors)} error(s)")
        print("\n📝 Please fix the errors above and run validation again.")
        sys.exit(1)

if __name__ == '__main__':
    main()

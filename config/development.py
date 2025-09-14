# Development-specific configuration overrides

import os
from datetime import timedelta
from config import Config

class DevelopmentConfig(Config):
    """Development-specific configuration overrides."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    
    # Override database URI for development
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///hockey_dev.db'
    
    # Relaxed security for development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable for API testing
    
    # CORS for frontend development
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://127.0.0.1:3000'
    ]
    
    # Development email settings (MailHog)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # CORS (allow all origins in development)
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    
    # Rate limiting (disabled in development)
    RATELIMIT_ENABLED = False

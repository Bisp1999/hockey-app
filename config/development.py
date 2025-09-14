# Development-specific configuration overrides

import os
from datetime import timedelta

class DevelopmentConfig:
    """Development configuration settings"""
    
    # Flask settings
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    
    # Security (relaxed for development)
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = False
    
    # Email (MailHog)
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = True
    
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

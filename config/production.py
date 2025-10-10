# Production-specific configuration overrides

import os
from datetime import timedelta
from .base import Config 

class ProductionConfig:
    """Production configuration settings"""
    
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security (strict for production)
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'
    
    # Email
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = False
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # CORS (restrict to actual domain)
    CORS_ORIGINS = []  # Set in environment variables
    
    # Rate limiting (enabled in production)
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Production specific
    PREFERRED_URL_SCHEME = 'https'
    
    # SSL/TLS
    SSL_REDIRECT = True

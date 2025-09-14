# Testing-specific configuration overrides

import os
from datetime import timedelta

class TestingConfig:
    """Testing configuration settings"""
    
    # Flask settings
    DEBUG = False
    TESTING = True
    
    # Database (in-memory SQLite for speed)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security (disabled for testing)
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Email (suppressed in tests)
    MAIL_SUPPRESS_SEND = True
    MAIL_DEBUG = False
    
    # Logging
    LOG_LEVEL = 'WARNING'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)
    
    # File uploads (smaller for tests)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB
    
    # CORS (allow test origins)
    CORS_ORIGINS = ['http://localhost:3000']
    
    # Rate limiting (disabled in testing)
    RATELIMIT_ENABLED = False
    
    # Testing specific
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    SERVER_NAME = 'localhost.localdomain'

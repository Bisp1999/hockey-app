"""
Application configuration including database and email settings.
"""
import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://hockey_user:hockey_pass@localhost/hockey_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME'))
    MAIL_MAX_EMAILS = os.getenv('MAIL_MAX_EMAILS')
    MAIL_ASCII_ATTACHMENTS = os.getenv('MAIL_ASCII_ATTACHMENTS', 'False').lower() == 'true'
    
    # Session configuration
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'hockey:'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Multi-tenant configuration
    TENANT_URL_SUBDOMAIN_ENABLED = os.environ.get('TENANT_URL_SUBDOMAIN_ENABLED', 'True').lower() in ['true', '1', 'yes']
    TENANT_URL_PATH_ENABLED = os.environ.get('TENANT_URL_PATH_ENABLED', 'False').lower() in ['true', '1', 'yes']
    
    # File upload configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 16 * 1024 * 1024)  # 16MB default
    
    # Internationalization
    DEFAULT_LANGUAGE = os.environ.get('DEFAULT_LANGUAGE') or 'en'
    SUPPORTED_LANGUAGES = os.environ.get('SUPPORTED_LANGUAGES', 'en,fr').split(',')
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://hockey_user:hockey_pass@localhost/hockey_dev'
    SESSION_COOKIE_SECURE = False
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    MAIL_SUPPRESS_SEND = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    CORS_ORIGINS = [
        'https://myhockeyapp.netlify.app',
        'https://app-production-bdef.up.railway.app'
    ]
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_DOMAIN = '.pickupteams.com'
    PREFERRED_URL_SCHEME = 'https'
    SSL_REDIRECT = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

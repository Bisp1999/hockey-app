# Configuration package initialization

from .development import DevelopmentConfig
from .testing import TestingConfig
from .production import ProductionConfig

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

def get_config(env_name='development'):
    """Get configuration class based on environment name"""
    return config.get(env_name, DevelopmentConfig)

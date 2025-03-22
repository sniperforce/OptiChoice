"""
Centralized configuration module for the MCDM system.

This module contains all necessary configurations for the system operation,
from directory paths to default parameters for MCDM methods.
"""
import os
import logging
from datetime import timedelta


class BaseConfig:
    
    # Application information
    APP_NAME = "OptiChoice"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Software for Multi-Criteria Decision Making"
    
    # Directories
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    # Ensure necessary directories exist
    for directory in [DATA_DIR, UPLOAD_FOLDER, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # Logging
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = os.path.join(LOG_DIR, "mcdm.log")
    
    # API
    API_PREFIX = "/api"
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    
    # Security
    SECRET_KEY = "change_this_to_a_random_secret_key"  # Change in production
    JWT_SECRET_KEY = "change_this_to_a_random_jwt_key"  # Change in production
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Files
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'pdf'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Persistence
    PROJECTS_DIR = os.path.join(DATA_DIR, "projects")
    
    # User interface
    ITEMS_PER_PAGE = 20
    DEFAULT_LANGUAGE = "es"
    
    # MCDM methods configurations
    MCDM_METHODS = {
        "TOPSIS": {
            "normalization_method": "vector",
            "normalize_matrix": True,
            "distance_metric": "euclidean",
            "apply_weights_after_normalization": True,
            "consider_criteria_type": True
        },
        "AHP": {
            "consistency_ratio_threshold": 0.1,
            "weight_calculation_method": "eigenvector",
            "use_pairwise_comparison_for_alternatives": True,
            "normalize_before_comparison": True,
            "normalization_method": "minmax"
        },
        "ELECTRE": {
            "variant": "I",
            "concordance_threshold": 0.7,
            "discordance_threshold": 0.3,
            "normalization_method": "minmax",
            "normalize_matrix": True,
            "scoring_method": "net_flow"
        },
        "PROMETHEE": {
            "variant": "II",
            "default_preference_function": "v-shape",
            "normalization_method": "minmax",
            "normalize_matrix": True
        }
    }
    
    # Visualization configurations
    CHARTS = {
        "default_colors": [
            "#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
            "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"
        ],
        "bar_chart": {
            "width": 800,
            "height": 500,
            "margin": {"top": 30, "right": 30, "bottom": 70, "left": 60}
        },
        "radar_chart": {
            "width": 500,
            "height": 500,
            "margin": {"top": 50, "right": 50, "bottom": 50, "left": 50}
        },
        "heatmap": {
            "width": 800,
            "height": 500,
            "margin": {"top": 30, "right": 30, "bottom": 70, "left": 60},
            "colors": ["#f7fbff", "#08306b"]
        }
    }


class DevelopmentConfig(BaseConfig):
    """Configuration for development environment."""
    
    DEBUG = True
    TESTING = False
    
    # More detailed logging
    LOG_LEVEL = logging.DEBUG


class TestingConfig(BaseConfig):
    """Configuration for testing environment."""
    
    DEBUG = False
    TESTING = True
    
    # Test directories
    DATA_DIR = os.path.join(BaseConfig.BASE_DIR, "test_data")
    UPLOAD_FOLDER = os.path.join(BaseConfig.BASE_DIR, "test_uploads")
    LOG_DIR = os.path.join(BaseConfig.BASE_DIR, "test_logs")
    
    # Ensure necessary directories exist
    for directory in [DATA_DIR, UPLOAD_FOLDER, LOG_DIR]:
        os.makedirs(directory, exist_ok=True)
    
    # Test database
    PROJECTS_DIR = os.path.join(DATA_DIR, "projects")


class ProductionConfig(BaseConfig):
    """Configuration for production environment."""
    
    DEBUG = False
    TESTING = False
    
    # More restrictive logging
    LOG_LEVEL = logging.WARNING
    
    # Enhanced security
    # In production, these keys should be set through environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY', BaseConfig.SECRET_KEY)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', BaseConfig.JWT_SECRET_KEY)


# Configuration according to environment
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

# Active configuration
active_config = config_by_name[os.environ.get('FLASK_ENV', 'development')]


# Global access to configuration
class Config(object):
    def __getattr__(name):
        return getattr(active_config, name)
    
    @classmethod
    def get(cls, name, default=None):
        return getattr(active_config, name, default)
    
    @classmethod
    def set_env(cls, env_name):
        global active_config
        
        if env_name not in config_by_name:
            raise ValueError(f"Invalid configuration environment: {env_name}")
            
        active_config = config_by_name[env_name]
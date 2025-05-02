# backend/tests/unit/test_config.py
import os
import pytest
from config import BaseConfig, DevelopmentConfig, TestingConfig, ProductionConfig, Config, config_by_name, active_config

class TestConfig:
    
    def test_base_config(self):
        """Test that BaseConfig has the expected attributes."""
        assert BaseConfig.APP_NAME == "OptiChoice"
        assert BaseConfig.APP_VERSION == "1.0.0"
        assert hasattr(BaseConfig, 'BASE_DIR')
        assert hasattr(BaseConfig, 'LOG_LEVEL')
        assert hasattr(BaseConfig, 'MCDM_METHODS')
        assert hasattr(BaseConfig, 'CHARTS')
    
    def test_development_config(self):
        """Test that DevelopmentConfig inherits from BaseConfig and overrides attributes."""
        assert issubclass(DevelopmentConfig, BaseConfig)
        assert DevelopmentConfig.DEBUG is True
        assert DevelopmentConfig.TESTING is False
        
    def test_testing_config(self):
        """Test that TestingConfig inherits from BaseConfig and overrides attributes."""
        assert issubclass(TestingConfig, BaseConfig)
        assert TestingConfig.DEBUG is False
        assert TestingConfig.TESTING is True
        assert TestingConfig.DATA_DIR != BaseConfig.DATA_DIR
        
    def test_production_config(self):
        """Test that ProductionConfig inherits from BaseConfig and overrides attributes."""
        assert issubclass(ProductionConfig, BaseConfig)
        assert ProductionConfig.DEBUG is False
        assert ProductionConfig.TESTING is False
        
    def test_config_by_name(self):
        """Test that config_by_name returns the correct config class."""
        assert config_by_name['development'] == DevelopmentConfig
        assert config_by_name['testing'] == TestingConfig
        assert config_by_name['production'] == ProductionConfig
        
    def test_config_accessor(self):
        """Test the Config class accessor methods."""
        # Test getting an attribute using get() method
        assert Config.get('APP_NAME') == "OptiChoice"
        
        # Test getting an attribute with default value
        assert Config.get('NON_EXISTENT', 'default_value') == 'default_value'
        
    def test_config_env_switching(self):
        """Test switching between environments."""
        original_env = os.environ.get('FLASK_ENV', 'development')
        
        # Set environment to testing
        Config.set_env('testing')
        assert Config.get('TESTING') is True
        assert Config.get('DEBUG') is False
        
        # Set environment to production
        Config.set_env('production')
        assert Config.get('TESTING') is False
        assert Config.get('DEBUG') is False
        
        # Set environment to development
        Config.set_env('development')
        assert Config.get('TESTING') is False
        assert Config.get('DEBUG') is True
        
        # Test invalid environment
        with pytest.raises(ValueError):
            Config.set_env('invalid_env')
            
        # Restore original environment
        Config.set_env(original_env)
            
    def test_mcdm_method_settings(self):
        """Test MCDM method specific settings."""
        # Test that all required methods are defined
        methods = Config.get('MCDM_METHODS')
        assert 'TOPSIS' in methods
        assert 'AHP' in methods
        assert 'ELECTRE' in methods
        assert 'PROMETHEE' in methods
        
        # Test method specific settings
        assert 'normalization_method' in methods['TOPSIS']
        assert 'consistency_ratio_threshold' in methods['AHP']
        assert 'variant' in methods['ELECTRE']
        assert 'default_preference_function' in methods['PROMETHEE']
        
    def test_directory_creation(self):
        """Test that necessary directories are created."""
        assert os.path.exists(BaseConfig.DATA_DIR)
        assert os.path.exists(BaseConfig.UPLOAD_FOLDER)
        assert os.path.exists(BaseConfig.LOG_DIR)
        
    def test_chart_settings(self):
        """Test chart configuration settings."""
        charts = Config.get('CHARTS')
        assert 'default_colors' in charts
        assert 'bar_chart' in charts
        assert 'radar_chart' in charts
        assert 'heatmap' in charts
        
        # Test specific chart settings
        assert 'width' in charts['bar_chart']
        assert 'height' in charts['bar_chart']
        assert 'margin' in charts['bar_chart']
    
    def test_active_config(self):
        """Test the active configuration is correctly set."""
        # By default it should be development
        Config.set_env('development')
        assert active_config == DevelopmentConfig

import pytest
from unittest.mock import Mock, patch

from application.methods.method_factory import MCDMMethodFactory
from application.methods.method_interface import MCDMMethodInterface
from application.methods.topsis import TOPSISMethod
from application.methods.ahp import AHPMethod
from application.methods.electre import ELECTREMethod
from application.methods.promethee import PROMETHEEMethod
from utils.exceptions import ValidationError

class TestMCDMMethodFactory:
    
    def test_create_method_topsis(self):
        """Test creating TOPSIS method."""
        method = MCDMMethodFactory.create_method("TOPSIS")
        assert isinstance(method, TOPSISMethod)
        assert method.name == "TOPSIS"
    
    def test_create_method_ahp(self):
        """Test creating AHP method."""
        method = MCDMMethodFactory.create_method("AHP")
        assert isinstance(method, AHPMethod)
        assert method.name == "AHP"
    
    def test_create_method_electre(self):
        """Test creating ELECTRE method."""
        method = MCDMMethodFactory.create_method("ELECTRE")
        assert isinstance(method, ELECTREMethod)
        assert method.name == "ELECTRE"
    
    def test_create_method_promethee(self):
        """Test creating PROMETHEE method."""
        method = MCDMMethodFactory.create_method("PROMETHEE")
        assert isinstance(method, PROMETHEEMethod)
        assert method.name == "PROMETHEE"
    
    def test_create_method_case_insensitive(self):
        """Test creating method with different case."""
        method1 = MCDMMethodFactory.create_method("topsis")
        method2 = MCDMMethodFactory.create_method("TOPSIS")
        method3 = MCDMMethodFactory.create_method("Topsis")
        
        assert isinstance(method1, TOPSISMethod)
        assert isinstance(method2, TOPSISMethod)
        assert isinstance(method3, TOPSISMethod)
    
    def test_create_method_with_alias(self):
        """Test creating method using alias name."""
        # Probar con el alias completo de TOPSIS
        method = MCDMMethodFactory.create_method("TECHNIQUE FOR ORDER OF PREFERENCE BY SIMILARITY TO IDEAL SOLUTION")
        assert isinstance(method, TOPSISMethod)
        
        # Probar con el alias de AHP
        method = MCDMMethodFactory.create_method("ANALYTIC HIERARCHY PROCESS")
        assert isinstance(method, AHPMethod)
    
    def test_create_method_invalid_name(self):
        """Test error when creating method with invalid name."""
        with pytest.raises(ValidationError) as exc_info:
            MCDMMethodFactory.create_method("INVALID_METHOD")
        
        assert "MCDM method not available" in str(exc_info.value)
        assert "Available methods" in str(exc_info.value.errors[0])
    
    def test_get_available_methods(self):
        """Test getting list of available methods."""
        methods = MCDMMethodFactory.get_available_methods()
        
        assert isinstance(methods, list)
        assert "TOPSIS" in methods
        assert "AHP" in methods
        assert "ELECTRE" in methods
        assert "PROMETHEE" in methods
        assert len(methods) >= 4  # At least these four methods
    
    def test_get_method_info(self):
        """Test getting method information."""
        info = MCDMMethodFactory.get_method_info("TOPSIS")
        
        assert info['name'] == "TOPSIS"
        assert 'full_name' in info
        assert 'description' in info
        assert 'default_parameters' in info
        assert isinstance(info['default_parameters'], dict)
    
    def test_get_method_info_invalid_name(self):
        """Test error when getting info for invalid method."""
        with pytest.raises(ValidationError) as exc_info:
            MCDMMethodFactory.get_method_info("INVALID_METHOD")
        
        assert "MCDM method not available" in str(exc_info.value)
    
    def test_register_method(self):
        """Test registering a new method."""
        # Create a mock method class that implements the interface
        class MockMethod(MCDMMethodInterface):
            @property
            def name(self):
                return "MOCK"
            
            @property
            def full_name(self):
                return "Mock Method"
            
            @property
            def description(self):
                return "Test method"
            
            def get_default_parameters(self):
                return {}
            
            def validate_parameters(self, parameters):
                return True
            
            def execute(self, decision_matrix, parameters=None):
                pass
        
        # Save original methods to restore later
        original_methods = MCDMMethodFactory._methods.copy()
        
        try:
            # Register the new method
            MCDMMethodFactory.register_method("MOCK", MockMethod)
            
            # Verify it was registered
            assert "MOCK" in MCDMMethodFactory._methods
            assert MCDMMethodFactory._methods["MOCK"] == MockMethod
            
            # Test creating the method
            method = MCDMMethodFactory.create_method("MOCK")
            assert isinstance(method, MockMethod)
            assert method.name == "MOCK"
            
        finally:
            # Restore original methods
            MCDMMethodFactory._methods = original_methods
    
    def test_register_method_invalid_class(self):
        """Test error when registering class that doesn't implement interface."""
        class InvalidMethod:
            pass
        
        with pytest.raises(ValueError) as exc_info:
            MCDMMethodFactory.register_method("INVALID", InvalidMethod)
        
        assert "does not implement the MCDMMethodInterface" in str(exc_info.value)
    
    def test_register_method_duplicate_name(self):
        """Test error when registering method with existing name."""
        # Create a mock method class
        class MockMethod(MCDMMethodInterface):
            @property
            def name(self):
                return "TOPSIS"
            
            @property
            def full_name(self):
                return "Mock TOPSIS"
            
            @property
            def description(self):
                return "Test method"
            
            def get_default_parameters(self):
                return {}
            
            def validate_parameters(self, parameters):
                return True
            
            def execute(self, decision_matrix, parameters=None):
                pass
        
        with pytest.raises(ValueError) as exc_info:
            MCDMMethodFactory.register_method("TOPSIS", MockMethod)
        
        assert "A method with the name 'TOPSIS' is already registered" in str(exc_info.value)
    
    def test_create_method_with_params(self):
        """Test creating method with parameters."""
        # Mock the validate_parameters method
        with patch.object(TOPSISMethod, 'validate_parameters', return_value=True):
            params = {'normalization_method': 'vector'}
            method = MCDMMethodFactory.create_method_with_params("TOPSIS", params)
            
            assert isinstance(method, TOPSISMethod)
            # The validate_parameters method should have been called
            method.validate_parameters.assert_called_once_with(params)
    
    def test_create_method_with_params_invalid(self):
        """Test error when parameters are invalid."""
        # Mock the validate_parameters method to return False
        with patch.object(TOPSISMethod, 'validate_parameters', return_value=False):
            params = {'invalid_param': 'value'}
            
            with pytest.raises(ValidationError) as exc_info:
                MCDMMethodFactory.create_method_with_params("TOPSIS", params)
            
            assert "Invalid parameters for the TOPSIS method" in str(exc_info.value)
    
    def test_create_method_with_params_no_params(self):
        """Test creating method without parameters."""
        method = MCDMMethodFactory.create_method_with_params("TOPSIS", None)
        assert isinstance(method, TOPSISMethod)
    
    def test_original_methods_not_modified(self):
        """Test that original methods dictionary is not modified during tests."""
        original_methods = {"TOPSIS": TOPSISMethod, "AHP": AHPMethod, 
                          "ELECTRE": ELECTREMethod, "PROMETHEE": PROMETHEEMethod}
        
        assert MCDMMethodFactory._methods == original_methods
        
        # Verify aliases are present
        expected_aliases = {
            "TECHNIQUE FOR ORDER OF PREFERENCE BY SIMILARITY TO IDEAL SOLUTION": "TOPSIS",
            "ANALYTIC HIERARCHY PROCESS": "AHP",
            "ELIMINATION ET CHOIX TRADUISANT LA REALITÉ": "ELECTRE",
            "ELIMINATION AND CHOICE EXPRESSING REALITY": "ELECTRE",
            "PREFERENCE RANKING ORGANIZATION METHOD FOR ENRICHMENT OF EVALUATIONS": "PROMETHEE"
        }
        
        for alias, method_name in expected_aliases.items():
            assert MCDMMethodFactory._aliases.get(alias) == method_name
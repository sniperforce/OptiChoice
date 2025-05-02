import pytest
import numpy as np

from application.methods.promethee import PROMETHEEMethod
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from utils.exceptions import MethodError, ValidationError

class TestPROMETHEEMethod:
    
    @pytest.fixture
    def promethee_method(self):
        """Fixture that provides a PROMETHEE method instance."""
        return PROMETHEEMethod()
    
    @pytest.fixture
    def sample_decision_matrix(self):
        """Fixture providing a sample decision matrix for testing."""
        alternatives = [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3"),
            Alternative(id="alt4", name="Alternative 4")
        ]
        
        criteria = [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE, weight=0.4),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE, weight=0.3),
            Criteria(id="crit3", name="Criteria 3", optimization_type=OptimizationType.MAXIMIZE, weight=0.3)
        ]
        
        values = np.array([
            [8.0, 2.0, 7.0],
            [6.0, 4.0, 8.0],
            [7.0, 3.0, 6.0],
            [9.0, 2.5, 7.5]
        ])
        
        return DecisionMatrix(
            name="Test Matrix",
            alternatives=alternatives,
            criteria=criteria,
            values=values
        )
    
    def test_promethee_properties(self, promethee_method):
        """Test that PROMETHEE method has correct properties."""
        assert promethee_method.name == "PROMETHEE"
        assert promethee_method.full_name == "Preference Ranking Organization Method for Enrichment of Evaluations"
        assert isinstance(promethee_method.description, str)
        assert len(promethee_method.description) > 0
    
    def test_preference_functions(self, promethee_method):
        """Test that all preference functions are correctly defined."""
        expected_functions = {
            "usual": 1,
            "u-shape": 2,
            "v-shape": 3,
            "level": 4,
            "v-shape-indifference": 5,
            "gaussian": 6
        }
        
        assert promethee_method.PREFERENCE_FUNCTIONS == expected_functions
    
    def test_default_parameters(self, promethee_method):
        """Test that default parameters are correctly set."""
        params = promethee_method.get_default_parameters()
        
        assert params['variant'] == 'II'
        assert params['default_preference_function'] == 'v-shape'
        assert params['preference_functions'] is None
        assert params['p_thresholds'] is None
        assert params['q_thresholds'] is None
        assert params['s_thresholds'] is None
        assert params['normalization_method'] == 'minimax'
        assert params['normalize_matrix'] == True
    
    def test_validate_parameters_valid(self, promethee_method):
        """Test parameter validation with valid parameters."""
        valid_params = {
            'variant': 'II',
            'default_preference_function': 'v-shape',
            'preference_functions': {'crit1': 'v-shape', 'crit2': 'u-shape'},
            'p_thresholds': {'crit1': 0.5, 'crit2': 0.3},
            'q_thresholds': {'crit1': 0.2, 'crit2': 0.1},
            's_thresholds': {'crit1': 0.3}
        }
        
        assert promethee_method.validate_parameters(valid_params) == True
    
    def test_validate_parameters_invalid_variant(self, promethee_method):
        """Test parameter validation with invalid variant."""
        invalid_params = {
            'variant': 'III'  # Invalid variant
        }
        
        assert promethee_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_invalid_preference_function(self, promethee_method):
        """Test parameter validation with invalid preference function."""
        invalid_params = {
            'default_preference_function': 'invalid_function'
        }
        
        assert promethee_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_threshold_consistency(self, promethee_method):
        """Test parameter validation for threshold consistency (p >= q)."""
        invalid_params = {
            'p_thresholds': {'crit1': 0.2},
            'q_thresholds': {'crit1': 0.3}  # q > p should be invalid
        }
        
        assert promethee_method.validate_parameters(invalid_params) == False
    
    def test_execute_promethee_ii(self, promethee_method, sample_decision_matrix):
        """Test PROMETHEE II execution."""
        params = {
            'variant': 'II',
            'default_preference_function': 'v-shape',
            'p_thresholds': {'crit1': 0.5, 'crit2': 0.3, 'crit3': 0.4}
        }
        
        result = promethee_method.execute(sample_decision_matrix, params)
        
        assert result.method_name == "PROMETHEE-II"
        assert len(result.alternative_ids) == 4
        assert len(result.scores) == 4
        assert len(result.rankings) == 4
        
        # Verify metadata contains PROMETHEE specific information
        metadata = result.metadata
        assert 'positive_flow' in metadata
        assert 'negative_flow' in metadata
        assert 'net_flow' in metadata
        assert 'preference_matrix' in metadata
    
    def test_execute_promethee_i(self, promethee_method, sample_decision_matrix):
        """Test PROMETHEE I execution."""
        params = {
            'variant': 'I',
            'default_preference_function': 'v-shape',
            'p_thresholds': {'crit1': 0.5, 'crit2': 0.3, 'crit3': 0.4}
        }
        
        result = promethee_method.execute(sample_decision_matrix, params)
        
        assert result.method_name == "PROMETHEE-I"
        
        # Check for PROMETHEE I specific metadata
        metadata = result.metadata
        assert 'outranking_matrix' in metadata
        assert 'incomparabilities' in metadata
    
    def test_different_preference_functions(self, promethee_method, sample_decision_matrix):
        """Test execution with different preference functions."""
        function_types = ['usual', 'u-shape', 'v-shape', 'level', 'v-shape-indifference', 'gaussian']
        
        for func_type in function_types:
            params = {
                'variant': 'II',
                'default_preference_function': func_type,
                'q_thresholds': {'crit1': 0.1, 'crit2': 0.1, 'crit3': 0.1},
                'p_thresholds': {'crit1': 0.5, 'crit2': 0.5, 'crit3': 0.5},
                's_thresholds': {'crit1': 0.3, 'crit2': 0.3, 'crit3': 0.3}
            }
            
            result = promethee_method.execute(sample_decision_matrix, params)
            assert result is not None
            assert len(result.scores) == 4
    
    def test_preference_function_calculation(self, promethee_method):
        """Test individual preference function calculations."""
        # Test usual function
        assert promethee_method._apply_preference_function(0.5, 1, 0.0, 0.0, 0.0) == 1.0
        assert promethee_method._apply_preference_function(-0.1, 1, 0.0, 0.0, 0.0) == 0.0
        
        # Test U-shape (quasi)
        assert promethee_method._apply_preference_function(0.5, 2, 0.0, 0.2, 0.0) == 1.0
        assert promethee_method._apply_preference_function(0.1, 2, 0.0, 0.2, 0.0) == 0.0
        
        # Test V-shape (linear)
        assert promethee_method._apply_preference_function(0.5, 3, 1.0, 0.0, 0.0) == 0.5
        assert promethee_method._apply_preference_function(1.5, 3, 1.0, 0.0, 0.0) == 1.0
        
        # Test level function
        assert promethee_method._apply_preference_function(0.1, 4, 0.5, 0.2, 0.0) == 0.0
        assert promethee_method._apply_preference_function(0.3, 4, 0.5, 0.2, 0.0) == 0.5
        assert promethee_method._apply_preference_function(0.6, 4, 0.5, 0.2, 0.0) == 1.0
    
    def test_flow_calculation(self, promethee_method, sample_decision_matrix):
        """Test preference flow calculations."""
        result = promethee_method.execute(sample_decision_matrix)
        
        metadata = result.metadata
        positive_flow = np.array(metadata['positive_flow'])
        negative_flow = np.array(metadata['negative_flow'])
        net_flow = np.array(metadata['net_flow'])
        
        # Net flow should be positive - negative
        assert np.allclose(net_flow, positive_flow - negative_flow)
        
        # Flows should be normalized
        assert np.all(positive_flow >= 0)
        assert np.all(positive_flow <= 1)
        assert np.all(negative_flow >= 0)
        assert np.all(negative_flow <= 1)
    
    def test_incomparability_detection(self, promethee_method, sample_decision_matrix):
        """Test incomparability detection in PROMETHEE I."""
        params = {
            'variant': 'I',
            'default_preference_function': 'v-shape'
        }
        
        result = promethee_method.execute(sample_decision_matrix, params)
        metadata = result.metadata
        
        # PROMETHEE I should detect incomparabilities
        if 'incomparabilities' in metadata:
            incomparabilities = metadata['incomparabilities']
            # Each incomparability should be a tuple of two indices
            for i, j in incomparabilities:
                assert isinstance(i, int)
                assert isinstance(j, int)
                assert i != j
    
    def test_error_handling_missing_parameters(self, promethee_method, sample_decision_matrix):
        """Test error handling when parameters are missing."""
        params = None  # No parameters provided
        
        # Should use default parameters without error
        result = promethee_method.execute(sample_decision_matrix, params)
        assert result is not None
    
    def test_error_handling_invalid_matrix(self, promethee_method):
        """Test error handling with invalid decision matrix."""
        with pytest.raises(MethodError):
            promethee_method.execute(None)
    
    def test_error_handling_invalid_threshold_values(self, promethee_method, sample_decision_matrix):
        """Test error handling with negative threshold values."""
        params = {
            'q_thresholds': {'crit1': -0.1}  # Negative threshold
        }
        
        with pytest.raises((ValidationError, MethodError)):
            promethee_method.execute(sample_decision_matrix, params)
    
    def test_normalization_effect(self, promethee_method, sample_decision_matrix):
        """Test the effect of normalization on results."""
        params_with_norm = {
            'normalize_matrix': True,
            'normalization_method': 'minimax'
        }
        
        params_without_norm = {
            'normalize_matrix': False
        }
        
        result_with_norm = promethee_method.execute(sample_decision_matrix, params_with_norm)
        result_without_norm = promethee_method.execute(sample_decision_matrix, params_without_norm)
        
        # Results might differ when normalization is applied
        # This test verifies that the method can handle both cases
        assert result_with_norm is not None
        assert result_without_norm is not None
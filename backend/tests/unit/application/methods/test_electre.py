import pytest
import numpy as np

from application.methods.electre import ELECTREMethod
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from utils.exceptions import MethodError, ValidationError

class TestELECTREMethod:
    
    @pytest.fixture
    def electre_method(self):
        """Fixture providing an ELECTRE method instance."""
        return ELECTREMethod()
    
    @pytest.fixture
    def sample_decision_matrix(self):
        """Fixture providing a sample decision matrix for testing."""
        alternatives = [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
        ]
        
        criteria = [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE, weight=0.4),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE, weight=0.3),
            Criteria(id="crit3", name="Criteria 3", optimization_type=OptimizationType.MAXIMIZE, weight=0.3)
        ]
        
        values = np.array([
            [8.0, 2.0, 7.0],
            [6.0, 4.0, 8.0],
            [7.0, 3.0, 6.0]
        ])
        
        return DecisionMatrix(
            name="Test Matrix",
            alternatives=alternatives,
            criteria=criteria,
            values=values
        )
    
    def test_electre_properties(self, electre_method):
        """Test that ELECTRE method has correct properties."""
        assert electre_method.name == "ELECTRE"
        assert electre_method.full_name == "Elimination Et Choix Traduisant la Realité"
        assert isinstance(electre_method.description, str)
        assert len(electre_method.description) > 0
    
    def test_default_parameters(self, electre_method):
        """Test that default parameters are correctly set."""
        params = electre_method.get_default_parameters()
        
        assert params['variant'] == 'I'
        assert params['concordance_threshold'] == 0.7
        assert params['discordance_threshold'] == 0.3
        assert params['normalization_method'] == 'minimax'
        assert params['normalize_matrix'] == True
        assert params['scoring_method'] == 'net_flow'
    
    def test_validate_parameters_valid(self, electre_method):
        """Test parameter validation with valid parameters."""
        valid_params = {
            'variant': 'I',
            'concordance_threshold': 0.6,
            'discordance_threshold': 0.4,
            'normalization_method': 'minimax',
            'scoring_method': 'net_flow'
        }
        
        assert electre_method.validate_parameters(valid_params) == True
    
    def test_validate_parameters_invalid_variant(self, electre_method):
        """Test parameter validation with invalid variant."""
        invalid_params = {
            'variant': 'IV'  # Invalid variant
        }
        
        assert electre_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_invalid_concordance_threshold(self, electre_method):
        """Test parameter validation with invalid concordance threshold."""
        invalid_params = {
            'concordance_threshold': 1.5  # Must be between 0.5 and 1.0
        }
        
        assert electre_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_invalid_scoring_method(self, electre_method):
        """Test parameter validation with invalid scoring method."""
        invalid_params = {
            'scoring_method': 'invalid_method'
        }
        
        assert electre_method.validate_parameters(invalid_params) == False
    
    def test_execute_electre_i(self, electre_method, sample_decision_matrix):
        """Test ELECTRE I execution."""
        params = {
            'variant': 'I',
            'concordance_threshold': 0.65,
            'discordance_threshold': 0.35
        }
        
        result = electre_method.execute(sample_decision_matrix, params)
        
        assert result.method_name == "ELECTRE-I"
        assert len(result.alternative_ids) == 3
        assert len(result.scores) == 3
        assert len(result.rankings) == 3
        
        # Verify metadata contains ELECTRE I specific information
        metadata = result.metadata
        assert 'outranking_matrix' in metadata
        assert 'dominance_matrix' in metadata
        assert 'non_dominated_alternatives' in metadata
    
    def test_execute_electre_iii(self, electre_method, sample_decision_matrix):
        """Test ELECTRE III execution."""
        params = {
            'variant': 'III',
            'preference_thresholds': {'crit1': 0.5, 'crit2': 0.3, 'crit3': 0.4},
            'indifference_thresholds': {'crit1': 0.2, 'crit2': 0.1, 'crit3': 0.15},
            'veto_thresholds': {'crit1': 1.0, 'crit2': 0.8, 'crit3': 0.9}
        }
        
        result = electre_method.execute(sample_decision_matrix, params)
        
        assert result.method_name == "ELECTRE-III"
        assert len(result.alternative_ids) == 3
        
        # Verify metadata contains ELECTRE III specific information
        metadata = result.metadata
        assert 'credibility_matrix' in metadata
        assert 'ascending_distillation' in metadata
        assert 'descending_distillation' in metadata
        assert 'net_flows' in metadata
    
    def test_electre_iii_threshold_validation(self, electre_method):
        """Test ELECTRE III threshold validation (preference > indifference)."""
        params = {
            'variant': 'III',
            'preference_thresholds': {'crit1': 0.1},
            'indifference_thresholds': {'crit1': 0.3}  # Should be less than preference
        }
        
        assert electre_method.validate_parameters(params) == False
    
    def test_execute_with_different_scoring_methods(self, electre_method, sample_decision_matrix):
        """Test execution with different scoring methods."""
        scoring_methods = ['net_flow', 'pure_dominance', 'mixed']
        
        for method in scoring_methods:
            params = {
                'variant': 'I',
                'scoring_method': method
            }
            
            result = electre_method.execute(sample_decision_matrix, params)
            assert result is not None
            assert result.parameters['scoring_method'] == method
    
    def test_concordance_discordance_calculation(self, electre_method, sample_decision_matrix):
        """Test concordance and discordance matrix calculations."""
        result = electre_method.execute(sample_decision_matrix, {'variant': 'I'})
        
        # Verify that matrices are calculated correctly
        metadata = result.metadata
        outranking_matrix = np.array(metadata['outranking_matrix'])
        
        # Outranking matrix should be square
        n_alternatives = len(sample_decision_matrix.alternative)
        assert outranking_matrix.shape == (n_alternatives, n_alternatives)
        
        # Diagonal should be zeros (alternative doesn't outrank itself)
        assert np.all(np.diag(outranking_matrix) == 0)
    
    def test_error_handling_invalid_variant(self, electre_method, sample_decision_matrix):
        """Test error handling with invalid variant."""
        params = {'variant': 'IV'}
        
        with pytest.raises(MethodError):
            electre_method.execute(sample_decision_matrix, params)
    
    def test_error_handling_missing_thresholds(self, electre_method, sample_decision_matrix):
        """Test error handling with missing thresholds for ELECTRE III."""
        params = {
            'variant': 'III'
            # Missing thresholds
        }
        
        result = electre_method.execute(sample_decision_matrix, params)
        assert result is not None  # Should use default thresholds
    
    @pytest.fixture
    def sample_decision_matrix_for_normalization(self):
        """Fixture providing a decision matrix where normalization has clear effect."""
        alternatives = [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
        ]
        
        criteria = [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE, weight=0.4),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE, weight=0.3),
            Criteria(id="crit3", name="Criteria 3", optimization_type=OptimizationType.MAXIMIZE, weight=0.3)
        ]
        
        # Valores con diferentes escalas para que la normalización tenga un efecto claro
        values = np.array([
            [100.0, 2.0, 0.7],
            [60.0, 4.0, 0.8],
            [80.0, 3.0, 0.6]
        ])
        
        return DecisionMatrix(
            name="Test Matrix for Normalization",
            alternatives=alternatives,
            criteria=criteria,
            values=values
        )

    def test_normalization_application(self, electre_method, sample_decision_matrix_for_normalization):
        """Test that normalization is correctly applied when requested."""
        params_with_norm = {
            'normalize_matrix': True,
            'normalization_method': 'minimax'
        }
        
        params_without_norm = {
            'normalize_matrix': False
        }
        
        result_with_norm = electre_method.execute(sample_decision_matrix_for_normalization, params_with_norm)
        result_without_norm = electre_method.execute(sample_decision_matrix_for_normalization, params_without_norm)
        
        # Results should be different when normalization is applied
        assert not np.array_equal(result_with_norm.scores, result_without_norm.scores)
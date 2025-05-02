import pytest
import numpy as np

from application.methods.ahp import AHPMethod
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from utils.exceptions import MethodError, ValidationError

class TestAHPMethod:
    
    @pytest.fixture
    def ahp_method(self):
        """Fixture providing an AHP method instance."""
        return AHPMethod()
    
    @pytest.fixture
    def sample_decision_matrix(self):
        """Fixture providing a sample decision matrix for testing."""
        # Crear alternativas
        alternatives = [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
        ]
        
        # Crear criterios
        criteria = [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE, weight=1.0),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE, weight=1.0),
            Criteria(id="crit3", name="Criteria 3", optimization_type=OptimizationType.MAXIMIZE, weight=1.0)
        ]
        
        # Crear valores de la matriz
        values = np.array([
            [4.0, 5.0, 3.0],
            [3.0, 4.0, 5.0],
            [5.0, 3.0, 4.0]
        ])
        
        return DecisionMatrix(
            name="Test Matrix",
            alternatives=alternatives,
            criteria=criteria,
            values=values
        )
    
    @pytest.fixture
    def consistent_criteria_comparison_matrix(self):
        """Matriz de comparación de criterios consistente (CR < 0.1)."""
        return np.array([
            [1.0, 3.0, 5.0],
            [1/3, 1.0, 3.0],
            [1/5, 1/3, 1.0]
        ])
    
    @pytest.fixture
    def inconsistent_criteria_comparison_matrix(self):
        """Matriz de comparación de criterios inconsistente (CR > 0.1)."""
        return np.array([
            [1.0, 9.0, 1/9],  # Extremadamente inconsistente
            [1/9, 1.0, 9.0],
            [9.0, 1/9, 1.0]
        ])
    
    def test_ahp_properties(self, ahp_method):
        """Test that AHP method has correct properties."""
        assert ahp_method.name == "AHP"
        assert ahp_method.full_name == "Analytic Hierarchy Process"
        assert isinstance(ahp_method.description, str)
        assert len(ahp_method.description) > 0
    
    def test_default_parameters(self, ahp_method):
        """Test that default parameters are correctly set."""
        params = ahp_method.get_default_parameters()
        
        assert params['criteria_comparison_matrix'] is None
        assert params['alternatives_comparison_matrices'] is None
        assert params['consistency_ratio_threshold'] == 0.1
        assert params['weight_calculation_method'] == 'eigenvector'
        assert params['use_pairwise_comparison_for_alternatives'] == True
        assert params['show_consistency_details'] == True
        assert params['normalize_before_comparison'] == True
        assert params['normalization_method'] == 'minimax'
    
    def test_validate_parameters_valid(self, ahp_method, consistent_criteria_comparison_matrix):
        """Test parameter validation with valid parameters."""
        valid_params = {
            'criteria_comparison_matrix': consistent_criteria_comparison_matrix,
            'consistency_ratio_threshold': 0.1,
            'weight_calculation_method': 'eigenvector',
            'use_pairwise_comparison_for_alternatives': False,
            'show_consistency_details': True
        }
        
        assert ahp_method.validate_parameters(valid_params) == True
    
    def test_validate_parameters_invalid_threshold(self, ahp_method):
        """Test parameter validation with invalid consistency threshold."""
        invalid_params = {
            'consistency_ratio_threshold': -0.1  # Negative threshold
        }
        
        assert ahp_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_invalid_method(self, ahp_method):
        """Test parameter validation with invalid weight calculation method."""
        invalid_params = {
            'weight_calculation_method': 'invalid_method'
        }
        
        assert ahp_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_invalid_matrix_type(self, ahp_method):
        """Test parameter validation with invalid matrix type."""
        invalid_params = {
            'criteria_comparison_matrix': "not a matrix"
        }
        
        assert ahp_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_non_square_matrix(self, ahp_method):
        """Test parameter validation with non-square matrix."""
        non_square_matrix = np.array([[1, 2, 3], [4, 5, 6]])  # 2x3 matrix
        invalid_params = {
            'criteria_comparison_matrix': non_square_matrix
        }
        
        assert ahp_method.validate_parameters(invalid_params) == False
    
    def test_execute_with_consistent_matrix(self, ahp_method, sample_decision_matrix, 
                                          consistent_criteria_comparison_matrix):
        """Test AHP execution with consistent comparison matrix."""
        params = {
            'criteria_comparison_matrix': consistent_criteria_comparison_matrix,
            'use_pairwise_comparison_for_alternatives': False
        }
        
        result = ahp_method.execute(sample_decision_matrix, params)
        
        # Verificar que el resultado tiene la estructura correcta
        assert result.method_name == "AHP"
        assert len(result.alternative_ids) == 3
        assert len(result.scores) == 3
        assert len(result.rankings) == 3
        
        # Verificar que los metadatos contienen información de consistencia
        metadata = result.metadata
        assert 'criteria_weights' in metadata
        assert 'consistency_info' in metadata
        assert metadata['consistency_info']['criteria_consistency']['is_consistent'] == True
    
    def test_execute_with_inconsistent_matrix(self, ahp_method, sample_decision_matrix, 
                                            inconsistent_criteria_comparison_matrix):
        """Test AHP execution with inconsistent comparison matrix."""
        params = {
            'criteria_comparison_matrix': inconsistent_criteria_comparison_matrix,
            'use_pairwise_comparison_for_alternatives': False,
            'consistency_ratio_threshold': 0.1
        }
        
        result = ahp_method.execute(sample_decision_matrix, params)
        
        # Verificar que la inconsistencia se detecta
        metadata = result.metadata
        consistency_info = metadata['consistency_info']['criteria_consistency']
        assert consistency_info['is_consistent'] == False
        assert consistency_info['consistency_ratio'] > 0.1
    
    def test_execute_without_comparison_matrix(self, ahp_method, sample_decision_matrix):
        """Test AHP execution without providing comparison matrix (uses weights from criteria)."""
        result = ahp_method.execute(sample_decision_matrix)
        
        # Verificar que se generó una matriz de comparación consistente
        metadata = result.metadata
        assert 'criteria_weights' in metadata
        assert 'consistency_info' in metadata
        assert metadata['consistency_info']['criteria_consistency']['method'] == 'weights_derived'
    
    def test_calculate_weights_from_comparison_matrix(self, ahp_method, 
                                                    consistent_criteria_comparison_matrix):
        """Test internal weight calculation from comparison matrix."""
        n = consistent_criteria_comparison_matrix.shape[0]
        weights, consistency_info = ahp_method._calculate_weights_from_pairwise_matrix(
            consistent_criteria_comparison_matrix, n
        )
        
        # Verificar que los pesos suman 1
        assert np.isclose(np.sum(weights), 1.0)
        
        # Verificar que la información de consistencia es correcta
        assert 'consistency_index' in consistency_info
        assert 'consistency_ratio' in consistency_info
        assert 'is_consistent' in consistency_info
        assert 'max_eigenvalue' in consistency_info
    
    def test_random_consistency_index(self, ahp_method):
        """Test that random consistency index values are correct."""
        # Verificar algunos valores conocidos del índice de consistencia aleatoria
        assert ahp_method._RANDOM_CONSISTENCY_INDEX[3] == 0.58
        assert ahp_method._RANDOM_CONSISTENCY_INDEX[4] == 0.90
        assert ahp_method._RANDOM_CONSISTENCY_INDEX[5] == 1.12
    
    def test_execute_with_pairwise_alternatives(self, ahp_method, sample_decision_matrix):
        """Test AHP execution using pairwise comparison for alternatives."""
        # Crear matrices de comparación por pares para cada criterio
        alt_comp_matrices = [
            np.array([[1.0, 2.0, 3.0], [0.5, 1.0, 2.0], [1/3, 0.5, 1.0]]),  # Para criterio 1
            np.array([[1.0, 0.5, 2.0], [2.0, 1.0, 3.0], [0.5, 1/3, 1.0]]),  # Para criterio 2
            np.array([[1.0, 3.0, 0.5], [1/3, 1.0, 0.2], [2.0, 5.0, 1.0]])   # Para criterio 3
        ]
        
        params = {
            'alternatives_comparison_matrices': alt_comp_matrices,
            'use_pairwise_comparison_for_alternatives': True
        }
        
        result = ahp_method.execute(sample_decision_matrix, params)
        
        # Verificar que se calcularon las prioridades para alternativas
        metadata = result.metadata
        assert 'alternative_priorities' in metadata
        alt_priorities_array = np.array(metadata['alternative_priorities'])
        alt_priorities_array.shape == (3, 3)
    
    def test_execute_with_automatic_pairwise_generation(self, ahp_method, sample_decision_matrix):
        """Test AHP execution where it automatically generates pairwise matrices."""
        params = {
            'use_pairwise_comparison_for_alternatives': True,
            'alternatives_comparison_matrices': None,  # No proporcionamos matrices
            'normalize_before_comparison': True
        }
        
        result = ahp_method.execute(sample_decision_matrix, params)
        
        # Verificar que se generaron matrices de comparación automáticamente
        metadata = result.metadata
        assert 'alternative_priorities' in metadata
        
        # Verificar que se calculó información de consistencia para alternativas
        if 'alternatives_consistency' in metadata['consistency_info']:
            alt_consistency = metadata['consistency_info']['alternatives_consistency']
            assert len(alt_consistency) == len(sample_decision_matrix.criteria)
    
    def test_saaty_scale_interpretation(self, ahp_method):
        """Test that method properly handles Saaty's scale values."""
        # Crear una matriz de comparación con valores de la escala de Saaty
        comparison_matrix = np.array([
            [1.0, 3.0, 5.0, 7.0],  # Igual, moderado, fuerte, muy fuerte
            [1/3, 1.0, 3.0, 5.0],
            [1/5, 1/3, 1.0, 3.0],
            [1/7, 1/5, 1/3, 1.0]
        ])
        
        weights, consistency_info = ahp_method._calculate_weights_from_pairwise_matrix(
            comparison_matrix, 4
        )
        
        # Los pesos deberían estar ordenados de mayor a menor
        assert weights[0] > weights[1] > weights[2] > weights[3]
    
    def test_error_handling_no_decision_matrix(self, ahp_method):
        """Test error handling when decision matrix is not provided."""
        with pytest.raises(MethodError) as exc_info:
            ahp_method.execute(None)
        
        assert "'NoneType' object has no attribute 'alternative'" in str(exc_info.value)
    
    def test_error_handling_invalid_decision_matrix(self, ahp_method):
        """Test error handling with invalid decision matrix."""
        with pytest.raises(MethodError) as exc_info:
            ahp_method.execute("not a matrix")
        
        assert "Error executing the AHP method" in str(exc_info.value)
    
    def test_error_handling_wrong_matrix_dimensions(self, ahp_method, sample_decision_matrix):
        """Test error handling when comparison matrix has wrong dimensions."""
        wrong_dimension_matrix = np.array([[1.0, 2.0], [0.5, 1.0]])
        
        params = {
            'criteria_comparison_matrix': wrong_dimension_matrix
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ahp_method.execute(sample_decision_matrix, params)
        
        assert "incorrect dimensions" in str(exc_info.value)
    
    def test_approximate_weights_method(self, ahp_method):
        """Test the approximate weight calculation method."""
        # Probar el método alternativo de cálculo de pesos
        comparison_matrix = np.array([
            [1.0, 3.0, 5.0],
            [1/3, 1.0, 3.0],
            [1/5, 1/3, 1.0]
        ])
        
        # El método _approximate_weights calcula los pesos usando media geométrica
        weights = ahp_method._approximate_weights(comparison_matrix, 3)
        
        # Verificar que los pesos suman 1
        assert np.isclose(np.sum(weights), 1.0)
        
        # Verificar que los pesos tienen el orden esperado
        assert weights[0] > weights[1] > weights[2]
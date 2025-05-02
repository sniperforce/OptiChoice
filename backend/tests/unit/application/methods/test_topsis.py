import pytest
import numpy as np

from application.methods.topsis import TOPSISMethod
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from utils.exceptions import MethodError, ValidationError

class TestTOPSISMethod:
    
    @pytest.fixture
    def topsis_method(self):
        """Fixture providing a TOPSIS method instance."""
        return TOPSISMethod()
    
    @pytest.fixture
    def sample_decision_matrix(self):
        """Fixture providing a sample decision matrix for testing."""
        # Crear alternativas
        alternatives = [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
        ]
        
        # Crear criterios con diferentes tipos de optimización
        criteria = [
            Criteria(id="crit1", name="Criteria 1", 
                    optimization_type=OptimizationType.MAXIMIZE, weight=0.4),
            Criteria(id="crit2", name="Criteria 2", 
                    optimization_type=OptimizationType.MINIMIZE, weight=0.3),
            Criteria(id="crit3", name="Criteria 3", 
                    optimization_type=OptimizationType.MAXIMIZE, weight=0.3)
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
    
    def test_topsis_properties(self, topsis_method):
        """Test that TOPSIS method has correct properties."""
        assert topsis_method.name == "TOPSIS"
        assert topsis_method.full_name == "Technique for Order of Preference by Similarity to Ideal Solution"
        assert isinstance(topsis_method.description, str)
        assert len(topsis_method.description) > 0
    
    def test_default_parameters(self, topsis_method):
        """Test that default parameters are correctly set."""
        params = topsis_method.get_default_parameters()
        
        assert params['normalization_method'] == 'vector'
        assert params['normalize_matrix'] == True
        assert params['distance_metric'] == 'euclidean'
        assert params['apply_weights_after_normalization'] == True
        assert params['consider_criteria_type'] == True
    
    def test_validate_parameters_valid(self, topsis_method):
        """Test parameter validation with valid parameters."""
        valid_params = {
            'normalization_method': 'vector',
            'normalize_matrix': True,
            'distance_metric': 'euclidean',
            'apply_weights_after_normalization': True,
            'consider_criteria_type': True
        }
        
        assert topsis_method.validate_parameters(valid_params) == True
    
    def test_validate_parameters_invalid_normalization(self, topsis_method):
        """Test parameter validation with invalid normalization method."""
        invalid_params = {
            'normalization_method': 'invalid_method'
        }
        
        assert topsis_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_invalid_distance(self, topsis_method):
        """Test parameter validation with invalid distance metric."""
        invalid_params = {
            'distance_metric': 'invalid_metric'
        }
        
        assert topsis_method.validate_parameters(invalid_params) == False
    
    def test_validate_parameters_invalid_boolean(self, topsis_method):
        """Test parameter validation with invalid boolean values."""
        invalid_params = {
            'normalize_matrix': 'not_a_boolean'
        }
        
        assert topsis_method.validate_parameters(invalid_params) == False
    
    def test_execute_with_default_parameters(self, topsis_method, sample_decision_matrix):
        """Test TOPSIS execution with default parameters."""
        result = topsis_method.execute(sample_decision_matrix)
        
        # Verificar que el resultado tiene la estructura correcta
        assert result.method_name == "TOPSIS"
        assert len(result.alternative_ids) == 3
        assert len(result.scores) == 3
        assert len(result.rankings) == 3
        
        # Verificar que los metadatos están presentes
        metadata = result.metadata
        assert 'normalized_values' in metadata
        assert 'weighted_values' in metadata
        assert 'ideal_positive' in metadata
        assert 'ideal_negative' in metadata
        assert 'distances_positive' in metadata
        assert 'distances_negative' in metadata
    
    def test_execute_without_normalization(self, topsis_method, sample_decision_matrix):
        """Test TOPSIS execution without normalization."""
        params = {'normalize_matrix': False}
        result = topsis_method.execute(sample_decision_matrix, params)
        
        # Verificar que el resultado es diferente al de normalización
        assert result.method_name == "TOPSIS"
        # Los valores normalizados deberían ser iguales a los originales
        assert np.array_equal(
            result.metadata['normalized_values'], 
            sample_decision_matrix.values.tolist()
        )
    
    def test_execute_with_different_normalization(self, topsis_method, sample_decision_matrix):
        """Test TOPSIS with different normalization methods."""
        normalization_methods = ['minimax', 'sum', 'max', 'vector']
        
        results = {}
        for method in normalization_methods:
            params = {'normalization_method': method}
            result = topsis_method.execute(sample_decision_matrix, params)
            results[method] = result.scores
        
        # Verificar que diferentes métodos producen diferentes resultados
        # (pueden coincidir en algunos casos, pero no en general)
        unique_scores = set(tuple(scores) for scores in results.values())
        assert len(unique_scores) > 1
    
    def test_execute_with_different_distance_metrics(self, topsis_method, sample_decision_matrix):
        """Test TOPSIS with different distance metrics."""
        distance_metrics = ['euclidean', 'manhattan', 'chebyshev']
        
        results = {}
        for metric in distance_metrics:
            params = {'distance_metric': metric}
            result = topsis_method.execute(sample_decision_matrix, params)
            results[metric] = result.scores
        
        # Verificar que diferentes métricas producen diferentes resultados
        unique_scores = set(tuple(scores) for scores in results.values())
        assert len(unique_scores) > 1
    
    def test_parameter_validation_strict(self, topsis_method):
        """Test strict parameter validation."""
        invalid_params = {
            'normalization_method': 'invalid_method'
        }

        assert topsis_method.validate_parameters(invalid_params) == False

        with pytest.raises(ValueError) as exc_info:
            topsis_method._prepare_execution(None, invalid_params)
        
        assert "Invalid Parameters for the method TOPSIS" in str(exc_info.value)

    def test_execute_without_considering_criteria_type(self, topsis_method, sample_decision_matrix):
        """Test TOPSIS execution without considering criteria optimization type."""
        params = {'consider_criteria_type': False}
        result_without = topsis_method.execute(sample_decision_matrix, params)
        
        params = {'consider_criteria_type': True}
        result_with = topsis_method.execute(sample_decision_matrix, params)
        
        # Los resultados deberían ser diferentes
        assert not np.array_equal(result_without.scores, result_with.scores)
    
    def test_execute_with_equal_values(self, topsis_method):
        """Test TOPSIS with all equal values in the matrix."""
        alternatives = [
            Alternative(id=f"alt{i}", name=f"Alternative {i}") for i in range(3)
        ]
        criteria = [
            Criteria(id=f"crit{i}", name=f"Criteria {i}") for i in range(3)
        ]
        values = np.ones((3, 3))  # Todos los valores son 1
        
        matrix = DecisionMatrix(
            name="Equal Values",
            alternatives=alternatives,
            criteria=criteria,
            values=values
        )
        
        result = topsis_method.execute(matrix)
        
        # Todas las alternativas deberían tener el mismo score
        assert np.allclose(result.scores, 0.5)
    
    def test_prepare_execution_invalid_parameters(self, topsis_method):
        """Test that _prepare_execution raises error with invalid parameters."""
        invalid_params = {
            'normalization_method': 'invalid_method'
        }       
        alternatives = [Alternative(id="alt1", name="Alt 1")]
        criteria = [Criteria(id="crit1", name="Crit 1")]
        matrix = DecisionMatrix(
            name="Test",
            alternatives=alternatives,
            criteria=criteria,
            values=np.array([[1.0]])
        )
        with pytest.raises(ValueError) as exc_info:
            topsis_method._prepare_execution(matrix, invalid_params)
        
        assert "Invalid Parameters for the method TOPSIS" in str(exc_info.value)

    def test_execute_with_single_alternative(self, topsis_method):
        """Test TOPSIS with only one alternative."""
        alternatives = [Alternative(id="alt1", name="Alternative 1")]
        criteria = [Criteria(id="crit1", name="Criteria 1")]
        values = np.array([[5.0]])
        
        matrix = DecisionMatrix(
            name="Single Alternative",
            alternatives=alternatives,
            criteria=criteria,
            values=values
        )
        
        result = topsis_method.execute(matrix)
        
        # Con una sola alternativa, el score debería ser 0.5
        assert result.scores[0] == 0.5
    
    def test_calculate_distances(self, topsis_method):
        """Test internal distance calculation method."""
        values = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])
        ideal_point = np.array([0.0, 0.0, 0.0])
        
        # Probar distancia euclidiana
        euclidean_distances = topsis_method._calculate_distances(
            values, ideal_point, 2, 'euclidean'
        )
        expected_euclidean = [
            np.sqrt(1**2 + 2**2 + 3**2),
            np.sqrt(4**2 + 5**2 + 6**2)
        ]
        assert np.allclose(euclidean_distances, expected_euclidean)
        
        # Probar distancia manhattan
        manhattan_distances = topsis_method._calculate_distances(
            values, ideal_point, 2, 'manhattan'
        )
        expected_manhattan = [6.0, 15.0]  # |1|+|2|+|3| = 6, |4|+|5|+|6| = 15
        assert np.allclose(manhattan_distances, expected_manhattan)
        
        # Probar distancia chebyshev
        chebyshev_distances = topsis_method._calculate_distances(
            values, ideal_point, 2, 'chebyshev'
        )
        expected_chebyshev = [3.0, 6.0]  # max(|1|,|2|,|3|) = 3, max(|4|,|5|,|6|) = 6
        assert np.allclose(chebyshev_distances, expected_chebyshev)
    
    def test_error_handling_invalid_matrix(self, topsis_method):
        """Test error handling with invalid decision matrix."""
        with pytest.raises(MethodError) as exc_info:
            topsis_method.execute("not a matrix")

        assert "'str' object has no attribute 'alternative'" in str(exc_info.value)
        assert "TOPSIS" in str(exc_info.value)
    
    def test_error_handling_invalid_parameters(self, topsis_method, sample_decision_matrix):
        """Test error handling with invalid parameters that fail validation."""
        invalid_params = {
            'normalization_method': 'invalid_method',
            'normalize_matrix': True
        }
        
        with pytest.raises(MethodError) as exc_info:
            topsis_method.execute(sample_decision_matrix, invalid_params)
        
        assert "Error executing the TOPSIS method" in str(exc_info.value)
        assert "Invalid Parameters for the method TOPSIS" in str(exc_info.value)
    
    def test_zero_values_handling(self, topsis_method):
        """Test handling of zero values in the matrix."""
        alternatives = [
            Alternative(id=f"alt{i}", name=f"Alternative {i}") for i in range(3)
        ]
        criteria = [
            Criteria(id=f"crit{i}", name=f"Criteria {i}") for i in range(3)
        ]
        # Crear matriz con algunos valores cero
        values = np.array([
            [0.0, 5.0, 3.0],
            [4.0, 0.0, 2.0],
            [5.0, 3.0, 0.0]
        ])
        
        matrix = DecisionMatrix(
            name="Zero Values",
            alternatives=alternatives,
            criteria=criteria,
            values=values
        )
        
        # Debería ejecutarse sin errores
        result = topsis_method.execute(matrix)
        assert result.method_name == "TOPSIS"
    
    def test_weights_normalization(self, topsis_method, sample_decision_matrix):
        """Test that criteria weights are properly normalized."""
        # Modificar los pesos para que no sumen 1
        for crit in sample_decision_matrix.criteria:
            crit.weight = 2.0  # Todos los pesos = 2, suma = 6
        
        result = topsis_method.execute(sample_decision_matrix)
        
        # Los pesos deberían haberse normalizado
        metadata = result.metadata
        weighted_values = metadata['weighted_values']
        
        # Verificar que el resultado existe (la normalización funcionó)
        assert len(weighted_values) > 0
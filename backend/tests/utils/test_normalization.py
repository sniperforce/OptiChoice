import pytest
import numpy as np
from domain.entities.criteria import Criteria, OptimizationType
from utils.normalization import normalize_matrix, normalize_minmax, normalize_sum, normalize_max, normalize_vector

class TestNormalization:
    
    @pytest.fixture
    def sample_values(self):
        """Matriz de valores para pruebas."""
        return np.array([
            [5.0, 2.0, 7.0],
            [9.0, 3.0, 5.0],
            [2.0, 8.0, 3.0]
        ])
    
    @pytest.fixture
    def mixed_criteria(self):
        """Criterios mixtos (beneficio y costo)."""
        return [
            Criteria(id="c1", name="C1", optimization_type=OptimizationType.MAXIMIZE),
            Criteria(id="c2", name="C2", optimization_type=OptimizationType.MINIMIZE),
            Criteria(id="c3", name="C3", optimization_type=OptimizationType.MAXIMIZE)
        ]
    
    def test_normalize_minmax(self, sample_values, mixed_criteria):
        """Prueba la normalización min-max."""
        normalized = normalize_minmax(sample_values, mixed_criteria)
        
        # Verificar que los valores están en el rango [0, 1]
        assert np.all(normalized >= 0)
        assert np.all(normalized <= 1)
        
        # Verificar valores específicos para el primer criterio (beneficio)
        # (5-2)/(9-2) = 3/7 = 0.4286
        assert np.isclose(normalized[0, 0], 0.4286, atol=1e-4)
        # (9-2)/(9-2) = 7/7 = 1.0
        assert np.isclose(normalized[1, 0], 1.0)
        # (2-2)/(9-2) = 0/7 = 0.0
        assert np.isclose(normalized[2, 0], 0.0)
        
        # Verificar valores para el segundo criterio (costo)
        # (8-2)/(8-2) = 6/6 = 1.0
        assert np.isclose(normalized[0, 1], 1.0, atol=1e-4)
        # (8-3)/(8-2) = 5/6 = 0.8333
        assert np.isclose(normalized[1, 1], 0.8333, atol=1e-4)
        # (8-8)/(8-2) = 0/6 = 0.0
        assert np.isclose(normalized[2, 1], 0.0)
    
    def test_normalize_sum(self, sample_values, mixed_criteria):
        """Prueba la normalización por suma."""
        normalized = normalize_sum(sample_values, mixed_criteria)
        
        # Verificar que la suma de cada columna es aproximadamente 1
        for j in range(normalized.shape[1]):
            assert np.isclose(np.sum(normalized[:, j]), 1.0)
    
    def test_normalize_max(self, sample_values, mixed_criteria):
        """Prueba la normalización por máximo."""
        normalized = normalize_max(sample_values, mixed_criteria)
        
        # Para criterios de beneficio, el máximo debe ser 1
        assert np.isclose(np.max(normalized[:, 0]), 1.0)
        
        # Para criterios de costo, el mínimo debe ser 1
        assert np.isclose(np.max(normalized[:, 1]), 1.0)
    
    def test_normalize_vector(self, sample_values, mixed_criteria):
        """Prueba la normalización vectorial (norma euclidiana)."""
        normalized = normalize_vector(sample_values, mixed_criteria)
        
        # Verificar que la norma euclidiana de cada columna es aproximadamente 1
        for j in range(normalized.shape[1]):
            col_norm = np.sqrt(np.sum(normalized[:, j] ** 2))
            assert np.isclose(col_norm, 1.0, atol=1e-10)
        
        # Para criterios de costo, los valores deben ser negativos
        assert np.all(normalized[:, 1] < 0)
    
    def test_normalize_matrix_all_methods(self, sample_values, mixed_criteria):
        """Prueba la función general normalize_matrix con todos los métodos."""
        for method in ['minimax', 'sum', 'max', 'vector']:
            normalized = normalize_matrix(sample_values, mixed_criteria, method)
            
            # Verificar que la forma de la matriz no cambia
            assert normalized.shape == sample_values.shape
            
            # Verificar que no hay valores NaN o infinitos
            assert np.all(np.isfinite(normalized))
    
    def test_normalize_matrix_invalid_method(self, sample_values, mixed_criteria):
        """Prueba que se lance ValueError con método inválido."""
        with pytest.raises(ValueError):
            normalize_matrix(sample_values, mixed_criteria, "invalid_method")
    
    def test_normalize_edge_cases(self):
        """Prueba casos extremos: todos los valores iguales, ceros, etc."""
        # Matriz con todos los valores iguales
        equal_values = np.ones((3, 2))
        criteria = [
            Criteria(id="c1", name="C1", optimization_type=OptimizationType.MAXIMIZE),
            Criteria(id="c2", name="C2", optimization_type=OptimizationType.MINIMIZE)
        ]
        
        # Probar normalización minimax con valores iguales
        normalized = normalize_minmax(equal_values, criteria)
        assert np.all(normalized[:, 0] == 1.0)  # Beneficio
        assert np.all(normalized[:, 1] == 0.0)  # Costo
        
        # Matriz con ceros
        zero_values = np.zeros((3, 2))
        normalized = normalize_vector(zero_values, criteria)
        assert np.all(normalized == 0.0)
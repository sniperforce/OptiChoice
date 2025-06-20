from typing import Dict, List, Any, Optional
import numpy as np
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from domain.entities.criteria import OptimizationType
from application.methods.method_interface import MCDMMethodInterface
from utils.exceptions import MethodError
from utils.normalization import normalize_matrix


class TOPSISMethod(MCDMMethodInterface):
    """Implementación del método TOPSIS"""
    
    @property
    def name(self) -> str:
        return "TOPSIS"
    
    @property
    def full_name(self) -> str:
        return "Technique for Order of Preference by Similarity to Ideal Solution"
    
    @property
    def description(self) -> str:
        return """TOPSIS is a multi-criteria decision making method that identifies 
        solutions from a finite set of alternatives based upon simultaneous 
        minimization of distance from an ideal point and maximization of distance 
        from a nadir point."""
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'normalization_method': 'vector',
            'ideal_solution': 'auto',
            'nadir_solution': 'auto'
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        valid_normalization = ['vector', 'linear', 'minmax']
        if parameters.get('normalization_method') not in valid_normalization:
            return False
        return True
    
    def execute(self, decision_matrix: DecisionMatrix, 
                parameters: Optional[Dict[str, Any]] = None) -> Result:
        """Ejecutar el método TOPSIS"""
        try:
            # Preparar parámetros
            params = self._prepare_execution(decision_matrix, parameters)
            
            # Obtener datos de la matriz
            matrix = decision_matrix.get_matrix()
            weights = decision_matrix.get_weights()
            criteria = decision_matrix.criteria
            alternatives = decision_matrix.alternatives
            
            # Verificar que la matriz no esté vacía
            if matrix.size == 0:
                raise MethodError("Empty decision matrix", self.name)
            
            # Normalizar la matriz
            normalized_matrix = normalize_matrix(
                matrix, 
                method=params['normalization_method']
            )
            
            # Aplicar pesos
            weighted_matrix = normalized_matrix * weights
            
            # Determinar solución ideal y nadir
            ideal_solution = np.zeros(len(criteria))
            nadir_solution = np.zeros(len(criteria))
            
            for j, criterion in enumerate(criteria):
                col = weighted_matrix[:, j]
                if criterion.optimization_type == OptimizationType.MAXIMIZE:
                    ideal_solution[j] = np.max(col)
                    nadir_solution[j] = np.min(col)
                else:  # MINIMIZE
                    ideal_solution[j] = np.min(col)
                    nadir_solution[j] = np.max(col)
            
            # Calcular distancias
            n_alternatives = len(alternatives)
            distances_to_ideal = np.zeros(n_alternatives)
            distances_to_nadir = np.zeros(n_alternatives)
            
            for i in range(n_alternatives):
                distances_to_ideal[i] = np.sqrt(
                    np.sum((weighted_matrix[i] - ideal_solution) ** 2)
                )
                distances_to_nadir[i] = np.sqrt(
                    np.sum((weighted_matrix[i] - nadir_solution) ** 2)
                )
            
            # Calcular coeficientes de cercanía
            # Evitar división por cero
            total_distances = distances_to_ideal + distances_to_nadir
            total_distances[total_distances == 0] = 1e-10
            
            closeness_coefficients = distances_to_nadir / total_distances
            
            # Crear resultado
            result = Result(
                method_name=self.name,
                alternative_ids=[alt.id for alt in alternatives],
                alternative_names=[alt.name for alt in alternatives],
                scores=closeness_coefficients,
                parameters=params,
                metadata={
                    'ideal_solution': ideal_solution.tolist(),
                    'nadir_solution': nadir_solution.tolist(),
                    'distances_to_ideal': distances_to_ideal.tolist(),
                    'distances_to_nadir': distances_to_nadir.tolist()
                }
            )
            
            return result
            
        except Exception as e:
            raise MethodError(
                f"Error executing TOPSIS: {str(e)}", 
                self.name
            )
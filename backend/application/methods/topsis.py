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
            matrix = decision_matrix.values
            criteria = decision_matrix.criteria
            alternatives = decision_matrix.alternative
            
            # Validaciones exhaustivas
            if matrix.size == 0:
                raise MethodError("Empty decision matrix", self.name)
            
            if len(alternatives) == 0:
                raise MethodError("No alternatives in decision matrix", self.name)
            
            if len(criteria) == 0:
                raise MethodError("No criteria in decision matrix", self.name)
            
            if matrix.shape[0] != len(alternatives):
                raise MethodError(
                    f"Matrix rows ({matrix.shape[0]}) don't match alternatives ({len(alternatives)})", 
                    self.name
                )
            
            if matrix.shape[1] != len(criteria):
                raise MethodError(
                    f"Matrix columns ({matrix.shape[1]}) don't match criteria ({len(criteria)})", 
                    self.name
                )
            
            # Verificar que no haya valores NaN o infinitos
            if np.any(np.isnan(matrix)):
                raise MethodError("Matrix contains NaN values", self.name)
            
            if np.any(np.isinf(matrix)):
                raise MethodError("Matrix contains infinite values", self.name)
            
            # Calcular y validar pesos
            weights = np.array([c.weight for c in criteria])
            
            if len(weights) != len(criteria):
                raise MethodError(
                    f"Number of weights ({len(weights)}) doesn't match criteria ({len(criteria)})", 
                    self.name
                )
            
            if np.sum(weights) == 0:
                raise MethodError("Sum of weights is zero", self.name)
            
            # Normalizar pesos para que sumen 1
            weights = weights / np.sum(weights)
            
            # Log para debugging
            print(f"TOPSIS - Matrix shape: {matrix.shape}")
            print(f"TOPSIS - Weights: {weights}")
            print(f"TOPSIS - Normalization method: {params['normalization_method']}")
            
            # Normalizar la matriz
            normalized_matrix = normalize_matrix(matrix, method=params['normalization_method'])
            
            # Aplicar pesos
            weighted_matrix = normalized_matrix * weights
            
            # Determinar soluciones ideales
            ideal_positive = np.zeros(len(criteria))
            ideal_negative = np.zeros(len(criteria))
            
            for j, criterion in enumerate(criteria):
                if criterion.optimization_type == OptimizationType.MAXIMIZE:
                    ideal_positive[j] = np.max(weighted_matrix[:, j])
                    ideal_negative[j] = np.min(weighted_matrix[:, j])
                else:
                    ideal_positive[j] = np.min(weighted_matrix[:, j])
                    ideal_negative[j] = np.max(weighted_matrix[:, j])
            
            # Calcular distancias
            distances_positive = np.sqrt(np.sum((weighted_matrix - ideal_positive) ** 2, axis=1))
            distances_negative = np.sqrt(np.sum((weighted_matrix - ideal_negative) ** 2, axis=1))
            
            # Calcular proximidad relativa
            # Evitar división por cero
            denominator = distances_positive + distances_negative
            scores = np.where(
                denominator > 0,
                distances_negative / denominator,
                0.0
            )
            
            # Calcular rankings
            rankings = len(scores) - np.argsort(np.argsort(scores))
            
            # Crear resultado
            result = Result(
                method_name=self.name,
                alternatives=alternatives,
                scores=scores,
                rankings=rankings,
                parameters=params
            )
            
            # Agregar metadatos
            result.set_metadata('normalized_matrix', normalized_matrix.tolist())
            result.set_metadata('weighted_matrix', weighted_matrix.tolist())
            result.set_metadata('ideal_positive', ideal_positive.tolist())
            result.set_metadata('ideal_negative', ideal_negative.tolist())
            result.set_metadata('distances_positive', distances_positive.tolist())
            result.set_metadata('distances_negative', distances_negative.tolist())
            
            return result
            
        except MethodError:
            raise
        except Exception as e:
            raise MethodError(
                f"Unexpected error in TOPSIS execution: {str(e)}",
                self.name
            ) from e
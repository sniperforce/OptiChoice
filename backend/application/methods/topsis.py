"""
Module that implements the TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) method.

TOPSIS is a multi-criteria decision method based on selecting alternatives
that are closest to the positive ideal solution and furthest from the negative ideal solution.
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from application.methods.method_interface import MCDMMethodInterface
from utils.exceptions import MethodError, ValidationError
from utils.normalization import normalize_matrix


class TOPSISMethod(MCDMMethodInterface):
    @property
    def name(self) -> str:
        return "TOPSIS"
    
    @property
    def full_name(self) -> str:
        return "Technique for Order of Preference by Similarity to Ideal Solution"
    
    @property
    def description(self) -> str:
        return """
        TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) is a 
        multi-criteria decision method developed by Hwang and Yoon in 1981.
        
        Main characteristics:
        - Identifies positive and negative ideal solutions
        - Calculates Euclidean distance (or other) to these solutions
        - Determines the relative proximity of each alternative to the ideal solution
        - Provides a complete ranking of alternatives
        - Compensates deficiencies between criteria
        
        TOPSIS is especially useful when a compensatory method is required
        and when all criteria can be valued on numerical scales.
        The method is simple, efficient, and has a solid mathematical foundation.
        """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'normalization_method': 'vector',
            'normalize_matrix': True,
            
            # Distance measure to use ('euclidean', 'manhattan', 'chebyshev')
            'distance_metric': 'euclidean',
            
            # If True, weights are applied after normalization
            'apply_weights_after_normalization': True,
            
            # If True, criteria types (benefit/cost) are considered
            # If False, all criteria are assumed to be benefit
            'consider_criteria_type': True
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        if 'normalization_method' in parameters:
            if parameters['normalization_method'] not in ['minmax', 'sum', 'max', 'vector']:
                return False
        
        if 'normalize_matrix' in parameters:
            if not isinstance(parameters['normalize_matrix'], bool):
                return False
        
        if 'distance_metric' in parameters:
            if parameters['distance_metric'] not in ['euclidean', 'manhattan', 'chebyshev']:
                return False
        
        if 'apply_weights_after_normalization' in parameters:
            if not isinstance(parameters['apply_weights_after_normalization'], bool):
                return False
        
        if 'consider_criteria_type' in parameters:
            if not isinstance(parameters['consider_criteria_type'], bool):
                return False
        
        return True
    
    def execute(self, decision_matrix: DecisionMatrix, 
                parameters: Optional[Dict[str, Any]] = None) -> Result:
        try:
            params = self._prepare_execution(decision_matrix, parameters)
            
            alternatives = decision_matrix.alternatives
            criteria = decision_matrix.criteria
            values = decision_matrix.values.copy()
            
            n_alternatives = len(alternatives)
            n_criteria = len(criteria)
            
            # Step 1: Normalize the matrix if requested
            if params.get('normalize_matrix', True):
                values = normalize_matrix(
                    values=values,
                    criteria=criteria,
                    method=params.get('normalization_method', 'vector')
                )
            
            # Get criteria weights and normalize them
            weights = np.array([crit.weight for crit in criteria])
            weights = weights / np.sum(weights) if np.sum(weights) > 0 else np.ones(n_criteria) / n_criteria
            
            # Step 2: Apply weighting (multiply by weights)
            if params.get('apply_weights_after_normalization', True):
                weighted_values = values.copy()
                for j in range(n_criteria):
                    weighted_values[:, j] *= weights[j]
            else:
                weighted_values = values.copy()
            
            # Step 3: Determine positive and negative ideal solutions
            ideal_positive = np.zeros(n_criteria)
            ideal_negative = np.zeros(n_criteria)
            
            for j in range(n_criteria):
                if params.get('consider_criteria_type', True) and criteria[j].is_cost_criteria():
                    # For cost criteria, lower is better
                    ideal_positive[j] = np.min(weighted_values[:, j])
                    ideal_negative[j] = np.max(weighted_values[:, j])
                else:
                    # For benefit criteria, higher is better
                    ideal_positive[j] = np.max(weighted_values[:, j])
                    ideal_negative[j] = np.min(weighted_values[:, j])
            
            # Step 4: Calculate distances to ideal solutions
            distances_positive = self._calculate_distances(
                weighted_values, ideal_positive, n_alternatives, params.get('distance_metric', 'euclidean'))
                
            distances_negative = self._calculate_distances(
                weighted_values, ideal_negative, n_alternatives, params.get('distance_metric', 'euclidean'))
            
            # Step 5: Calculate relative proximity to the ideal solution (scores)
            scores = np.zeros(n_alternatives)
            for i in range(n_alternatives):
                # Avoid division by zero
                denominator = distances_positive[i] + distances_negative[i]
                if denominator > 0:
                    scores[i] = distances_negative[i] / denominator
                else:
                    scores[i] = 0.5  # Neutral value if both distances are zero
            
            result = Result(
                method_name=self.name,
                alternative_ids=[alt.id for alt in alternatives],
                alternative_names=[alt.name for alt in alternatives],
                scores=scores,
                parameters=params,
                metadata={
                    'normalized_values': values.tolist(),
                    'weighted_values': weighted_values.tolist(),
                    'ideal_positive': ideal_positive.tolist(),
                    'ideal_negative': ideal_negative.tolist(),
                    'distances_positive': distances_positive.tolist(),
                    'distances_negative': distances_negative.tolist()
                }
            )
            
            return result
            
        except ValidationError as e:
            raise e
        except Exception as e:
            raise MethodError(
                message=f"Error executing the TOPSIS method: {str(e)}",
                method_name=self.name
            ) from e
    
    def _calculate_distances(self, values: np.ndarray, ideal_point: np.ndarray, 
                          n_alternatives: int, metric: str) -> np.ndarray:
        distances = np.zeros(n_alternatives)
        
        for i in range(n_alternatives):
            if metric == 'euclidean':
                # Euclidean distance: square root of the sum of squared differences
                distances[i] = np.sqrt(np.sum((values[i, :] - ideal_point) ** 2))
                
            elif metric == 'manhattan':
                # Manhattan distance: sum of absolute differences
                distances[i] = np.sum(np.abs(values[i, :] - ideal_point))
                
            elif metric == 'chebyshev':
                # Chebyshev distance: maximum absolute difference
                distances[i] = np.max(np.abs(values[i, :] - ideal_point))
                
            else:
                # By default, use Euclidean distance
                distances[i] = np.sqrt(np.sum((values[i, :] - ideal_point) ** 2))
        
        return distances
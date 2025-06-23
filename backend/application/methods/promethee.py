"""
Module that implements the PROMETHEE (Preference Ranking Organization Method for Enrichment of Evaluations) method.

PROMETHEE is a multi-criteria decision method based on pairwise comparisons
and preference flows, developed by Jean-Pierre Brans and Bertrand Mareschal.
"""
from typing import Dict, List, Any, Optional, Tuple, Callable
import numpy as np
import math

from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from domain.entities.criteria import Criteria
from application.methods.method_interface import MCDMMethodInterface
from utils.exceptions import MethodError, ValidationError
from utils.normalization import normalize_matrix

class PROMETHEEMethod(MCDMMethodInterface):
    """
    Implementation of the PROMETHEE (Preference Ranking Organization Method for Enrichment of Evaluations) method.
    
    PROMETHEE is based on the enrichment of preference relations through
    functions that quantify the intensity of preference of one alternative over another
    for each criterion. These intensities are aggregated to calculate preference flows
    that allow establishing a complete order among alternatives.
    
    This implementation includes PROMETHEE I (partial ranking) and PROMETHEE II (complete ranking),
    with multiple preference functions available.
    """

    PREFERENCE_FUNCTIONS = {
        "usual": 1,
        "u-shape": 2,
        "v-shape": 3,
        "level": 4,
        "v-shape-indifference": 5,
        "gaussian": 6
    }

    @property
    def name(self) -> str:
        return "PROMETHEE" 

    @property
    def full_name(self) -> str:
        return "Preference Ranking Organization Method for Enrichment of Evaluations"

    @property
    def description(self) -> str:
        return """
        PROMETHEE (Preference Ranking Organization Method for Enrichment of Evaluations) is 
        a multi-criteria decision method developed by Jean-Pierre Brans and Bertrand Mareschal.
        
        Main characteristics:
        - Uses preference functions to model the intensity of preference
        - Calculates positive, negative, and net preference flows
        - Allows different types of criteria and measurement scales
        - Provides both a partial ranking (PROMETHEE I) and complete ranking (PROMETHEE II)
        - Has a graphical extension (GAIA) for visualization
        
        PROMETHEE is especially useful when detailed modeling of decision-maker
        preferences is required and when compensation between
        criteria must be explicitly considered.
        """

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            # Method variant ('I' for partial ranking, 'II' for complete ranking)
            'variant': 'II',
            'default_preference_function': 'v-shape',
            'preference_functions': None,  
            'p_thresholds': None,
            'q_thresholds': None, 
            
            # s parameters (gaussian) by criterion
            's_thresholds': None,
            'normalization_method': 'minmax',
            'normalize_matrix': True
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        # Ensure parameters is not None
        if parameters is None:
            return False
            
        if 'variant' in parameters:
            if parameters['variant'] not in ['I', 'II']:
                return False
        
        if 'default_preference_function' in parameters:
            if parameters['default_preference_function'] not in self.PREFERENCE_FUNCTIONS:
                return False

        if 'preference_functions' in parameters and parameters['preference_functions'] is not None:
            if not isinstance(parameters['preference_functions'], dict):
                return False
            
            for func_name in parameters['preference_functions'].values():
                if func_name not in self.PREFERENCE_FUNCTIONS:
                    return False

        for threshold_name in ['p_thresholds', 'q_thresholds', 's_thresholds']:
            if threshold_name in parameters and parameters[threshold_name] is not None:
                if not isinstance(parameters[threshold_name], dict):
                    return False
                
                for value in parameters[threshold_name].values():
                    if not isinstance(value, (int, float)) or value < 0:
                        return False

        if ('p_thresholds' in parameters and parameters['p_thresholds'] is not None and
            'q_thresholds' in parameters and parameters['q_thresholds'] is not None):
            
            p_thresholds = parameters['p_thresholds']
            q_thresholds = parameters['q_thresholds']
            
            # Verify that p >= q for all common criteria
            for crit_id in set(p_thresholds.keys()).intersection(q_thresholds.keys()):
                if p_thresholds[crit_id] < q_thresholds[crit_id]:
                    return False

        if 'normalization_method' in parameters:
            if parameters['normalization_method'] not in ['minmax', 'sum', 'max', 'vector']:
                return False

        if 'normalize_matrix' in parameters:
            if not isinstance(parameters['normalize_matrix'], bool):
                return False
        
        return True

    def execute(self, decision_matrix: DecisionMatrix,
                parameters: Optional[Dict[str, Any]] = None) -> Result:
        try:
            # Initialize parameters if None
            if parameters is None:
                parameters = {}
                
            # Get default parameters and update with provided ones
            params = self.get_default_parameters()
            params.update(parameters)
            
            # Check if parameters are valid
            if not self.validate_parameters(params):
                raise ValidationError(
                    message="Invalid parameters for PROMETHEE method",
                    errors=["Please check parameter values and types"]
                )

            alternatives = decision_matrix.alternative
            criteria = decision_matrix.criteria
            values = decision_matrix.values

            n_alternatives = len(alternatives)
            n_criteria = len(criteria)

            if params.get('normalize_matrix', True):
                criteria_types = ['minimize' if crit.optimization_type.value == 'minimize' else 'maximize' 
                  for crit in criteria]

                values = normalize_matrix(
                    values,
                    method=params.get('normalization_method', 'minmax'),
                    criteria_types=criteria_types
                )

            weights = np.array([crit.weight for crit in criteria])
            weights = weights / np.sum(weights) if np.sum(weights) > 0 else np.ones(n_criteria) / n_criteria

            pref_functions, p_values, q_values, s_values = self._prepare_preference_functions(
                params, criteria
            )

            preference_matrix = self._calculate_preference_matrix(
                values, weights, criteria, n_alternatives, n_criteria,
                pref_functions, p_values, q_values, s_values
            )

            positive_flow, negative_flow, net_flow = self._calculate_preference_flows(
                preference_matrix, n_alternatives
            )    

            variant = params.get('variant', 'II')

            if variant == 'I':
                # PROMETHEE I: Partial ranking
                outranking_matrix, incomparabilities = self._promethee_i_ranking(
                    positive_flow, negative_flow, n_alternatives)
                
                metadata = {
                    'positive_flow': positive_flow.tolist(),
                    'negative_flow': negative_flow.tolist(),
                    'net_flow': net_flow.tolist(),
                    'preference_matrix': preference_matrix.tolist(),
                    'outranking_matrix': outranking_matrix.tolist(),
                    'incomparabilities': [(int(i), int(j)) for i, j in incomparabilities]
                }

                scores = net_flow
            
            else:
                # PROMETHEE II: Complete ranking based on net flow
                metadata = {
                    'positive_flow': positive_flow.tolist(),
                    'negative_flow': negative_flow.tolist(),
                    'net_flow': net_flow.tolist(),
                    'preference_matrix': preference_matrix.tolist()
                }
                
                scores = net_flow
            
            result = Result(
                method_name=f"{self.name}-{variant}",
                alternative_ids=[alt.id for alt in alternatives],
                alternative_names=[alt.name for alt in alternatives],
                scores=scores,
                parameters=params,
                metadata=metadata
            )

            return result
        
        except ValidationError as e:
            raise e
        except Exception as e:
            raise MethodError(
                message=f"Error executing the PROMETHEE method: {str(e)}",
                method_name=self.name
            ) from e
        
    def _prepare_preference_functions(self, params: Dict[str, Any],
                                      criteria: List[Criteria]) -> Tuple[Dict[str, int],
                                                                    Dict[str, float],
                                                                    Dict[str, float],
                                                                    Dict[str, float]]:
        """
        Prepares the preference functions and thresholds for each criterion.
        
        Args:
            params: Dictionary of parameters for the method
            criteria: List of criteria objects
            
        Returns:
            Tuple containing dictionaries for preference functions and thresholds (p, q, s)
        """
        # Get default preference function
        default_func = params.get('default_preference_function', 'v-shape')
        if default_func not in self.PREFERENCE_FUNCTIONS:
            default_func = 'v-shape'  # Fallback to v-shape if invalid
        default_func_id = self.PREFERENCE_FUNCTIONS[default_func]
        
        # Default thresholds
        default_p = 0.2  # Preference threshold
        default_q = 0.1  # Indifference threshold
        default_s = 0.15  # Gaussian threshold
        
        # Initialize result dictionaries
        pref_functions = {}
        p_values = {}
        q_values = {}
        s_values = {}
        
        # Get specific functions and thresholds with null safety
        specific_funcs = params.get('preference_functions') or {}
        p_thresholds = params.get('p_thresholds') or {}
        q_thresholds = params.get('q_thresholds') or {}
        s_thresholds = params.get('s_thresholds') or {}
        
        # Assign functions and thresholds for each criterion
        for crit in criteria:
            crit_id = crit.id
            
            # Preference function
            if crit_id in specific_funcs and specific_funcs[crit_id] in self.PREFERENCE_FUNCTIONS:
                pref_functions[crit_id] = self.PREFERENCE_FUNCTIONS[specific_funcs[crit_id]]
            else:
                pref_functions[crit_id] = default_func_id
            
            # Get thresholds with safeguards
            p_values[crit_id] = p_thresholds.get(crit_id, default_p)
            q_values[crit_id] = q_thresholds.get(crit_id, default_q)
            s_values[crit_id] = s_thresholds.get(crit_id, default_s)
            
            # Ensure p ≥ q
            if p_values[crit_id] < q_values[crit_id]:
                p_values[crit_id] = q_values[crit_id]
        
        return pref_functions, p_values, q_values, s_values
    
    def _calculate_preference_matrix(self, values: np.ndarray, weights: np.ndarray,
                                  criteria: List[Criteria], n_alternatives: int, n_criteria: int,
                                  pref_functions: Dict[str, int], p_values: Dict[str, float],
                                  q_values: Dict[str, float], s_values: Dict[str, float]) -> np.ndarray:
        """
        Calculates the aggregated preference matrix.
        
        Args:
            values: Matrix of normalized values
            weights: Vector of normalized weights
            criteria: List of criteria
            n_alternatives: Number of alternatives
            n_criteria: Number of criteria
            pref_functions: Dictionary of preference functions by criterion
            p_values: Dictionary of preference thresholds by criterion
            q_values: Dictionary of indifference thresholds by criterion
            s_values: Dictionary of Gaussian thresholds by criterion
            
        Returns:
            np.ndarray: Aggregated preference matrix
        """
        # Initialize preference matrix
        preference_matrix = np.zeros((n_alternatives, n_alternatives))
        
        # For each pair of alternatives
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i == j:  # Skip self-comparison
                    continue
                    
                # Calculate weighted preference sum for this pair
                preference_sum = 0.0
                
                # For each criterion
                for k in range(n_criteria):
                    crit = criteria[k]
                    crit_id = crit.id
                    
                    # Calculate difference between alternatives for this criterion
                    diff = values[i, k] - values[j, k]
                    
                    # Invert the difference if criterion is cost (minimize)
                    if crit.is_cost_criteria():
                        diff = -diff
                    
                    # Apply preference function
                    p_threshold = p_values[crit_id]
                    q_threshold = q_values[crit_id]
                    s_threshold = s_values[crit_id]
                    func_type = pref_functions[crit_id]
                    
                    preference = self._apply_preference_function(
                        diff, func_type, p_threshold, q_threshold, s_threshold
                    )
                    
                    # Add weighted preference to the sum
                    preference_sum += weights[k] * preference
                
                # Store the aggregated preference
                preference_matrix[i, j] = preference_sum
        
        return preference_matrix
    
    def _apply_preference_function(self, diff: float, func_type: int,
                             p: float, q: float, s: float) -> float:
        """
        Implementación revisada basada en la definición original de Brans & Vincke
        """
        # Para diferencias negativas
        if diff <= 0:
            return 0.0
        
        # Para cada tipo de función
        if func_type == 1:  # Usual
            return 1.0
            
        elif func_type == 2:  # U-shape (quasi)
            return 0.0 if diff <= q else 1.0
            
        elif func_type == 3:  # V-shape (linear)
            # Manejo más preciso de casos límite
            if p <= 0 or diff >= p:
                return 1.0
            else:
                return diff / p
                
        elif func_type == 4:  # Level
            if diff <= q:
                return 0.0
            elif diff <= p:
                return 0.5
            else:
                return 1.0
                
        elif func_type == 5:  # V-shape with indifference
            if diff <= q:
                return 0.0
            elif diff <= p:
                # Cálculo más preciso para valores cercanos a los umbrales
                return (diff - q) / (p - q)
            else:
                return 1.0
                
        elif func_type == 6:  # Gaussian
            if diff <= 0:
                return 0.0
            else:
                # Cálculo ajustado para mejor discriminación
                return 1.0 - math.exp(-(diff * diff) / (2 * s * s))
        
        return 0.0
    
    def _calculate_preference_flows(self, preference_matrix: np.ndarray, 
                                 n_alternatives: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates the positive, negative, and net preference flows.
        
        Args:
            preference_matrix: Matrix of preference values
            n_alternatives: Number of alternatives
            
        Returns:
            Tuple with positive, negative, and net flows
        """
        # Positive flow (sum by rows / (n-1))
        positive_flow = np.sum(preference_matrix, axis=1) / (n_alternatives - 1)
        
        # Negative flow (sum by columns / (n-1))
        negative_flow = np.sum(preference_matrix, axis=0) / (n_alternatives - 1)
        
        # Net flow (positive - negative)
        net_flow = positive_flow - negative_flow
        
        return positive_flow, negative_flow, net_flow
    
    def _promethee_i_ranking(self, positive_flow: np.ndarray, negative_flow: np.ndarray, 
                        n_alternatives: int) -> Tuple[np.ndarray, List[Tuple[int, int]]]:
        """
        Corregida según la teoría original de Brans & Vincke
        """
        outranking_matrix = np.zeros((n_alternatives, n_alternatives))
        incomparabilities = []
        
        # Tolerancia para comparaciones numéricas
        epsilon = 1e-6
        
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i == j:
                    continue
                    
                phi_plus_better = positive_flow[i] > positive_flow[j] + epsilon
                phi_plus_equal = abs(positive_flow[i] - positive_flow[j]) <= epsilon
                phi_minus_better = negative_flow[i] < negative_flow[j] - epsilon
                phi_minus_equal = abs(negative_flow[i] - negative_flow[j]) <= epsilon
                
                # Caso 1: i supera estrictamente a j
                if (phi_plus_better and phi_minus_better) or \
                (phi_plus_better and phi_minus_equal) or \
                (phi_plus_equal and phi_minus_better):
                    outranking_matrix[i, j] = 1
                
                # Caso 2: i es indiferente a j
                elif phi_plus_equal and phi_minus_equal:
                    outranking_matrix[i, j] = 0.5
                    outranking_matrix[j, i] = 0.5
                
                # Caso 3: i es incomparable con j (conflicto entre flujos)
                elif (phi_plus_better and phi_minus_better) or \
                    (phi_plus_better and phi_minus_better):
                    outranking_matrix[i, j] = -1
                    if (j, i) not in incomparabilities:
                        incomparabilities.append((i, j))
        
        return outranking_matrix, incomparabilities
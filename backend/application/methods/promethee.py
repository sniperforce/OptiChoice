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
            'normalization_method': 'minimax',
            'normalize_matrix': True
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
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
            if parameters['normalization_method'] not in ['minimax', 'sum', 'max', 'vector']:
                return False

        if 'normalize_matrix' in parameters:
            if not isinstance(parameters['normalize_matrix'], bool):
                return False
        
        return True

    def execute(self, decision_matrix: DecisionMatrix,
                parameters: Optional[Dict[str, Any]] = None) -> Result:
        try:
            params = self._prepare_execution(decision_matrix, parameters)

            alternatives = decision_matrix.alternative
            criteria = decision_matrix.criteria
            values = decision_matrix.values.copy()

            n_alternatives = len(alternatives)
            n_criteria = len(criteria)

            if params.get('normalize_matrix', True):
                values = normalize_matrix(
                    values=values,
                    criteria=criteria,
                    method=params.get('normalization_method', 'minmax')
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
                    'incomparabilities': [list(inc) for inc in incomparabilities]
                }

                scores = net_flow
            
            else:
                # PROMETHEE  II: Complete ranking based on net flow
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
                message=f"Error executing the PROMETHEE method:{str(e)}",
                method_name=self.name
            ) from e
        
    def _prepare_preference_functions(self, params: Dict[str, Any],
                                      criteria: List[Criteria]) -> Tuple[Dict[str, int],
                                                                    Dict[str, float],
                                                                    Dict[str, float],
                                                                    Dict[str, float]]:
        """
            Prepares the preference functions and thresholds for each criterion

            Returns:
                Tuple with dictionaries of preference functinos and p, q, and s thresholds
        """
        default_func = params.get('default_preference_function', 'v-shape')
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
        
        # Specific preference functions (if provided)
        specific_funcs = params.get('preference_functions', {})
        
        # Specific thresholds (if provided)
        p_thresholds = params.get('p_thresholds', {})
        q_thresholds = params.get('q_thresholds', {})
        s_thresholds = params.get('s_thresholds', {})
        
        # Assign functions and thresholds for each criterion
        for crit in criteria:
            # Preference function
            if specific_funcs and crit.id in specific_funcs:
                func_name = specific_funcs[crit.id]
                pref_functions[crit.id] = self.PREFERENCE_FUNCTIONS[func_name]
            else:
                pref_functions[crit.id] = default_func_id
            
            # Preference threshold (p)
            p_values[crit.id] = p_thresholds.get(crit.id, default_p)
            
            # Indifference threshold (q)
            q_values[crit.id] = q_thresholds.get(crit.id, default_q)
            
            # Gaussian threshold (s)
            s_values[crit.id] = s_thresholds.get(crit.id, default_s)
        
        return pref_functions, p_values, q_values, s_values
    
    def _calculate_preference_matrix(self, values: np.ndarray, weights: np.ndarray,
                                  criteria: List[Criteria], n_alternatives: int, n_criteria: int,
                                  pref_functions: Dict[str, int], p_values: Dict[str, float],
                                  q_values: Dict[str, float], s_values: Dict[str, float]) -> np.ndarray:
        """
        Calculates the aggregated preference matrix.
        
        Args:
            values: Matrix of normalized values.
            weights: Vector of normalized weights.
            criteria: List of criteria.
            n_alternatives: Number of alternatives.
            n_criteria: Number of criteria.
            pref_functions: Dictionary of preference functions by criterion.
            p_values: Dictionary of preference thresholds by criterion.
            q_values: Dictionary of indifference thresholds by criterion.
            s_values: Dictionary of Gaussian thresholds by criterion.
            
        Returns:
            np.ndarray: Aggregated preference matrix.
        """
        # Initialize preference matrix
        preference_matrix = np.zeros((n_alternatives, n_alternatives))
        
        # For each pair of alternatives
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:  # Don't compare an alternative with itself
                    preference_sum = 0.0
                    
                    # For each criterion
                    for k in range(n_criteria):
                        crit = criteria[k]
                        
                        # Calculate difference between alternatives
                        diff = values[i, k] - values[j, k]
                        
                        # Invert the difference if the criterion is cost
                        if crit.is_cost_criteria():
                            diff = -diff
                        
                        # Calculate preference according to the corresponding function
                        preference = self._apply_preference_function(
                            diff,
                            pref_functions[crit.id],
                            p_values[crit.id],
                            q_values[crit.id],
                            s_values[crit.id]
                        )
                        
                        # Add weighted preference
                        preference_sum += weights[k] * preference
                    
                    # Save aggregated preference
                    preference_matrix[i, j] = preference_sum
        
        return preference_matrix
    
    def _apply_preference_function(self, diff: float, func_type: int,
                                p: float, q: float, s: float) -> float:
        # If the difference is negative, there is no preference
        if diff <= 0:
            return 0.0
        
        # Apply the corresponding preference function
        if func_type == 1:  # Usual
            return 1.0
            
        elif func_type == 2:  # U-shape
            return 0.0 if diff <= q else 1.0
            
        elif func_type == 3:  # V-shape
            return min(diff / p, 1.0) if p > 0 else (0.0 if diff == 0 else 1.0)
            
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
                return (diff - q) / (p - q)
            else:
                return 1.0
                
        elif func_type == 6:  # Gaussian
            if diff <= 0:
                return 0.0
            else:
                return 1.0 - math.exp(-(diff * diff) / (2 * s * s))
        
        # By default, return 0
        return 0.0
    
    def _calculate_preference_flows(self, preference_matrix: np.ndarray, 
                                 n_alternatives: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculates the positive, negative, and net preference flows.
        
        Returns:
            Tuple with positive, negative, and net flows.
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
        Establishes the partial ranking according to PROMETHEE I.
        
        Returns:
            Tuple with the outranking matrix and list of incomparabilities.
        """
        # Initialize outranking matrix
        outranking_matrix = np.zeros((n_alternatives, n_alternatives))
        
        # List of pairs of incomparable alternatives
        incomparabilities = []
        
        # For each pair of alternatives
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:
                    # Check outranking conditions
                    if ((positive_flow[i] > positive_flow[j] and negative_flow[i] < negative_flow[j]) or
                        (positive_flow[i] == positive_flow[j] and negative_flow[i] < negative_flow[j]) or
                        (positive_flow[i] > positive_flow[j] and negative_flow[i] == negative_flow[j])):
                        # i outranks j
                        outranking_matrix[i, j] = 1
                    elif ((positive_flow[i] == positive_flow[j] and negative_flow[i] == negative_flow[j])):
                        # i is indifferent to j
                        outranking_matrix[i, j] = 0.5
                        outranking_matrix[j, i] = 0.5
                    elif ((positive_flow[i] > positive_flow[j] and negative_flow[i] > negative_flow[j]) or
                          (positive_flow[i] < positive_flow[j] and negative_flow[i] < negative_flow[j])):
                        # i is incomparable with j
                        if (j, i) not in incomparabilities:  # Avoid duplicates
                            incomparabilities.append((i, j))
        
        return outranking_matrix, incomparabilities

                                                                    




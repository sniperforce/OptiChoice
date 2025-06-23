"""
Module that implements the ELECTRE (ELimination Et Choix Traduisant la REalité) method.

ELECTRE is a family of multi-criteria decision methods based on outranking relations
between alternatives, developed by Bernard Roy and his team.
"""
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np

from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from application.methods.method_interface import MCDMMethodInterface
from utils.exceptions import MethodError, ValidationError
from utils.normalization import normalize_matrix

class ELECTREMethod(MCDMMethodInterface):
    """
    Implementation of the ELECTRE (ELimination Et Choix Traduisant la REalité) method.
    
    ELECTRE is based on the concept of outranking relations between alternatives.
    One alternative outranks another if it is at least as good as the other in most criteria
    and not significantly worse in any criterion.
    
    This implementation provides different variants of the ELECTRE method:
    - ELECTRE I: Used for selection problems
    - ELECTRE III: Incorporates pseudo-criteria and better handles imprecision
    """

    @property
    def name(self) -> str:
        return "ELECTRE"
    
    @property
    def full_name(self) -> str:
        return "Elimination Et Choix Traduisant la Realité"
    
    @property
    def description(self) -> str:
        return """
        ELECTRE (ELimination Et Choix Traduisant la REalité) is a family of 
        multi-criteria decision methods developed by Bernard Roy and his team in France.
        
        Main characteristics:
        - Uses the concept of outranking relations
        - Allows expressing preference, indifference, and incomparability between alternatives
        - Considers concordance and discordance thresholds
        - Handles both quantitative and qualitative criteria
        - Different variants (I, II, III, IV, TRI) for different types of problems
        
        ELECTRE is especially useful when non-compensatory aspects need to be considered
        in decision making, that is, when good performance in one criterion does not
        necessarily compensate for poor performance in another.
        """
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            'variant': 'I',
            'concordance_threshold': 0.7, # between 0.5 and 1.0
            'discordance_threshold': 0.3, # between 0.0 and 1.0
            'normalization_method': 'minmax',
            'normalize_matrix': True,
            'preference_threshold': None,   # For ELECTRE III: preference thresholds by criterian (indifference < preference)
            'indifference_threshold': None, # For ELECTRE III: indifference thresholds by criterion
            'veto_thresholds': None,

            # For alternatives that neither dominate nor are dominated, how to calculate score
            # 'net_flow': net flow (dominance - dominated)
            # 'pure_dominance': only consider when it dominates
            # 'mixed': weighted average between dominance and not being dominated
            'scoring_method': 'net_flow',
            'dominance_weight': 0.6 # For scoring_mmethod='mixed', weight of dominance (0.0-1.0)
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        if 'variant' in parameters:
            if parameters['variant'] not in ['I', 'III']:
                return False
            
        if 'concordance_threshold' in parameters:
            threshold = parameters['concordance_threshold']
            if not isinstance(threshold, (int, float)) or threshold < 0.5 or threshold > 1.0:
                return False
        
        if 'discordance_threshold' in parameters:
            threshold = parameters['discordance_threshold']
            if not isinstance(threshold, (int, float)) or threshold < 0.0 or threshold > 1.0:
                return False
            
        if 'normalization_method' in parameters:
            method = parameters['normalization_method']
            if method not in ['minmax', 'sum', 'max', 'vector']:
                return False
        
        if 'normalize_matrix' in parameters:
            if not isinstance(parameters['normalize_matrix'], bool):
                return False
        
        if 'scoring_method' in parameters:
            method = parameters['scoring_method']
            if method not in ['net_flow', 'pure_dominance', 'mixed']:
                return False
        
        if 'dominance_weight' in parameters:
            weight = parameters['dominance_weight']
            if not isinstance(weight, (int, float)) or weight < 0.0 or weight > 1.0:
                return False
        
        variant = parameters.get('variant', 'I')
        if variant == 'III':
            for threshold_name in ['preference_thresholds', 'indifference_thresholds', 'veto_thresholds']:
                if threshold_name in parameters and parameters[threshold_name] is not None:
                    thresholds = parameters[threshold_name]
                    if not isinstance(thresholds, dict):
                        return False
                    
                    for key, value in thresholds.items():
                        if not isinstance(value, (int, float)) or value < 0:
                            return False
            
            if (parameters.get('preference_thresholds') is not None and 
                parameters.get('indifference_thresholds') is not None):
                
                p_thresholds = parameters['preference_thresholds']
                i_thresholds = parameters['indifference_thresholds']
                
                for key in set(p_thresholds.keys()).intersection(i_thresholds.keys()):
                    if p_thresholds[key] < i_thresholds[key]:
                        return False
        
        return True
    
    def execute(self, decision_matrix: DecisionMatrix,
                parameters: Optional[Dict[str, Any]] = None) -> Result:
        try:
            params = self._prepare_execution(decision_matrix, parameters)

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
            
            # Get criteria weights and normalize them
            weights = np.array([crit.weight for crit in criteria])
            weights = weights / np.sum(weights) if np.sum(weights) > 0 else np.ones(n_criteria) / n_criteria

            variant = params.get('variant', 'I')

            if variant == 'I':
                outranking_matrix, dominance_matrix, non_dominated = self._execute_electre_i(
                    values, weights, n_alternatives, n_criteria, params
                )

                metadata = {
                    'outranking_matrix': outranking_matrix.tolist(),
                    'dominance_matrix': dominance_matrix.tolist(),
                    'non_dominated_alternatives': list(non_dominated)
                }
            
            elif variant == 'III':
                credibility_matrix, distillation_ranks, net_flows = self._execute_electre_iii(
                    values, weights, alternatives, criteria, n_alternatives, n_criteria, params)
                
                metadata = {
                    'credibility_matrix': credibility_matrix.tolist(),
                    'ascending_distillation': distillation_ranks['ascending'].tolist(),
                    'descending_distillation': distillation_ranks['descending'].tolist(),
                    'net_flows': net_flows.tolist()
                }
                
            else:
                raise ValidationError(
                    message=f"ELECTRE variant not implemented: {variant}",
                    errors=[f"Available variants are: 'I', 'III'"]
                )
            
            scores = self._calculate_scores(
                variant, n_alternatives, outranking_matrix if variant == 'I' else credibility_matrix, params
            )

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
                message=f"Error executing the ELECTRE method: {str(e)}",
                method_name=self.name
            ) from e
        
    def _execute_electre_i(self, values: np.ndarray, weights: np.ndarray,
                           n_alternatives: int, n_criteria: int, 
                           params: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray, Set[int]]:
        concordance_threshold = params.get('concordance_threshold', 0.7)
        discordance_threshold = params.get('discordance_threshold', 0.3)

        # Initialize matrices
        concordance_matrix = np.zeros((n_alternatives, n_alternatives))
        discordance_matrix = np.zeros((n_alternatives, n_alternatives))
        outranking_matrix = np.zeros((n_alternatives, n_alternatives))

        # Calculate concordance and discordance matrices
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:
                    # Calculate concordance set (indices where i is at least as good as j)
                    concordance_indices = []
                    for k in range(n_criteria):
                        if values[i, k] >= values[j, k]:
                            concordance_indices.append(k)

                    if concordance_indices:
                        concordance_matrix[i, j] = np.sum(weights[concordance_indices])

                    discordance_indices = []
                    for k in range(n_criteria):
                        if values[i, k] < values[j, k]:
                            discordance_indices.append(k)

                    if discordance_indices:
                        max_diff = np.max([values[j, k] - values[i, k] for k in discordance_indices])
                        max_range = np.max(values[:, discordance_indices]) - np.min(values[:, discordance_indices])
                        discordance_matrix[i, j] = max_diff / max_range if max_range > 0 else 0

        # Determine outranking realtions
        for i in range (n_alternatives):
            for j in range(n_alternatives):
                if i != j:
                    # i outranks j if concordance >= threshold and discordance <= threshold
                    if (concordance_matrix[i, j] >= concordance_threshold and 
                        discordance_matrix[i, j] <= discordance_threshold):
                        outranking_matrix[i, j] = 1
        
        # Identify dominant and dominated alternatives
        dominance_matrix = np.zeros((n_alternatives, n_alternatives))
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:
                    # i dominates j if i outranks j and j does not outrank i
                    if outranking_matrix[i, j] == 1 and outranking_matrix[j, i] == 0:
                        dominance_matrix[i, j] = 1
        
        # Identify non-dominated alternatives (kernel)
        dominated = set()
        for j in range(n_alternatives):
            for i in range(n_alternatives):
                if dominance_matrix[i, j] == 1:
                    dominated.add(j)
                    break
        
        non_dominated = set(range(n_alternatives)) - dominated

        return outranking_matrix, dominance_matrix, non_dominated
    
    def _execute_electre_iii(self, values: np.ndarray, weights: np.ndarray,
                             alternatives: List[Any], criteria: List[Any],
                             n_alternatives: int, n_criteria: int,
                             params: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, np.ndarray], np.ndarray]:
        # Get thresholds from parameters or use default values
        preference_thresholds = self._get_thresholds(params.get('preference_thresholds'), criteria, 0.2)
        indifference_thresholds = self._get_thresholds(params.get('indifference_thresholds'), criteria, 0.1)
        veto_thresholds = self._get_thresholds(params.get('veto_thresholds'), criteria, 0.5)
        
        # Initialize matrices
        concordance_matrix = np.zeros((n_alternatives, n_alternatives))
        credibility_matrix = np.zeros((n_alternatives, n_alternatives))
        
        # Calculate partial concordance indices by criterion
        concordance_by_criteria = np.zeros((n_alternatives, n_alternatives, n_criteria))
        
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:  # Don't compare an alternative with itself
                    for k in range(n_criteria):
                        # Difference between alternatives for this criterion
                        diff = values[i, k] - values[j, k]
                        p_threshold = preference_thresholds[criteria[k].id]
                        i_threshold = indifference_thresholds[criteria[k].id]
                        
                        # Calculate partial concordance index
                        if diff >= p_threshold:
                            # Strict preference: i is clearly better than j
                            concordance_by_criteria[i, j, k] = 1.0
                        elif diff <= -i_threshold:
                            # No preference: j is clearly better than i
                            concordance_by_criteria[i, j, k] = 0.0
                        else:
                            # Weak preference: intermediate zone with linear interpolation
                            concordance_by_criteria[i, j, k] = (diff + i_threshold) / (p_threshold + i_threshold)
        
        # Calculate global concordance index
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:
                    # Weighted sum of partial concordance indices
                    concordance_matrix[i, j] = np.sum(weights * concordance_by_criteria[i, j])
        
        # Calculate discordance indices by criterion
        discordance_by_criteria = np.zeros((n_alternatives, n_alternatives, n_criteria))
        
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:
                    for k in range(n_criteria):
                        # Difference between alternatives for this criterion (from j to i)
                        diff = values[j, k] - values[i, k]
                        p_threshold = preference_thresholds[criteria[k].id]
                        v_threshold = veto_thresholds[criteria[k].id]
                        
                        # Calculate discordance index
                        if diff <= p_threshold:
                            # No discordance: i is not significantly worse than j
                            discordance_by_criteria[i, j, k] = 0.0
                        elif diff >= v_threshold:
                            # Complete veto: i is much worse than j in this criterion
                            discordance_by_criteria[i, j, k] = 1.0
                        else:
                            # Partial discordance: linear interpolation
                            discordance_by_criteria[i, j, k] = (diff - p_threshold) / (v_threshold - p_threshold)
        
        # Calculate credibility index
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i != j:
                    # Initially equal to the concordance index
                    credibility_matrix[i, j] = concordance_matrix[i, j]
                    
                    # Identify criteria with discordance
                    discord_criteria = []
                    for k in range(n_criteria):
                        if discordance_by_criteria[i, j, k] > concordance_matrix[i, j]:
                            discord_criteria.append(k)
                    
                    # Apply veto effect (reduce credibility due to strong discordance)
                    if discord_criteria:
                        for k in discord_criteria:
                            disc_factor = (1 - discordance_by_criteria[i, j, k]) / (1 - concordance_matrix[i, j])
                            credibility_matrix[i, j] *= disc_factor
        
        # Perform descending and ascending distillation
        distillation_ranks = {
            'descending': self._descending_distillation(credibility_matrix, n_alternatives),
            'ascending': self._ascending_distillation(credibility_matrix, n_alternatives)
        }
        
        # Calculate net flows (similar to PROMETHEE)
        positive_flow = np.sum(credibility_matrix, axis=1) / (n_alternatives - 1)  # Dominance
        negative_flow = np.sum(credibility_matrix, axis=0) / (n_alternatives - 1)  # Weakness
        net_flows = positive_flow - negative_flow
        
        return credibility_matrix, distillation_ranks, net_flows
    
    def _get_thresholds(self, thresholds_dict: Optional[Dict[str, float]], 
                      criteria: List[Any], default_value: float) -> Dict[str, float]:
        result = {}
        
        if thresholds_dict is None:
            # Use default value for all criteria
            for crit in criteria:
                result[crit.id] = default_value
        else:
            # Use provided values or default values
            for crit in criteria:
                result[crit.id] = thresholds_dict.get(crit.id, default_value)
        
        return result
    
    def _descending_distillation(self, credibility_matrix: np.ndarray, 
                              n_alternatives: int) -> np.ndarray:
        remaining = set(range(n_alternatives))
        ranks = np.zeros(n_alternatives, dtype=int)
        current_rank = 1
        
        while remaining:
            if len(remaining) == 1:
                # If only one alternative remains, assign it the next rank
                last_alt = list(remaining)[0]
                ranks[last_alt] = current_rank
                break
            
            # Convert set to list for indexing
            remaining_list = list(remaining)
            
            # Create submatrix with remaining alternatives
            submatrix = np.zeros((len(remaining), len(remaining)))
            for i, orig_i in enumerate(remaining_list):
                for j, orig_j in enumerate(remaining_list):
                    if orig_i != orig_j:
                        submatrix[i, j] = credibility_matrix[orig_i, orig_j]
            
            # Calculate discrimination threshold
            max_cred = np.max(submatrix)
            min_cred = np.min(submatrix[submatrix > 0]) if np.any(submatrix > 0) else 0
            threshold = max_cred - 0.15 * (max_cred - min_cred)
            
            # Calculate qualification for each alternative
            qualification = np.zeros(len(remaining))
            for i in range(len(remaining)):
                # Count how many alternatives are outranked by i
                strength = np.sum(submatrix[i, :] >= threshold)
                # Count how many alternatives outrank i
                weakness = np.sum(submatrix[:, i] >= threshold)
                # Net qualification
                qualification[i] = strength - weakness
            
            # Find the alternatives with highest qualification
            max_qual = np.max(qualification)
            best_alternatives = set()
            for i, qual in enumerate(qualification):
                if qual == max_qual:
                    best_alternatives.add(remaining_list[i])
            
            # Assign rank to the best alternatives and remove them from the remaining set
            for alt in best_alternatives:
                ranks[alt] = current_rank
                remaining.remove(alt)
            
            # Increment rank for the next iteration
            current_rank += len(best_alternatives)
        
        return ranks
    
    
    def _ascending_distillation(self, credibility_matrix: np.ndarray, 
                             n_alternatives: int) -> np.ndarray:
        
        # Similar to descending distillation, but with inverse logic
        remaining = set(range(n_alternatives))
        ranks = np.zeros(n_alternatives, dtype=int)
        current_rank = n_alternatives
        
        while remaining:
            if len(remaining) == 1:
                # If only one alternative remains, assign it the next rank
                last_alt = list(remaining)[0]
                ranks[last_alt] = current_rank
                break
            
            # Convert set to list for indexing
            remaining_list = list(remaining)
            
            # Create submatrix with remaining alternatives
            submatrix = np.zeros((len(remaining), len(remaining)))
            for i, orig_i in enumerate(remaining_list):
                for j, orig_j in enumerate(remaining_list):
                    if orig_i != orig_j:
                        submatrix[i, j] = credibility_matrix[orig_i, orig_j]
            
            # Calculate discrimination threshold
            max_cred = np.max(submatrix)
            min_cred = np.min(submatrix[submatrix > 0]) if np.any(submatrix > 0) else 0
            threshold = max_cred - 0.15 * (max_cred - min_cred)
            
            # Calculate qualification for each alternative
            qualification = np.zeros(len(remaining))
            for i in range(len(remaining)):
                # Count how many alternatives are outranked by i
                strength = np.sum(submatrix[i, :] >= threshold)
                # Count how many alternatives outrank i
                weakness = np.sum(submatrix[:, i] >= threshold)
                # Net qualification
                qualification[i] = strength - weakness
            
            # Find the alternatives with lowest qualification
            min_qual = np.min(qualification)
            worst_alternatives = set()
            for i, qual in enumerate(qualification):
                if qual == min_qual:
                    worst_alternatives.add(remaining_list[i])
            
            # Assign rank to the worst alternatives and remove them from the remaining set
            for alt in worst_alternatives:
                ranks[alt] = current_rank
                remaining.remove(alt)
            
            # Decrement rank for the next iteration
            current_rank -= len(worst_alternatives)
        
        return ranks
    
    def _calculate_scores(self, variant: str, n_alternatives: int, 
                        relation_matrix: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        
        scoring_method = params.get('scoring_method', 'net_flow')
        
        if variant == 'I':
            # For ELECTRE I: count outranking relations
            dominance_count = np.sum(relation_matrix, axis=1)  # How many alternatives it dominates
            dominated_count = np.sum(relation_matrix, axis=0)  # By how many alternatives it is dominated
            
            if scoring_method == 'net_flow':
                # Net flow method (similar to PROMETHEE)
                return (dominance_count - dominated_count) / (n_alternatives - 1)
            
            elif scoring_method == 'pure_dominance':
                # Only consider how many alternatives it dominates
                return dominance_count / (n_alternatives - 1)
            
            elif scoring_method == 'mixed':
                # Weighted average
                dominance_weight = params.get('dominance_weight', 0.6)
                non_dominance_weight = 1.0 - dominance_weight
                
                dominance_score = dominance_count / (n_alternatives - 1)
                non_dominance_score = 1.0 - (dominated_count / (n_alternatives - 1))
                
                return dominance_weight * dominance_score + non_dominance_weight * non_dominance_score
            
        elif variant == 'III':
            # For ELECTRE III: use distillation results
            # Use credibility matrix to calculate flows
            positive_flow = np.sum(relation_matrix, axis=1) / (n_alternatives - 1)
            negative_flow = np.sum(relation_matrix, axis=0) / (n_alternatives - 1)
            
            if scoring_method == 'net_flow':
                # Net flow (positive - negative)
                return positive_flow - negative_flow
            
            elif scoring_method == 'pure_dominance':
                # Only positive flow
                return positive_flow
            
            elif scoring_method == 'mixed':
                # Weighted combination of flows
                dominance_weight = params.get('dominance_weight', 0.6)
                non_dominance_weight = 1.0 - dominance_weight
                
                return dominance_weight * positive_flow + non_dominance_weight * (1.0 - negative_flow)
        
        # By default, return net flow
        return np.zeros(n_alternatives)

    

        

        


                        

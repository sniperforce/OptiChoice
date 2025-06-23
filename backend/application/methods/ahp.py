"""
    Module that implements the AHP (Analytic Hierarchy Process) method

    AHP is a multi-criteria decision method developed by Thomas L. Saaty that uses 
    pairwise comparisons, eigenvector, and consistency analysis to establish priorities
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from numpy.linalg import eigvals, eig

from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from application.methods.method_interface import MCDMMethodInterface
from utils.exceptions import MethodError, ValidationError
from utils.normalization import normalize_matrix

class AHPMethod(MCDMMethodInterface):
    """
        Implementation of the AHP (Analytic Hierarchy Process) method.
    
        AHP uses pairwise comparisons to establish the relative importance between criteria
        and the relative performance between alternatives. Comparisons are translated into weights through
        the calculation of eigenvectors, and the consistency of the judgments is verified.
        
        Saaty's fundamental scale uses values from 1 to 9 to indicate the intensity of preference:
        1: Equal importance
        3: Moderate importance
        5: Strong importance 
        7: Very strong importance
        9: Extreme importance
        (Intermediate values 2, 4, 6, 8 can also be used)
    """
    # Random Consistency Index(RI)
    # These Values are constants defined by Saaty for different matrix sizes
    _RANDOM_CONSISTENCY_INDEX = {
        1: 0.00,
        2: 0.00,
        3: 0.58,
        4: 0.90,
        5: 1.12,
        6: 1.24,
        7: 1.32,
        8: 1.41,
        9: 1.45,
        10: 1.49,
        11: 1.51,
        12: 1.48,
        13: 1.56,
        14: 1.57,
        15: 1.59
    }

    @property
    def name(self) -> str:
        return "AHP"
    
    @property
    def full_name(self) -> str:
        return "Analytic Hierarchy Process"

    @property
    def description(self) -> str:
        return """ The Analytic Hierarchy Process (AHP) is a method developed by Thomas L. Saaty 
        for decision-making with multiple criteria. The method decomposes a complex problem 
        into a hierarchy of simpler subproblems, and then synthesizes the results.
        
        Main characteristics:
        - Uses pairwise comparisons between criteria and alternatives
        - Calculates priorities using eigenvectors
        - Verifies the consistency of judgments
        - Allows structuring the problem in a hierarchy
        
        AHP is especially useful when subjective and objective factors must be considered,
        and when the elements of the decision are difficult to quantify or compare directly.""" 
    
    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            # Pairwise comparison matrix for criteria (1 on the diagonal)
            'criteria_comparison_matrix': None,
            
            # List of pairwise comparison matrices for alternatives (one per criterion)
            'alternatives_comparison_matrices': None,
            
            # Acceptable consistency threshold (< 0.1 is generally acceptable)
            'consistency_ratio_threshold': 0.1,
            
            # Method to calculate weights from the comparison matrix (eigenvector/approximate)
            'weight_calculation_method': 'eigenvector',
            
            # If False, direct values from the decision matrix are used without pairwise comparisons
            'use_pairwise_comparison_for_alternatives': True,
            
            # If True, detailed information about consistency is shown
            'show_consistency_details': True,

            # If True, normalize the values before generate automatic comparition matrix
            'normalize_before_comparison': True,

            # Normalization method ('minimax', 'sum', 'max', 'vector')
            'normalization_method': 'minmax'
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        if 'consistency_ratio_threshold' in parameters:
            threshold = parameters['consistency_ratio_threshold']
            if not isinstance(threshold, (int, float)) or threshold <= 0:
                return False
            
        if 'weight_calculation_method' in parameters:
            method = parameters['weight_calculation_method']
            if method not in ['eigenvector', 'approximate']:
                return False
        
        if 'use_pairwise_comparison_for_alternatives' in parameters:
            if not isinstance(parameters['use_pairwise_comparison_for_alternatives'], bool):
                return False
        
        if 'show_consistency_details' in parameters:
            if not isinstance(parameters['show_consistency_details'], bool):
                return False
        
        if parameters.get('criteria_comparison_matrix') is not None:
            criteria_matrix = parameters['criteria_comparison_matrix']
            if not isinstance(criteria_matrix, np.ndarray) and not isinstance(criteria_matrix, list):
                return False
            
            if isinstance(criteria_matrix, list):
                try:
                    criteria_matrix = np.array(criteria_matrix, dtype=float)
                except:
                    return False
            
            if len(criteria_matrix.shape) != 2 or criteria_matrix.shape[0] != criteria_matrix.shape[1]:
                return False
        
        if parameters.get('alternatives_comparison_matrices') is not None:
            alt_matrices = parameters['alternatives_comparison_matrices']
            if not isinstance(alt_matrices, list):
                return False
            
            for matrix in alt_matrices:
                if not isinstance(matrix, np.ndarray) and not isinstance(matrix, list):
                    return False
                
                if isinstance(matrix, list):
                    try:
                        matrix = np.array(matrix, dtype=float)
                    except:
                        return False
                
                if len(matrix.shape) != 2 or matrix.shape[0] != matrix.shape[1]:
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

            # Step 1: Calculate criteria weights
            criteria_weights, criteria_consistency = self._calculate_criteria_weights(
                criteria, params.get('criteria_comparison_matrix'), n_criteria
            )

            # Record consistency information if requested
            consistency_info = {}
            if params.get('show_consistency_details', True):
                consistency_info['criteria_consistency'] = criteria_consistency
            
            # Step 2: Calculate alternative scores for each criterion
            alternative_priorities = np.zeros((n_alternatives, n_criteria))

            # If using pairwise comparison matrices for alternatives
            if params.get('use_pairwise_comparison_for_alternatives', True):
                alternative_priorities, alt_consistency = self._calculate_alternative_priorities_pairwise(
                    alternatives, criteria,
                    params.get('alternatives_comparison_matrices'),
                    n_alternatives, n_criteria, params    
                )

                if params.get('show_consistency_details', True):
                    consistency_info['alternatives_consistency'] = alt_consistency
            else:
                # Use decision matrix values directly
                alternative_priorities = values
            
            # Step 3: Calculate global scores
            scores = np.zeros(n_alternatives)
            for i in range(n_alternatives):
                # Multiply each local priority by the criterion weight and sum
                scores[i] = np.sum(alternative_priorities[i, :] * criteria_weights)

            result = Result(
                method_name=self.name,
                alternative_ids=[alt.id for alt in alternatives],
                alternative_names=[alt.name for alt in alternatives],
                scores=scores,
                parameters=params,
                metadata={
                    'criteria_weights': criteria_weights.tolist(),
                    'alternative_priorities': alternative_priorities.tolist(),
                    'consistency_info': consistency_info
                }
            )
            
            return result
        
        except ValidationError as e:
            raise e
        except Exception as e:
            raise MethodError(
                message=f"Error executing the AHP method: {str(e)}",
                method_name=self.name
            ) from e
        
    def _calculate_criteria_weights(self, criteria, comparison_matrix,
                                    n_criteria) -> Tuple[np.ndarray, Dict]:
        """
            Calculates the criteria weights using a pairwise comparison matrix.

            If no comparison matrix is provided, the weights defined in the criteria
            are used to generate a consistent matrix.

            Returns:
                Tuple[np.ndarrat, Dict]: Criteria weights and consistency information
        """

        consistency_info = {}

        if comparison_matrix is None:
            weights = np.array([crit.weight for crit in criteria])

            # Normalize weights
            sum_weights = np.sum(weights)
            if sum_weights > 0:
                weights = weights / sum_weights
            else:
                weights = np.ones(n_criteria) / n_criteria
            
            # Generate consistent comparsion matrix from weights
            comparison_matrix = np.ones((n_criteria, n_criteria))
            for i in range(n_criteria):
                for j in range(n_criteria):
                    if i != j and weights[j] > 0:
                        comparison_matrix[i, j] = weights[i] / weights[j]
            

            consistency_info = {
                'consistency_index': 0.0,
                'consistency_ratio': 0.0,
                'is_consistent': True,
                'max_eigenvalue': n_criteria,
                'method': 'weights_derived'
            }

            return weights, consistency_info

        if isinstance(comparison_matrix, list):
            comparison_matrix = np.array(comparison_matrix, dtype=float)

        if comparison_matrix.shape != (n_criteria, n_criteria):
            raise ValidationError(
                message='The criteria comparison matrix has incorrect dimensions',
                errors=[f"Expected: ({n_criteria}), ({n_criteria}), Obtained: {comparison_matrix.shape}"]
            )
        
        weights, consistency_info = self._calculate_weights_from_pairwise_matrix(
            comparison_matrix, n_criteria
        )

        return weights, consistency_info
    
    def _calculate_alternative_priorities_pairwise(self, alternatives, criteria,
                                                   comparison_matrices, n_alternatives,
                                                   n_criteria, params) -> Tuple[np.ndarray, List[Dict]]:
        """
            Calculates the priorities of the alternatives for each criterion using pariwise
            comparison matrices

            Returns:
                Tuple[np.ndarray, List[Dict]]: Alternative priorities and consistency information.
        """       
        alternative_priorities = np.zeros((n_alternatives, n_criteria))
        consistency_info = []

        if comparison_matrices is None:
            comparison_matrices = []

            # Obtain the values from the decision matrix
            values = np.zeros((n_alternatives, n_criteria))
            for i in range(n_alternatives):
                for j in range(n_criteria):
                    values[i, j] = alternatives[i].get_metadata(f"criterion_{criteria[j].id}", 1.0)
            
            # Normalize values if requested
            if params.get('normalize_before_comparison', True):
                criteria_types = ['minimize' if crit.optimization_type.value == 'minimize' else 'maximize' 
                  for crit in criteria]

                values = normalize_matrix(
                    values,
                    method=params.get('normalization_method', 'minmax'),
                    criteria_types=criteria_types
                )
            
            # For each criteria, create a comparition matrix  between alternatives
            for j in range(n_criteria):
                alt_comparison = np.ones((n_alternatives, n_alternatives))

                # Get normalized values for this criterion
                criterion_values=values[:, j]

                # Fill the matrix
                for i in range(n_alternatives):
                    for k in range(n_alternatives):
                        if i != k:
                            if criteria[j].is_benefit_criteria():
                                if criterion_values[k] > 0:
                                    alt_comparison[i, k] = criterion_values[i] / criterion_values[k]
                            else:
                                if criterion_values[i] > 0:
                                    alt_comparison[i, k] = criterion_values[k] / criterion_values[i]

                comparison_matrices.append(alt_comparison)           
                        
        # Process each criterion
        for j in range(n_criteria):
            if j < len(comparison_matrices):
                alt_comparison = comparison_matrices[j]

                if isinstance(alt_comparison, list):
                    alt_comparison = np.array(alt_comparison, dtype=float)
                
                if alt_comparison.shape != (n_alternatives, n_alternatives):
                    raise ValidationError(
                        message=f"The comparison matrix for criterion {criteria[j].name} has incorrect dimensions",
                        errors=[f"Expected: ({n_alternatives}, {n_alternatives}), Obtained: {alt_comparison.shape}"]
                    )
                
                priorities, crit_consistency = self._calculate_weights_from_pairwise_matrix(
                    alt_comparison, n_alternatives)
                
                alternative_priorities[:, j] = priorities
                consistency_info.append({
                    'criterion_name': criteria[j].name,
                    'criterion_id': criteria[j].id,
                    **crit_consistency
                })

            else:
                alternative_priorities[:, j] = np.ones(n_alternatives) / n_alternatives

                consistency_info.append({
                    'criterion_name': criteria[j].name,
                    'criterion_id': criteria[j].id,
                    'consistency_index': 0.0,
                    'consistency_ratio': 0.0,
                    'is_consistent': True,
                    'max_eigenvalue': n_alternatives,
                    'method': 'uniform_values'
                })

        return alternative_priorities, consistency_info
    
    def _calculate_weights_from_pairwise_matrix(self, matrix: np.ndarray, size: int) -> Tuple[np.ndarray, Dict]:
        # Ensure the matrix is square of the correct size
        if matrix.shape != (size, size):
            raise ValidationError(
                message="Comparison matrix with incorrect dimensions",
                errors=[f"Expected: ({size}, {size}), Obtained: {matrix.shape}"]
            )
        
        # Eigenvector method (original Saaty)
        # 1. Calculate the principal eigenvector of the matrix
        eigenvalues, eigenvectors = eig(matrix)
        
        # Find the index of the largest eigenvalue
        max_idx = np.argmax(np.real(eigenvalues))
        max_eigenvalue = np.real(eigenvalues[max_idx])
        
        # Get the corresponding eigenvector
        weights = np.real(eigenvectors[:, max_idx])
        
        # Normalize to sum to 1
        weights = weights / np.sum(weights)
        
        # Calculate consistency index (CI)
        consistency_index = (max_eigenvalue - size) / (size - 1) if size > 1 else 0
        
        # Get random consistency index (RI)
        random_ci = self._RANDOM_CONSISTENCY_INDEX.get(size, 1.59)
        
        # Calculate consistency ratio (CR)
        consistency_ratio = consistency_index / random_ci if random_ci > 0 else 0
        
        # Determine if the matrix is consistent
        is_consistent = consistency_ratio <= 0.1  # Saaty's threshold
        
        # Consistency information
        consistency_info = {
            'consistency_index': float(consistency_index),
            'consistency_ratio': float(consistency_ratio),
            'is_consistent': bool(is_consistent),
            'max_eigenvalue': float(max_eigenvalue),
            'method': 'eigenvector'
        }
        
        return weights, consistency_info
    
    def _approximate_weights(self, matrix: np.ndarray, size: int) -> np.ndarray:
        # Calculate geometric mean of each row
        row_products = np.ones(size)
        for i in range(size):
            row_products[i] = np.prod(matrix[i, :]) ** (1.0 / size)
        
        # Normalize to sum to 1
        weights = row_products / np.sum(row_products)
        
        return weights    
    


            
            

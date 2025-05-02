"""
Module that defines the main service for multi-criteria decision making.

This service is responsible for coordinating the application of MCDM methods to projects,
managing results, and providing comparative analysis.
"""
from typing import Dict, List, Any, Optional, Tuple, Set, Union
import time
import numpy as np

from domain.entities.criteria import OptimizationType, ScaleType
from domain.entities.project import Project
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria
from application.methods.method_factory import MCDMMethodFactory
from application.methods.method_interface import MCDMMethodInterface
from utils.exceptions import ServiceError, ValidationError, MethodError


class DecisionService:
    
    def __init__(self):
        self._method_factory = MCDMMethodFactory
    
    def get_available_methods(self) -> List[str]:
        return self._method_factory.get_available_methods()
    
    def get_method_info(self, method_name: str) -> Dict[str, Any]:
        try:
            return self._method_factory.get_method_info(method_name)
        except ValidationError as e:
            raise ServiceError(
                message=f"Error retrieving method information: {e.message}",
                service_name="DecisionService"
            ) from e
    
    def execute_method(self, project: Project, method_name: str, 
                     parameters: Optional[Dict[str, Any]] = None) -> Result:
        try:
            if project.decision_matrix is None:
                raise ServiceError(
                    message="The project has no decision matrix",
                    service_name="DecisionService"
                )
            method = self._method_factory.create_method_with_params(method_name, parameters)
            
            # Execute method and measure time
            start_time = time.time()
            result = method.execute(project.decision_matrix, parameters)
            execution_time = time.time() - start_time
            
            # Update execution time
            result.set_metadata('execution_time', execution_time)
            
            # Save result in the project
            project.add_result(method_name, result)
            
            return result
            
        except (ValidationError, MethodError) as e:
            raise ServiceError(
                message=f"Error executing method {method_name}: {e.message}",
                service_name="DecisionService"
            ) from e
        except Exception as e:
            raise ServiceError(
                message=f"Unexpected error executing method {method_name}: {str(e)}",
                service_name="DecisionService"
            ) from e
    
    def execute_all_methods(self, project: Project, 
                         parameters: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Result]:
        results = {}
        errors = []
        parameters = parameters or {}
        
        available_methods = self.get_available_methods()
        
        for method_name in available_methods:
            try:
                method_params = parameters.get(method_name)
        
                result = self.execute_method(project, method_name, method_params)
            
                results[method_name] = result
                
            except ServiceError as e:
                errors.append(f"{method_name}: {e.message}")
        
        if errors:
            for result in results.values():
                result.set_metadata('execution_errors', errors)
                
            if not results:
                raise ServiceError(
                    message=f"Could not execute any MCDM method: {'; '.join(errors)}",
                    service_name="DecisionService"
                )
        
        return results
    
    def compare_methods(self, project: Project, 
                      method_names: Optional[List[str]] = None) -> Dict[str, Any]:
        try:
            if not project.results:
                raise ServiceError(
                    message="The project has no MCDM method results",
                    service_name="DecisionService"
                )
            
            available_results = set(project.results.keys())
            if method_names:
                methods_to_compare = [m for m in method_names if m in available_results]
                if not methods_to_compare:
                    raise ServiceError(
                        message="None of the specified methods have results in the project",
                        service_name="DecisionService"
                    )
            else:
                methods_to_compare = list(available_results)
            
            comparison = project.compare_methods(methods_to_compare)
        
            comparison = self._calculate_additional_metrics(comparison, project, methods_to_compare)
            
            return comparison
            
        except Exception as e:
            raise ServiceError(
                message=f"Error comparing methods: {str(e)}",
                service_name="DecisionService"
            ) from e
    
    def _calculate_additional_metrics(self, comparison: Dict[str, Any], 
                                   project: Project, methods: List[str]) -> Dict[str, Any]:
        # Calculate ranking correlation between methods
        ranking_correlation = self._calculate_ranking_correlation(project, methods)
        comparison['rankings_correlation'] = ranking_correlation
        
        # Calculate consensus between methods
        consensus_info = self._calculate_consensus(project, methods)
        comparison['consensus'] = consensus_info
        
        return comparison
    
    def _calculate_ranking_correlation(self, project: Project, 
                                    methods: List[str]) -> Dict[str, Dict[str, float]]:
        correlation = {}
        
        # For each pair of methods
        for i, method1 in enumerate(methods):
            correlation[method1] = {}
            
            for method2 in methods:
                if method1 == method2:
                    # Correlation of a method with itself is 1.0
                    correlation[method1][method2] = 1.0
                    continue
                
                # Get rankings from both methods
                result1 = project.results[method1]
                result2 = project.results[method2]
                
                # Calculate Spearman correlation
                corr = self._calculate_spearman_correlation(
                    result1.rankings, result2.rankings)
                
                correlation[method1][method2] = corr
        
        return correlation
    
    def _calculate_spearman_correlation(self, rankings1: np.ndarray, 
                                     rankings2: np.ndarray) -> float:
        n = len(rankings1)
        
        # Calculate the squared difference between rankings
        d_squared = np.sum((rankings1 - rankings2) ** 2)
        
        # Apply Spearman correlation formula
        spearman = 1 - (6 * d_squared) / (n * (n * n - 1))
        
        return spearman
    
    def _calculate_consensus(self, project: Project, methods: List[str]) -> Dict[str, Any]:
        alternatives = project.alternatives
        n_alternatives = len(alternatives)
        
        # Initialize count of times each alternative appears in the top-k
        top_counts = {alt.id: 0 for alt in alternatives}
        
        # Initialize concordance matrix (frequency with which one alternative is ranked better than another)
        concordance_matrix = np.zeros((n_alternatives, n_alternatives))
        
        for method in methods:
            result = project.results[method]
            
            # Increment count for alternatives in top-3
            sorted_alts = result.get_sorted_alternatives()
            for i in range(min(3, n_alternatives)):
                alt_id = sorted_alts[i]['id']
                top_counts[alt_id] += 1
            
            # Update concordance matrix
            for i in range(n_alternatives):
                for j in range(n_alternatives):
                    if i != j:
                        # Alternatives by ID
                        alt_i_id = alternatives[i].id
                        alt_j_id = alternatives[j].id
                        
                        rank_i = result.get_ranking_by_id(alt_i_id)
                        rank_j = result.get_ranking_by_id(alt_j_id)
                        
                        # If i is ranked better than j, increment concordance
                        if rank_i < rank_j:
                            concordance_matrix[i, j] += 1
        
        # Normalize concordance matrix
        concordance_matrix = concordance_matrix / len(methods)
        
        # Find the alternative with the highest consensus (highest frequency in top-3)
        consensus_alt_id = max(top_counts, key=top_counts.get)
        consensus_alt = next(alt for alt in alternatives if alt.id == consensus_alt_id)
        
        # Determine general consensus level (average concordance)
        consensus_level = np.mean(concordance_matrix)
        
        return {
            'top_3_counts': top_counts,
            'concordance_matrix': concordance_matrix.tolist(),
            'consensus_alternative': {
                'id': consensus_alt.id,
                'name': consensus_alt.name,
                'top_count': top_counts[consensus_alt.id]
            },
            'consensus_level': float(consensus_level)
        }
    
    def perform_sensitivity_analysis(self, project: Project, method_name: str,
                                  criteria_id: str, weight_range: Tuple[float, float],
                                  steps: int = 10) -> Dict[str, Any]:
        try:
            if project.decision_matrix is None:
                raise ServiceError(
                    message="The project has no decision matrix",
                    service_name="DecisionService"
                )
            
            try:
                criteria = project.get_criteria_by_id(criteria_id)
            except ValueError:
                raise ServiceError(
                    message=f"Criterion with ID: {criteria_id} not found",
                    service_name="DecisionService"
                )
            
            method = self._method_factory.create_method(method_name)
            
            original_weight = criteria.weight
            
            min_weight, max_weight = weight_range
            weights_to_test = np.linspace(min_weight, max_weight, steps)
            
            sensitivity_results = {
                'method': method_name,
                'criteria': {
                    'id': criteria.id,
                    'name': criteria.name,
                    'original_weight': original_weight
                },
                'weight_range': list(weight_range),
                'weights_tested': weights_to_test.tolist(),
                'rankings': [],
                'scores': []
            }
            
            for weight in weights_to_test:
                # Modify criterion weight
                criteria.weight = weight
                
                # Update decision matrix (necessary if weights are integrated)
                project.create_decision_matrix()
                
                result = method.execute(project.decision_matrix)
            
                sensitivity_results['rankings'].append(result.rankings.tolist())
                sensitivity_results['scores'].append(result.scores.tolist())
            
            # Restore original weight
            criteria.weight = original_weight
            project.create_decision_matrix()
            
            # Analyze stability of results
            sensitivity_results['stability'] = self._analyze_ranking_stability(
                np.array(sensitivity_results['rankings']))
            
            return sensitivity_results
            
        except Exception as e:
            raise ServiceError(
                message=f"Error performing sensitivity analysis: {str(e)}",
                service_name="DecisionService"
            ) from e
    
    def _analyze_ranking_stability(self, rankings: np.ndarray) -> Dict[str, Any]:
        n_alternatives = rankings.shape[1]
        
        ranking_variance = np.var(rankings, axis=0)
        
        stability_index = 1.0 / (1.0 + np.mean(ranking_variance))
        
        rank_changes = {}
        for alt_idx in range(n_alternatives):
            changes = np.diff(rankings[:, alt_idx])
            rank_changes[str(alt_idx)] = {
                'total_changes': int(np.count_nonzero(changes)),
                'max_change': int(np.max(np.abs(changes))) if len(changes) > 0 else 0
            }
        
        return {
            'ranking_variance': ranking_variance.tolist(),
            'stability_index': float(stability_index),  # 0-1, higher = more stable
            'rank_changes': rank_changes
        }
    
    def create_project(self, name: str, description: str = "", 
                    decision_maker: str = "") -> Project:
        return Project(name=name, description=description, decision_maker=decision_maker)
    
    def add_alternative(self, project: Project, id: str, name: str, 
                      description: str = "", metadata: Optional[Dict] = None) -> Alternative:
        try:
            alternative = Alternative(id=id, name=name, description=description, metadata=metadata)
            
            project.add_alternative(alternative)
            
            return alternative
            
        except ValueError as e:
            raise ServiceError(
                message=f"Error adding alternative: {str(e)}",
                service_name="DecisionService"
            ) from e
    
    def add_criteria(self, project: Project, id: str, name: str, 
                   description: str = "", optimization_type="maximize",
                   scale_type="quantitative", weight=1.0, unit="",
                   metadata: Optional[Dict] = None) -> Criteria:
        try:
            if isinstance(optimization_type, str):
                optimization_type = OptimizationType(optimization_type)
            if isinstance(scale_type, str):
                scale_type = ScaleType(scale_type)
                
            criteria = Criteria(
                id=id, 
                name=name, 
                description=description,
                optimization_type=optimization_type,
                scale_type=scale_type,
                weight=weight,
                unit=unit,
                metadata=metadata
            )
            project.add_criteria(criteria)
            
            return criteria
            
        except ValueError as e:
            raise ServiceError(
                message=f"Error adding criterion: {str(e)}",
                service_name="DecisionService"
            ) from e
        
    def create_decision_matrix(self, project: Project, name: Optional[str] = None,
                             values: Optional[List[List[float]]] = None) -> DecisionMatrix:
        try:
            return project.create_decision_matrix(name, values)    
        except ValueError as e:
            raise ServiceError(
                message=f"Error creating decision matrix: {str(e)}",
                service_name="DecisionService"
            ) from e
    
    def set_matrix_value(self, project: Project, alternative_id: str, 
                       criteria_id: str, value: float) -> None:
        try:
            # Verify that the project has a decision matrix
            if project.decision_matrix is None:
                raise ServiceError(
                    message="The project has no decision matrix",
                    service_name="DecisionService"
                )
                
            # Get indices
            alt_idx, _ = project.decision_matrix.get_alternative_by_id(alternative_id)
            crit_idx, _ = project.decision_matrix.get_criteria_by_id(criteria_id)
            
            # Set value
            project.decision_matrix.set_values(alt_idx, crit_idx, value)
            
        except ValueError as e:
            raise ServiceError(
                message=f"Error setting value in matrix: {str(e)}",
                service_name="DecisionService"
            ) from e
"""
Module that defines the ProjectValidator class to validate Project objects.

This validator ensures that projects comply with business rules.
"""
from typing import Dict, List, Optional, Tuple, Union, Any
from uuid import UUID

from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from application.validators.matrix_validator import MatrixValidator


class ProjectValidator:
    @staticmethod
    def validate_id(project_id: str) -> Tuple[bool, Optional[str]]:
        if not project_id:
            return False, "Project ID cannot be empty"
        
        if not isinstance(project_id, str):
            return False, "ID must be a string"
            
        try:
            UUID(project_id)
        except ValueError:
            return False, "Project ID must be a valid UUID"
            
        return True, None
    
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, Optional[str]]:
        if not name:
            return False, "Project name cannot be empty"
        
        if not isinstance(name, str):
            return False, "Name must be a string"
            
        return True, None
    
    @staticmethod
    def validate_description(description: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(description, str):
            return False, "Description must be a string"
            
        return True, None
    
    @staticmethod
    def validate_decision_maker(decision_maker: str) -> Tuple[bool, Optional[str]]:
        if decision_maker is None:
            return False, "Decision maker cannot be None"
        
        if not isinstance(decision_maker, str):
            return False, "Decision maker must be a string"
            
        return True, None
    
    @staticmethod
    def validate_alternatives(alternatives: List[Alternative]) -> Tuple[bool, List[str]]:
        errors = []
        
        if len(alternatives) == 0:
            errors.append("Alternatives list cannot be empty")
            return False, errors

        if not isinstance(alternatives, list):
            errors.append("Alternatives must be in a list")
            return False, errors
            
        if not all(isinstance(alt, Alternative) for alt in alternatives):
            errors.append("All elements must be instances of Alternative")
            return False, errors

        alt_ids = [alt.id for alt in alternatives]
        unique_ids = set(alt_ids)
        if len(alt_ids) != len(unique_ids):
            errors.append("There are alternatives with duplicate IDs")
            
            seen = set()
            duplicates = set()
            for alt_id in alt_ids:
                if alt_id in seen:
                    duplicates.add(alt_id)
                else:
                    seen.add(alt_id)
                    
            errors.append(f"Duplicate IDs: {', '.join(duplicates)}")
            
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_criteria(criteria: List[Criteria]) -> Tuple[bool, List[str]]:
        errors = []
        
        if len(criteria) == 0:
            errors.append("Criteria list cannot be empty")
            return False, errors

        if not isinstance(criteria, list):
            errors.append("Criteria must be in a list")
            return False, errors
            
        if not all(isinstance(crit, Criteria) for crit in criteria):
            errors.append("All elements must be instances of Criteria")
            return False, errors
            
        crit_ids = [crit.id for crit in criteria]
        unique_ids = set(crit_ids)
        if len(crit_ids) != len(unique_ids):
            errors.append("There are criteria with duplicate IDs")
            
            seen = set()
            duplicates = set()
            for crit_id in crit_ids:
                if crit_id in seen:
                    duplicates.add(crit_id)
                else:
                    seen.add(crit_id)
                    
            errors.append(f"Duplicate IDs: {', '.join(duplicates)}")
            
        
        total_weight = sum(crit.weight for crit in criteria)
        if total_weight <= 0:
            errors.append("The sum of criteria weights must be greater than zero")
            
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_decision_matrix(matrix: Optional[DecisionMatrix], 
                              alternatives: List[Alternative],
                              criteria: List[Criteria]) -> Tuple[bool, List[str]]:
        
        if matrix is None:
            return True, []
            
        errors = []
        
        if not isinstance(matrix, DecisionMatrix):
            errors.append("Decision matrix must be an instance of DecisionMatrix")
            return False, errors
        
        matrix_valid, matrix_errors = MatrixValidator.validate_consistency(matrix)
        if not matrix_valid:
            errors.extend(matrix_errors)
        
        matrix_alt_ids = {alt.id for alt in matrix.alternative}
        project_alt_ids = {alt.id for alt in alternatives}
        if not matrix_alt_ids.issubset(project_alt_ids):
            missing_alts = matrix_alt_ids - project_alt_ids
            errors.append(f"The matrix contains alternatives not defined in the project: {', '.join(missing_alts)}")
        
        matrix_crit_ids = {crit.id for crit in matrix.criteria}
        project_crit_ids = {crit.id for crit in criteria}
        if not matrix_crit_ids.issubset(project_crit_ids):
            missing_crits = matrix_crit_ids - project_crit_ids
            errors.append(f"The matrix contains criteria not defined in the project: {', '.join(missing_crits)}")
            
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_results(results: Dict[str, Result], 
                       alternatives: List[Alternative]) -> Tuple[bool, List[str]]:
        
        errors = []
        
        if not isinstance(results, dict):
            errors.append("Results must be in a dictionary")
            return False, errors
            
        for method_name, result in results.items():
            if not isinstance(method_name, str):
                errors.append(f"Method name '{method_name}' must be a string")
                
            if not isinstance(result, Result):
                errors.append(f"Result for method '{method_name}' must be an instance of Result")
                continue
            
            result_alt_ids = set(result.alternative_ids)
            project_alt_ids = {alt.id for alt in alternatives}
            if not result_alt_ids.issubset(project_alt_ids):
                missing_alts = result_alt_ids - project_alt_ids
                errors.append(f"Result for method '{method_name}' contains alternatives not defined in the project: {', '.join(missing_alts)}")
                
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_metadata(metadata: Dict) -> Tuple[bool, Optional[str]]:
        
        if metadata is None:
            return False, "Metadata cannot be None"
        
        if not isinstance(metadata, dict):
            return False, "Metadata must be a dictionary"
            
        return True, None
    
    @classmethod
    def validate_project_data(cls, project_id: str, name: str, 
                           description: str = "", decision_maker: str = "",
                           alternatives: Optional[List[Alternative]] = None,
                           criteria: Optional[List[Criteria]] = None,
                           decision_matrix: Optional[DecisionMatrix] = None,
                           results: Optional[Dict[str, Result]] = None,
                           metadata: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        
        errors = []
        
        id_valid, id_error = cls.validate_id(project_id)
        if not id_valid:
            errors.append(id_error)
        
        name_valid, name_error = cls.validate_name(name)
        if not name_valid:
            errors.append(name_error)
        
        desc_valid, desc_error = cls.validate_description(description)
        if not desc_valid:
            errors.append(desc_error)
        
        dm_valid, dm_error = cls.validate_decision_maker(decision_maker)
        if not dm_valid:
            errors.append(dm_error)
        
        alternatives = alternatives or []
        criteria = criteria or []
        
        alt_valid, alt_errors = cls.validate_alternatives(alternatives)
        if not alt_valid:
            errors.extend(alt_errors)
        
        crit_valid, crit_errors = cls.validate_criteria(criteria)
        if not crit_valid:
            errors.extend(crit_errors)
        
        if decision_matrix is not None:
            matrix_valid, matrix_errors = cls.validate_decision_matrix(
                decision_matrix, alternatives, criteria)
            if not matrix_valid:
                errors.extend(matrix_errors)
        
        results = results or {}
        results_valid, results_errors = cls.validate_results(results, alternatives)
        if not results_valid:
            errors.extend(results_errors)
        
        metadata = metadata or {}
        meta_valid, meta_error = cls.validate_metadata(metadata)
        if not meta_valid:
            errors.append(meta_error)
        
        return len(errors) == 0, errors
        
    @classmethod
    def validate_from_dict(cls, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        
        errors = []
        
        required_fields = ['id', 'name']
        for field in required_fields:
            if field not in data:
                errors.append(f"Field '{field}' is required")
        
        if errors:
            return False, errors
        
        id_valid, id_error = cls.validate_id(data['id'])
        if not id_valid:
            errors.append(id_error)
        
        name_valid, name_error = cls.validate_name(data['name'])
        if not name_valid:
            errors.append(name_error)
        
        if 'description' in data:
            desc_valid, desc_error = cls.validate_description(data['description'])
            if not desc_valid:
                errors.append(desc_error)
        
        if 'decision_maker' in data:
            dm_valid, dm_error = cls.validate_decision_maker(data['decision_maker'])
            if not dm_valid:
                errors.append(dm_error)
        
        if 'alternatives' in data and not isinstance(data['alternatives'], list):
            errors.append("Field 'alternatives' must be a list")
        
        if 'criteria' in data and not isinstance(data['criteria'], list):
            errors.append("Field 'criteria' must be a list")
        
        if 'decision_matrix' in data and not isinstance(data['decision_matrix'], dict):
            errors.append("Field 'decision_matrix' must be a dictionary")
        
        if 'results' in data and not isinstance(data['results'], dict):
            errors.append("Field 'results' must be a dictionary")
        
        if 'metadata' in data and not isinstance(data['metadata'], dict):
            errors.append("Field 'metadata' must be a dictionary")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_project(project: Any) -> Tuple[bool, List[str]]:
        errors = []
        
        alt_valid, alt_errors = ProjectValidator.validate_alternatives(project.alternatives)
        if not alt_valid:
            errors.extend(alt_errors)
        
        crit_valid, crit_errors = ProjectValidator.validate_criteria(project.criteria)
        if not crit_valid:
            errors.extend(crit_errors)
        
        if project.decision_matrix is not None:
            matrix_valid, matrix_errors = ProjectValidator.validate_decision_matrix(
                project.decision_matrix, project.alternatives, project.criteria)
            if not matrix_valid:
                errors.extend(matrix_errors)
    
        results_valid, results_errors = ProjectValidator.validate_results(
            project.results, project.alternatives)
        if not results_valid:
            errors.extend(results_errors)
        
        return len(errors) == 0, errors
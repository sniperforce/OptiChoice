"""
  Module for validate DecisionMatrix objects

"""

from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np

from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria

class MatrixValidator:
    @staticmethod
    def validate_name(name: str) -> Tuple[bool, Optional[str]]:
        if not name:
            return False, "The name of the matrix cannot be empty"
        if not isinstance(name, str):
            return False, "The name must be a text string"
        return True, None
    
    @staticmethod
    def validate_alternatives(alternatives: List[Alternative]) -> Tuple[bool, Optional[str]]:
        if not alternatives:
            return False, "The matrix must contains at least one alternative"
        if not isinstance(alternatives, list):
            return False, "The alternatives must be in a list"
        if not all(isinstance(alt, Alternative) for alt in alternatives):
            return False, "All the elements must be instance of Alternative"
        
        alt_ids = [alt.id for alt in alternatives]
        if len(alt_ids) != len(set(alt_ids)):
            return False, "Exist alternatives with duplicated ID's"
        
        return True, None
    
    @staticmethod
    def validate_criteria(criteria: List[Criteria]) -> Tuple[bool, Optional[str]]:
        if not criteria:
            return False, 'The matrix must contains at least one criteria'
        if not isinstance(criteria, list):
            return False, "The criterian must be in a list"
        if not all(isinstance(crit, Criteria) for crit in criteria):
            return False, "All the elements must be instance of Criteria"
        
        crit_ids = [crit.id for crit in criteria]
        if len(crit_ids) != len(set(crit_ids)):
            return False, "Exist criterian with duplicated ID's"
        
        return True, None
    
    @staticmethod
    def validate_values(values: np.ndarray, num_alternatives: int, num_criteria: int) -> Tuple[bool, Optional[str]]:
        if not isinstance(values, np.ndarray):
            return False, "The values must be a Numpy Matrix"
        
        if values.shape != (num_alternatives, num_criteria):
            return False, f"The dimensions of the matrix ({values.shape}) doesnt match with the number of alternatives ({num_alternatives}) and criterian ({num_criteria})"
        if not np.issubdtype(values.dtype, np.number):
            return False, "All the values of the matrix must be numerical"
        if not np.all(np.isfinite(values)):
            return False, "The matrix contains not valid values (NaN or Infinite)"
        
        return True, None
    
    @classmethod
    def validate_matrix_data(cls, name: str, alternatives: List[Alternative], 
                         criteria: List[Criteria], 
                         values: Optional[np.ndarray] = None) -> Tuple[bool, List[str]]:
        errors = []

        name_valid, name_error = cls.validate_name(name)
        if not name_valid:
            errors.append(name_error)
    
        alt_valid, alt_error = cls.validate_alternatives(alternatives)
        if not alt_valid:
            errors.append(alt_error)
        
        crit_valid, crit_error = cls.validate_criteria(criteria)
        if not crit_valid:
            errors.append(crit_error)
        
        if values is not None and alt_valid and crit_valid:
            values_valid, values_error = cls.validate_values(values, len(alternatives), len(criteria))
            if not values_valid:
                errors.append(values_error)
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_from_dict(cls, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        
        required_fields = ['name', 'alternatives', 'criteria', 'values']
        for field in required_fields:
            if field not in data:
                errors.append(f"El campo '{field}' es requerido")
        
        if errors:
            return False, errors
        
        name_valid, name_error = cls.validate_name(data['name'])
        if not name_valid:
            errors.append(name_error)
        
        if not isinstance(data['alternatives'], list):
            errors.append("The alternative field must be a list")
        elif not data['alternatives']:
            errors.append("The matrix must contain at least one alternative")
            
        if not isinstance(data['criteria'], list):
            errors.append("The field criteria must be a list")
        elif not data['criteria']:
            errors.append("The matrix must contain at least one criteria")
       
        if not isinstance(data['values'], list):
            errors.append("The value field must be a list")
        
        if errors:
            return False, errors
        
        return len(errors) == 0, errors
    
    def validate_consistency(matrix: Any) -> Tuple[bool, List[str]]:
        errors = []

        expected_shape = (len(matrix.alternative), len(matrix.criteria))
        actual_shape = matrix.shape

        if expected_shape != actual_shape:
            errors.append(f"The dimensions of the matrix ({actual_shape}) doesnt match with the number of alternatives ({expected_shape[0]}) and criterian ({expected_shape[1]})")
        
        values = matrix.values
        if not np.all(np.isfinite(values)):
            errors.append("The matrix contains unvalid values (NaN or infinite)")
        
        return len(errors) == 0, errors

    
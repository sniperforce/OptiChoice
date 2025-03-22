"""
    Module that validate Criteria objects

    This validator is in charge of verify that criterian comply with the bussines rules
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from domain.entities.criteria import OptimizationType, ScaleType

class CriteriaValidator:
    @staticmethod
    def validate_id(id: str) -> Tuple[bool, Optional[str]]:
        if not id:
            return False, "The criteria identifier cannot be empty"
        if not isinstance(id, str):
            return False, "The  identifier must be a text string"
        return True, None

    @staticmethod
    def validate_name(name: str) -> Tuple[bool, Optional[str]]:
        if not name:
            return False, "The criteria name cannot be empty"
        if not isinstance(name, str):
            return False, "The name must be a text string"
        return True, None
    
    @staticmethod
    def validate_description(description: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(description, str):
            return False, "The description must be a text string"
        
        return True, None
    
    @staticmethod
    def validate_optimization_type(opt_type: Any) -> Tuple[bool, Optional[str]]:
        if isinstance(opt_type, str):
            try:
                opt_type = OptimizationType(opt_type)
            except ValueError:
                return False, f"Invalid optimization type: {opt_type}. Must be 'maximize' or 'minimize'"
        
        if not isinstance(opt_type, OptimizationType):
            return False, "The optimization type must be a value of the enum Optimization Type"

        return True, None

    @staticmethod
    def validate_scale_type(scale_type: Any) -> Tuple[bool, Optional[str]]:
        if isinstance(scale_type, str):
            try:
                scale_type = ScaleType(scale_type)
            except ValueError:
                return False, f"Invalid scale type: {scale_type}. Must be 'quantitative', 'qualitative' or 'fuzzy'"

        if not isinstance(scale_type, ScaleType):
            return False, "The scale type must be a value of the enum ScaleType" 

        return True, None

    @staticmethod
    def validate_weight(weight: Any) -> Tuple[bool, Optional[str]]:
        try:
            weight = float(weight)
        except (ValueError, TypeError):
            return False, "The weight must be a number"

        if weight < 0:
            return False, "The weight cannot be negative"

        return True, None

    @staticmethod
    def validate_unit(unit: str) -> Tuple[bool, Optional[str]]:
        if unit is None:
            return False, "The unit cannot be None"

        if not isinstance(unit, str):
            return False, "The unit must be a text string"

        return True, None

    @staticmethod
    def validate_metadata(metadata: Dict) -> Tuple[bool, Optional[str]]:
        if not isinstance(metadata, dict):
            return False, "The metadata must be a dictionary"
        
        return True, None
    
    @classmethod
    def validate_criteria_data(cls, id: str, name: str, description: str = "",
                               optimization_type: Any = OptimizationType.MAXIMIZE,
                               scale_type: Any = ScaleType.QUANTITATIVE,
                               weight: float = 1.0, unit: str = "",
                               metadata: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        errors = []

        id_valid, id_error = cls.validate_id(id)
        if not id_valid:
            errors.append(id_error)

        name_valid, name_error = cls.validate_name(name)
        if not name_valid:
            errors.append(name_error)

        desc_valid, desc_error = cls.validate_description(description)
        if not desc_valid:
            errors.append(desc_error)
        
        opt_valid, opt_error = cls.validate_optimization_type(optimization_type)
        if not opt_valid:
            errors.append(opt_error)

        scale_valid, scale_error = cls.validate_scale_type(scale_type)
        if not scale_valid:
            errors.append(scale_error)

        weight_valid, weight_error = cls.validate_weight(weight)
        if not weight_valid:
            errors.append(weight_error)

        unit_valid, unit_error = cls.validate_unit(unit)
        if not unit_valid:
            errors.append(unit_error)

        metadata = metadata or {}
        meta_valid, meta_error = cls.validate_metadata(metadata)
        if not meta_valid:
            errors.append(meta_error)
        
        return len(errors) == 0, errors 

    @classmethod
    def validate_from_dict(cls, data: Dict) -> Tuple[bool, List[str]]:
        errors = []

        if 'id' not in data:
            errors.append("El campo 'id' es requerido")
        
        if 'name' not in data:
            errors.append("El campo 'name' es requerido")
        
        if errors:
            return False, errors
        
        return cls.validate_criteria_data(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            optimization_type=data.get('optimization_type', OptimizationType.MAXIMIZE),
            scale_type=data.get('scale_type', ScaleType.QUANTITATIVE),
            weight=data.get('weight', 1.0),
            unit=data.get('unit', ''),
            metadata=data.get('metadata', {})
        )

        
            
        
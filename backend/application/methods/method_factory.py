"""
Module that defines the MCDM method factory.

This factory implements the Factory pattern to create instances of different MCDM methods
according to the requested name or configuration.
"""
from typing import Dict, List, Any, Optional

from application.methods.method_interface import MCDMMethodInterface
from application.methods.topsis import TOPSISMethod
from application.methods.ahp import AHPMethod
from application.methods.electre import ELECTREMethod
from application.methods.promethee import PROMETHEEMethod
from utils.exceptions import ValidationError


class MCDMMethodFactory:
    _methods = {
        "TOPSIS": TOPSISMethod,
        "AHP": AHPMethod,
        "ELECTRE": ELECTREMethod,
        "PROMETHEE": PROMETHEEMethod
    }
    
    # Alternative names/aliases for methods
    _aliases = {
        "TECHNIQUE FOR ORDER OF PREFERENCE BY SIMILARITY TO IDEAL SOLUTION": "TOPSIS",
        "ANALYTIC HIERARCHY PROCESS": "AHP",
        "ELIMINATION ET CHOIX TRADUISANT LA REALITÉ": "ELECTRE",
        "ELIMINATION AND CHOICE EXPRESSING REALITY": "ELECTRE",
        "PREFERENCE RANKING ORGANIZATION METHOD FOR ENRICHMENT OF EVALUATIONS": "PROMETHEE"
    }
    
    @classmethod
    def create_method(cls, name: str) -> MCDMMethodInterface:
        # Convert to uppercase for case-insensitive comparison
        method_name = name.upper()
        
        # Look in aliases if necessary
        if method_name in cls._aliases:
            method_name = cls._aliases[method_name]
        
        # Check if the method exists
        if method_name not in cls._methods:
            available_methods = list(cls._methods.keys())
            raise ValidationError(
                message=f"MCDM method not available: {name}",
                errors=[f"Available methods: {', '.join(available_methods)}"]
            )
        
        # Create and return an instance of the method
        return cls._methods[method_name]()
    
    @classmethod
    def get_available_methods(cls) -> List[str]:
        return list(cls._methods.keys())
    
    @classmethod
    def get_method_info(cls, name: str) -> Dict[str, Any]:
        # Create an instance of the method to get its information
        method = cls.create_method(name)
        
        return {
            'name': method.name,
            'full_name': method.full_name,
            'description': method.description,
            'default_parameters': method.get_default_parameters()
        }
    
    @classmethod
    def register_method(cls, name: str, method_class: type) -> None:
        # Verify that the class implements the appropriate interface
        if not issubclass(method_class, MCDMMethodInterface):
            raise ValueError(
                f"The class {method_class.__name__} does not implement the MCDMMethodInterface"
            )
        
        # Verify that the name is not already registered
        if name in cls._methods:
            raise ValueError(f"A method with the name '{name}' is already registered")
        
        # Register the method
        cls._methods[name] = method_class
    
    @classmethod
    def create_method_with_params(cls, name: str, parameters: Optional[Dict[str, Any]] = None) -> MCDMMethodInterface:
        # Create method
        method = cls.create_method(name)
        
        # Validate parameters if provided
        if parameters is not None:
            if not method.validate_parameters(parameters):
                raise ValidationError(
                    message=f"Invalid parameters for the {name} method",
                    errors=["Refer to the method documentation for valid parameters."]
                )
        
        return method
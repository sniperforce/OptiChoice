"""
    Module that defines the base interface for all the MCDM methods
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result

class MCDMMethodInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def full_name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def execute(self, decision_matrix: DecisionMatrix,
                parameters: Optional[Dict[str, Any]] = None) -> Result:
        pass

    def _prepare_execution(self, decision_matrix: DecisionMatrix,
                           parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        effective_params = self.get_default_parameters()
        if parameters:
            effective_params.update(parameters)
        
        if not self.validate_parameters(effective_params):
            raise ValueError(f"Invalid Parameters for the method {self.name}")
        
        return effective_params
    
    def run_with_timing(self, decision_matrix: DecisionMatrix, 
                      parameters: Optional[Dict[str, Any]] = None) -> Result:
        start_time = time.time()
       
        result = self.execute(decision_matrix, parameters)
    
        execution_time = time.time() - start_time
        
        result.set_metadata('execution_time', execution_time)
        
        return result
    
    def __str__(self) -> str:
        return f"{self.name} - {self.full_name}"
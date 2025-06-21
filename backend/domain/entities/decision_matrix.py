""" Module that  define the DecisionMatrix class for represents the decision matrix in MCDM problems

    The decision matrix contains the values of evaluation for each alternative respect to each criterian
"""

from typing import Dict, List, Optional, Union, Tuple, Any
import numpy as np
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria
from utils.normalization import normalize_matrix

class DecisionMatrix:
    def __init__(self, alternatives: List[Alternative], criteria: List[Criteria],
                 values: Optional[Union[np.ndarray, List[List[float]]]] = None, 
                 name: Optional[str] = None):
        # CORRECCIÓN: Hacer el nombre opcional con valor por defecto
        self._name = name if name is not None else "Decision Matrix"
        self._alternatives = alternatives
        self._criteria = criteria

        if values is None:
            self._values = np.zeros((len(alternatives), len(criteria)))
        elif isinstance(values, np.ndarray):
            self._values = values.copy()
        else:
            self._values = np.array(values, dtype=float)
        
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def alternative(self) -> List[Alternative]:
        return list(self._alternatives)
    
    @property
    def criteria(self) -> List[Criteria]:
        return list(self._criteria)
    
    @property
    def values(self) -> np.ndarray:
        return self._values.copy()
    
    @property
    def shape(self) -> Tuple[int,int]:
        return self._values.shape
    
    def get_values(self, alternative_idx: int, criteria_idx: int) -> float:
        return self._values[alternative_idx, criteria_idx]
    
    def set_values(self, alternative_idx: int, criteria_idx: int, value: float) -> None:
        self._values[alternative_idx, criteria_idx] = value
    
    def get_alternative_values(self, alternative_idx: int) -> np.ndarray:
        return self._values[alternative_idx, :].copy()
    
    def get_criteria_values(self, criteria_idx: int) -> np.ndarray:
        return self._values[:, criteria_idx].copy()
    
    def get_alternative_by_id(self, alternative_id: str) -> Tuple[int, Alternative]:
        for idx, alt in enumerate(self._alternatives):
            if alt.id == alternative_id:
                return idx, alt
        raise ValueError(f"Dont find any alternative with ID: {alternative_id}")
    
    def get_criteria_by_id(self, criteria_id: str) -> Tuple[int, Criteria]:  # Cambiar int a str
        for idx, ct in enumerate(self._criteria):
            if str(ct.id) == str(criteria_id):  # Convertir ambos a string para comparación
                return idx, ct
        raise ValueError(f"Don't find any criteria with ID: {criteria_id}")
    
    def add_alternative(self, alternative: Alternative, values: Optional[List[float]] = None) -> None:
        if values is not None and len(values) != len(self._criteria):
            raise ValueError(f"The lenght of the values ({len(values)}) doesn't match with the number of criterian ({len(self._criteria)})")

        self._alternatives.append(alternative)

        # Prepare the new row for the matrix and add it
        if values is None:
            new_row = np.zeros(len(self._criteria))
        else:
            new_row = np.array(values, dtype=float)
        
        self._values = np.vstack((self._values, new_row))
    
    def add_criteria(self, criteria: Criteria, values: Optional[List[float]] = None) -> None:
        if values is not None and len(values) != len(self._alternatives):
            raise ValueError(f"The lenght of the values ({len(values)}) doesn't match with the number of alternatives ({len(self._alternatives)})")
        
        self._criteria.append(criteria)

        #Prepare and add the new column to the matrix
        new_col = np.zeros(len(self._alternatives)) if values is None else np.array(values, dtype=float)
        self._values = np.column_stack((self._values, new_col))
    
    def remove_alternative(self, alternative_idx: int) -> None:
        self._alternatives.pop(alternative_idx)
        self._values = np.delete(self._values, alternative_idx, axis=0)
    
    def remove_criteria(self, criteria_idx: int) -> None:
        self._criteria.pop(criteria_idx)
        self._values = np.delete(self._values, criteria_idx, axis=1)
    
    def normalize(self, method: str = 'minimax') -> 'DecisionMatrix':
        normalized_values = normalize_matrix(
            values=self._values,
            criteria=self._criteria,
            method=method
        )

        return DecisionMatrix(
            name=f"{self.name} (Normalizada - {method})",
            alternatives=self._alternatives,
            criteria=self._criteria,
            values=normalized_values
        )

    def weighted_matrix(self) -> 'DecisionMatrix':
        weights = np.array([criteria.weight  for criteria in self._criteria])

        # Normalize the weights so that they sum 1
        sum_weights = np.sum(weights)
        if sum_weights > 0:
            weights = weights / sum_weights
        
        # Apply the weights to each column
        weighted_values = self._values.copy()
        for j in range(weighted_values.shape[1]):
            weighted_values[:, j] = weighted_values[:, j] * weights[j]

        # Create and return a new weighted decision matrix
        return DecisionMatrix(
            name=f"{self.name} (Weighted)",
            alternatives=self._alternatives,
            criteria=self._criteria,
            values=weighted_values
        )
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'alternatives': [alt.to_dict() for alt in self._alternatives],
            'criteria': [crit.to_dict() for crit in self._criteria],
            'values': self._values.tolist()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DecisionMatrix':
        alternatives = [Alternative.from_dict(alt_data) for alt_data in data['alternatives']]
        criteria = [Criteria.from_dict(crit_data) for crit_data in data['criteria']]
        
        return cls(
            name=data['name'],
            alternatives=alternatives,
            criteria=criteria,
            values=data['values']
        )
"""
    Module that gives functions for normalize decisions matrix in MCDM problems

    This module contains different algorithms of normalization that can be apply
    to the values of a decision matrix, taking into account the type of criteria
    (benefit or cost)
"""

from typing import List, Optional, Union
import numpy as np
from domain.entities.criteria import Criteria

def normalize_matrix(matrix: np.ndarray, method: str = 'vector', 
                    criteria_types: Optional[List] = None) -> np.ndarray:
    """
    Normalize a decision matrix using different methods
    """
    # Validar entrada
    if matrix.size == 0:
        raise ValueError("Cannot normalize empty matrix")
    
    if np.any(np.isnan(matrix)):
        raise ValueError("Matrix contains NaN values")
    
    if np.any(np.isinf(matrix)):
        raise ValueError("Matrix contains infinite values")
    
    normalized = matrix.copy().astype(float)
    
    if method == 'vector':
        # Vector normalization
        for j in range(matrix.shape[1]):
            column_sum_sq = np.sum(matrix[:, j] ** 2)
            if column_sum_sq > 0:
                normalized[:, j] = matrix[:, j] / np.sqrt(column_sum_sq)
            else:
                # Si toda la columna es cero, mantenerla como cero
                normalized[:, j] = 0.0
                
    elif method == 'minmax':
        # Min-Max normalization
        for j in range(matrix.shape[1]):
            min_val = np.min(matrix[:, j])
            max_val = np.max(matrix[:, j])
            
            if max_val > min_val:
                if criteria_types and criteria_types[j] == 'minimize':
                    # Para criterios de minimización
                    normalized[:, j] = (max_val - matrix[:, j]) / (max_val - min_val)
                else:
                    # Para criterios de maximización
                    normalized[:, j] = (matrix[:, j] - min_val) / (max_val - min_val)
            else:
                # Si todos los valores son iguales
                normalized[:, j] = 1.0
                
    elif method == 'linear':
        # Linear normalization
        for j in range(matrix.shape[1]):
            max_val = np.max(matrix[:, j])
            if max_val > 0:
                normalized[:, j] = matrix[:, j] / max_val
            else:
                normalized[:, j] = 0.0
    
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized

def normalize_minmax(values: np.ndarray, criteria: List[Criteria]) -> np.ndarray:
    """
        Apply the Min-Max normalization to the value matrix

        Formula: (x - min) / (max - min) for benefits criterian,
                 (max - x) / (max - min) for cost criterian
    """

    normalized = values.copy()

    for j in range(normalized.shape[1]):
        col_min = np.min(normalized[:, j])
        col_max = np.max(normalized[:, j])

        #Avoid division by zero
        if col_max - col_min != 0:
            if criteria[j].is_benefit_criteria():
                # For benefit criterian (maximize)
                normalized[:, j] = (normalized[:, j] - col_min) / (col_max - col_min)
            else:
                #  For cost criterian (minimise)
                normalized[:, j] = (col_max - normalized[:, j]) / (col_max - col_min)
        else:
            # If every value are equal, normalize to 1 for benefit, 0 for cost
            normalized[:, j] = 1.0 if criteria[j].is_benefit_criteria() else 0.0
    
    return normalized

def normalize_sum(values: np.ndarray, criteria: List[Criteria]) -> np.ndarray:
    """
    Apply sum normalization to the values matrix
    
    Formula: x / sum(x) for benefit criteria,
             (1/x) / sum(1/x) for cost criteria.
    
    """
    normalized = values.copy()
    
    for j in range(normalized.shape[1]):
        if criteria[j].is_benefit_criteria():
            # For benefit criteria (maximize)
            col_sum = np.sum(normalized[:, j])
            if col_sum != 0:
                normalized[:, j] = normalized[:, j] / col_sum
            else:
                normalized[:, j] = np.ones_like(normalized[:, j]) / normalized.shape[0]
        else:
            # For cost criteria (minimise)
            # First invert the values (1/x) for not zero values
            inverted = np.zeros_like(normalized[:, j])
            non_zero_mask = normalized[:, j] != 0
            inverted[non_zero_mask] = 1 / normalized[non_zero_mask, j]
            
            # Then normalize by sum
            col_sum = np.sum(inverted)
            if col_sum != 0:
                normalized[:, j] = inverted / col_sum
            else:
                normalized[:, j] = np.zeros_like(normalized[:, j])
    
    return normalized

def normalize_max(values: np.ndarray, criteria: List[Criteria]) -> np.ndarray:
    """
    Apply normalization by max to the values matrix
    
    Formula: x / max(x) for benefit criterian,
             min(x) / x for cost criterian.
    
    """
    normalized = values.copy()
    
    for j in range(normalized.shape[1]):
        if criteria[j].is_benefit_criteria():
            # For benefit criterian (maximize)
            col_max = np.max(normalized[:, j])
            if col_max != 0:
                normalized[:, j] = normalized[:, j] / col_max
            else:
                normalized[:, j] = np.zeros_like(normalized[:, j])
        else:
            # For cost criterian (minimise)
            non_zero_mask = normalized[:, j] != 0
            if np.any(non_zero_mask):
                col_min = np.min(normalized[non_zero_mask, j])
                normalized_col = np.zeros_like(normalized[:, j])
                normalized_col[non_zero_mask] = col_min / normalized[non_zero_mask, j]
                normalized[:, j] = normalized_col
            else:
                normalized[:, j] = np.zeros_like(normalized[:, j])
    
    return normalized


def normalize_vector(values: np.ndarray, criteria: List[Criteria]) -> np.ndarray:
    """
    Apply vectorial normalization (euclidean norm) to the values matrix
    
    Fórmula: x / sqrt(sum(x^2)) for benefit criterian,
             -x / sqrt(sum(x^2)) for cost criterian.
    
    """
    normalized = values.copy()
    
    for j in range(normalized.shape[1]):
        col_norm = np.sqrt(np.sum(normalized[:, j] ** 2))
        
        if col_norm != 0:
            normalized[:, j] = normalized[:, j] / col_norm
            
            # For cost criterian, inver the sign
            if criteria[j].is_cost_criteria():
                normalized[:, j] = -normalized[:, j]
        else:
            normalized[:, j] = np.zeros_like(normalized[:, j])
    
    return normalized

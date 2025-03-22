"""
    Module for representsthe results of a MCDM method

    The results include scores, rankings y additional metadata from analisis
"""

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime

class Result:  
    def __init__(self, method_name: str, alternative_ids: List[str],
                 alternative_names: List[str], scores: np.ndarray,
                 execution_time: float = 0.0, parameters: Optional[Dict] = None,
                 metadata: Optional[Dict] = None):
        
        self._method_name = method_name
        self._alternative_ids = list(alternative_ids)
        self._alternative_names = list(alternative_names)
        self._scores = np.array(scores, dtype=float)
        self._execution_time = execution_time
        self._parameters = parameters or {}
        self._created_at = datetime.now()
        self._metadata = metadata or {} 

        # Calculate the rankings from the scores
        self._rankings = self._calculate_rankings()

    def _calculate_rankings(self) -> np.ndarray:
        # get the descending order (argsort returns the ascending order, that's why we invest with [::-1])
        sorted_indices = np.argsort(self._scores)[::-1]

        rankings = np.zeros_like(self._scores, dtype=int)

        current_rank = 1
        previous_score = None

        for i, idx in enumerate(sorted_indices):
            current_score = self._scores[idx]

            # If it is the first element or if the score is different from the previous one
            if previous_score is None or current_score != previous_score:
                current_rank = i + 1    # Asign new ranking (actual position + 1)
            
            # Asign ranking to the alternative
            rankings[idx] = current_rank

            # Update previous score
            previous_score = current_score
        
        return rankings
    
    @property
    def method_name(self) -> str:
        return self._method_name
    
    @property
    def alternative_ids(self) -> List[str]:
        return list(self._alternative_ids)
    
    @property
    def alternative_names(self) -> List[str]:
        return list(self._alternative_names)
    
    @property
    def scores(self) -> np.ndarray:
        return self._scores.copy()
    
    @property
    def rankings(self) -> np.ndarray:
        return self._rankings.copy()
    
    @property
    def execution_time(self) -> float:
        return self._execution_time
    
    @property
    def parameters(self) -> Dict:
        return self._parameters.copy()
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def metadata(self) -> Dict:
        return self._metadata.copy()
    
    def get_alternative_info(self, alternative_id: str) -> Tuple[str, float, int]:
        """
            Returns:
                Tuple[str, float, int]: Tuple with (name, score, ranking)
        """
        
        try:
            idx = self._alternative_ids.index(alternative_id)
            return (
                self._alternative_names[idx],
                self._scores[idx],
                self._rankings[idx]
            )
        except ValueError:
            raise ValueError(f"No alternative was found with ID: {alternative_id}")
        
    def get_ranking_by_id(self, alternative_id: str) -> int:
        try:
            idx = self._alternative_ids.index(alternative_id)
            return int(self._rankings[idx])
        except ValueError:
            raise ValueError(f"No alternative was found with ID: {alternative_id}")

    def get_score_by_id(self, alternative_id: str) -> float:
        try:
            idx = self._alternative_ids.index(alternative_id)
            return float(self._scores[idx])
        except ValueError:
            raise ValueError(f"No alternative was found with ID: {alternative_id}")
        
    def get_best_alternative(self) -> Tuple[str, str, float]:
        """
            Returns:
                Tuple[str, str, float]: Tuple with (id, name, score) of the best alternative
        """
        best_idx = np.argmax(self._scores)
        return (
            self._alternative_ids[best_idx],
            self._alternative_names[best_idx],
            float(self._scores[best_idx])
        )
    
    def get_worst_alternative(self) -> Tuple[str, str, float]:
        """
            Returns:
                Tuple[str, str, float]: Tuple with (id, name, score) of the worst alternative
        """
        worst_idx = np.argmin(self._scores)
        return (
            self._alternative_ids[worst_idx],
            self._alternative_names[worst_idx],
            float(self._scores[worst_idx])
        )
    
    def get_sorted_alternatives(self) -> List[Dict[str, Any]]:
        """
            Returns:
                List[Dict[str, Any]]: Dictionaries List with information of each alternative
        """
        sorted_indices = np.argsort(self._scores)[::-1]

        sorted_alternatives = []
        for idx in sorted_indices:
            sorted_alternatives.append({
                'id': self._alternative_ids[idx],
                'name': self._alternative_names[idx],
                'score': float(self._scores[idx]),
                'ranking': int(self._rankings[idx])
            })
        
        return sorted_alternatives
    
    def compare_alternatives(self, id_a: str, id_b: str) -> Dict[str, Any]:
        """
            Compare 2 alternatives by their ID

            Returns:
                Dict[str, Any]: Dictionary with comparative information
        """
        try:
            idx_a = self._alternative_ids[id_a]
            idx_b = self._alternative_ids[id_b]
        except ValueError as e:
            raise ValueError(f"ID of alternative not found: {e}")
        
        name_a = self._alternative_names[idx_a]
        name_b = self._alternative_names[idx_b]
        score_a = float(self._scores[idx_a])
        score_b = float(self._scores[idx_b])
        rank_a = int(self._rankings[idx_a])
        rank_b = int(self._rankings[idx_b])

        # Create comparison dictionary
        comparison = {
            'alternative_a': {
                'id': id_a,
                'name': name_a,
                'score': score_a,
                'ranking': rank_a
            },
            'alternative_b': {
                'id': id_b,
                'name': name_b,
                'score': score_b,
                'ranking': rank_b
            },
            'difference': {
                'score': score_a - score_b,
                'ranking': rank_b - rank_a  # Inverted because less ranking better
            },
            'better_alternative': id_a if score_a > score_b else id_b
        }

        return comparison
    
    def set_metadata(self, key: str, value: Any) -> None:
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'method_name': self._method_name,
            'alternative_ids': self._alternative_ids,
            'alternative_names': self._alternative_names,
            'scores': self._scores.tolist(),
            'rankings': self._rankings.tolist(),
            'execution_time': self._execution_time,
            'parameters': self._parameters,
            'created_at': self._created_at.isoformat(),
            'metadata': self._metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Result':
        result = cls(
            method_name=data['method_name'],
            alternative_ids=data['alternative_ids'],
            alternative_names=data['alternative_names'],
            scores=np.array(data['scores']),
            execution_time=data.get('execution_time', 0.0),
            parameters=data.get('parameters', {}),
            metadata=data.get('metadata', {})
        )
        # Restaurate the creation date if is available
        if 'created_at' in data:
            try:
                result._created_at = datetime.fromisoformat(data['created_at'])
            except (ValueError, TypeError):
                # If there is an error parsing the date, leave the current date
                pass

        return result

    def __str__(self) -> str:
        best_id, best_name, best_score = self.get_best_alternative()
        return (f"Resultado de {self._method_name}: "
                f"{len(self._alternative_ids)} alternativas evaluadas, "
                f"mejor alternativa: {best_name} (score: {best_score:.4f})")




"""
    Moduel that represents an MCDM complete project

    An MCDM project encompasses all the information and results for a decision problem
"""

from typing import Dict, List, Optional, Any, Set, Tuple, Union
from datetime import datetime
import numpy as np
import uuid
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result

class Project:
    def __init__(self, name: str, description: str='', decision_maker: str="",
                 project_id: Optional[str] = None, metadata: Optional[Dict] = None):
        self._id = project_id if project_id else str(uuid.uuid4())
        self._name = name
        self._description = description
        self._decision_maker = decision_maker
        self._created_at = datetime.now()
        self._updated_at = self._created_at
        self._alternatives: List[Alternative] = []
        self._criteria: List[Criteria] = []
        self._decision_matrix: Optional[DecisionMatrix] = None
        self._results: Dict[str, Result] = {}
        self._metadata = metadata or {}
    
    @property
    def id(self) -> str:
        return self._id
    
    @id.setter
    def id(self, value: str) -> None:
        self._id = value
        self._updated_at = datetime.now()
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._updated_at = datetime.now()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value:str) -> None:
        self._description = value
        self._updated_at = datetime.now()

    @property
    def decision_maker(self) -> str:
        return self._decision_maker
    
    @decision_maker.setter
    def decision_maker(self, value: str) -> None:
        self._decision_maker = value
        self._updated_at = datetime.now()
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def alternatives(self) -> List[Alternative]:
        return list(self._alternatives)
    
    @property
    def criteria(self) -> List[Criteria]:
        return list(self._criteria)
    
    @property
    def decision_matrix(self) -> Optional[DecisionMatrix]:
        return self._decision_matrix
    
    @property
    def results(self) -> Dict[str, Result]:
        return self._results.copy()
    
    @property
    def metadata(self) -> Dict:
        return self._metadata.copy()
    
    def set_metadata(self, key: str, value: Any) -> None:
        self._metadata[key] = value
        self._updated_at = datetime.now()
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        return self._metadata.get(key, default)

    def add_alternative(self, alternative: Alternative) -> None:
        # Verifica si ya existe una alternativa con el mismo ID
        if any(alt.id == alternative.id for alt in self._alternatives):
            raise ValueError(f"Already exists an alternative with ID: {alternative.id}")
        
        self._alternatives.append(alternative)
        self._updated_at = datetime.now()

        # Actualización segura de la matriz de decisión
        if self._decision_matrix is not None:
            try:
                self._decision_matrix.add_alternative(alternative)
            except Exception as e:
                # Si falla la actualización de la matriz, revertimos la operación
                self._alternatives.pop()
                raise ValueError(f"Error updating decision matrix: {str(e)}")
        
    def add_criteria(self, criteria: Criteria) -> None:
        # Verify if already existe a criteria with the same ID
        if any(crit.id == criteria.id for crit in self._criteria):
            raise ValueError(f"Already exist a criteria with ID: {criteria.id}")
        
        self._criteria.append(criteria)
        self._updated_at = datetime.now()

        if self._decision_matrix is not None:
            self._decision_matrix.add_criteria(criteria)
    
    def remove_alternative(self, alternative_id: str) -> None:
        for i, alt in enumerate(self._alternatives):
            if alt.id == alternative_id:
                self._alternatives.pop(i)
                self._updated_at = datetime.now()

                if self._decision_matrix is not None:
                    alt_idx, _ = self._decision_matrix.get_alternative_by_id(alternative_id)
                    self._decision_matrix.remove_alternative(alt_idx)
                
                return
        
        raise ValueError(f"No alternative were found with the ID: {alternative_id}")
    
    def remove_criteria(self, criteria_id: str) -> None:
        for i, crit in enumerate(self._criteria):
            if crit.id == criteria_id:
                self._criteria.pop(i)
                self._updated_at = datetime.now()
                
                if self._decision_matrix is not None:
                    crit_idx, _ = self._decision_matrix.get_criteria_by_id(criteria_id)
                    self._decision_matrix.remove_criteria(crit_idx)
                
                return
        
        raise ValueError(f"No criteria were found with the ID: {criteria_id}")
    
    def get_alternative_by_id(self, alternative_id: str) -> Alternative:
        for alt in self._alternatives:
            if alt.id == alternative_id:
                return alt
            
        raise ValueError(f"No alternative were found with the ID: {alternative_id}")

    def get_criteria_by_id(self, criteria_id: str) -> Criteria:
        for crit in self._criteria:
            if crit.id == criteria_id:
                return crit
        
        raise ValueError(f"No criteria were found with the ID: {criteria_id}")
    
    def create_decision_matrix(self) -> None:
        """Crear matriz de decisión con alternativas y criterios actuales"""
        
        if not self.alternatives or not self.criteria:
            raise ValueError("Cannot create matrix without alternatives and criteria")
        
        # CORRECCIÓN: Incluir nombre en la creación de la matriz
        self._decision_matrix = DecisionMatrix(
            name=f"{self.name} - Decision Matrix", 
            alternatives=list(self.alternatives),
            criteria=list(self.criteria)
        )
        
        # Marcar proyecto como actualizado
        self._updated_at = datetime.now()

    def set_decision_matrix(self, matrix: DecisionMatrix) -> None:
        matrix_alt_ids = {alt.id for alt in matrix.alternative}
        project_alt_ids = {alt.id for alt in self._alternatives}

        matrix_crit_ids = {crit.id for crit in matrix.criteria}
        project_crit_ids = {crit.id for crit in self._criteria}

        if not matrix_alt_ids.issubset(project_alt_ids):
            raise ValueError("The matrix contains alternatives that are not defined in the project")
        if not matrix_crit_ids.issubset(project_crit_ids):
            raise ValueError("The matrix contains criterian that are not defined in the project")

        self._decision_matrix = matrix
        self._updated_at = datetime.now()
    
    def add_result(self, method_name: str, result: 'Result') -> None:
        """Agregar resultado de un método"""
        self._results[method_name] = result
        self._updated_at = datetime.now()
    
    def get_result(self, method_name: str) -> Optional[Result]:
        return self._results.get(method_name)
    
    def remove_result(self, method_name: str) -> None:
        if method_name in self._results:
            del self._results[method_name]
            self._updated_at = datetime.now()
        else:
            raise KeyError(f"There is no result for the method: {method_name}")
    
    def get_available_methods(self) -> Set[str]:
        return set(self._results.keys())
    
    def get_best_alternative(self, method_name: str) -> Tuple[str, str, float]:
        if method_name not in self._results:
            raise KeyError(f"There is no result for the method: {method_name}")
        return self._results[method_name].get_best_alternative()
    
    def compare_methods(self, method_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Comparar resultados entre métodos"""
        if not self._results:
            return {}
        
        methods_to_compare = method_names or list(self._results.keys())
        
        # Preparar datos para comparación
        comparison = {
            'methods': methods_to_compare,
            'correlation_matrix': {},
            'ranking_comparison': {},
            'consensus_measures': {}
        }
        
        # Comparar rankings
        rankings = {}
        for method in methods_to_compare:
            if method in self._results:
                result = self._results[method]
                rankings[method] = result.rankings
        
        # Calcular correlaciones
        if len(rankings) >= 2:
            import numpy as np
            from scipy.stats import spearmanr, kendalltau
            
            method_list = list(rankings.keys())
            n_methods = len(method_list)
            
            # Matriz de correlación
            corr_matrix = np.zeros((n_methods, n_methods))
            
            for i in range(n_methods):
                for j in range(n_methods):
                    rank1 = rankings[method_list[i]]
                    rank2 = rankings[method_list[j]]
                    corr, _ = spearmanr(rank1, rank2)
                    corr_matrix[i, j] = corr
            
            comparison['correlation_matrix'] = corr_matrix.tolist()
            
        return comparison
    
    def to_dict(self) -> Dict[str, Any]:
        
        project_dict = {
            'id': self._id,
            'name': self._name,
            'description': self._description,
            'decision_maker': self._decision_maker,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'alternatives': [alt.to_dict() for alt in self._alternatives],
            'criteria': [crit.to_dict() for crit in self._criteria],
            'metadata': self._metadata,
            'results': {name: result.to_dict() for name, result in self._results.items()}
        }

        if self._decision_matrix is not None:
            project_dict['decision_matrix'] = self._decision_matrix.to_dict()
        
        return project_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        project = cls(
            name=data['name'],
            description=data.get('description', ''),
            decision_maker=data.get('decision_maker', ''),
            project_id=data.get('id'),
            metadata=data.get('metadata', {})
        )

        try:
            project._created_at = datetime.fromisoformat(data['created_at'])
            project._updated_at = datetime.fromisoformat(data['updated_at'])
        except (ValueError, TypeError, KeyError):
            pass

        for alt_data in data.get('alternatives', []):
            project._alternatives.append(Alternative.from_dict(alt_data))
        
        for crit_data in data.get('criteria', []):
            project._criteria.append(Criteria.from_dict(crit_data))
        
        if 'decision_matrix' in data:
            project._decision_matrix = DecisionMatrix.from_dict(data['decision_matrix'])
        
        for method_name, result_data in data.get('results', {}).items():
            project._results[method_name] = Result.from_dict(result_data)
        
        return project
    
    def __str__(self):
        return (f"MCDM Porject: {self._name}\n"
                f"- {len(self._alternatives)} alternatives\n"
                f"- {len(self._criteria)} criterian\n"
                f"- {len(self._results)} methods applied")
    

    



        



    

        
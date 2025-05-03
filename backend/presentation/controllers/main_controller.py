"""
Module that defines the main controller of the MCDM system.

This controller integrates the different services and provides a unified interface
for project management and execution of MCDM methods.
"""
from typing import Dict, List, Any, Optional, Tuple, Union
import os
from datetime import datetime

from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria
from domain.entities.result import Result
from domain.repositories.project_repository import ProjectRepository
from application.services.project_service import ProjectService
from application.services.decision_service import DecisionService
from utils.exceptions import ServiceError

class MainController:
    def __init__(self, project_repository: ProjectRepository):
        self._project_service = ProjectService(project_repository)
        self._decision_service = DecisionService()
        self._current_project = None
    
    @property
    def current_project(self) -> Optional[Project]:
        return self._current_project
    
    def new_project(self, name: str, description: str = "",
                    decision_maker: str = "") -> Project:
        project = self._decision_service.create_project(
            name=name, 
            description=description, 
            decision_maker=decision_maker
        )
        self._current_project = project
        return project
    
    def save_project(self) -> Project:
        if self._current_project is None:
            raise ValueError("There is no current project to save")
        
        saved_project = self._project_service.save_project(self._current_project)
        self._current_project = saved_project
        return saved_project
    
    def load_project(self, project_id: str) -> Project:
        project = self._project_service.get_project(project_id)
        self._current_project = project
        return project
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        projects = self._project_service.get_all_projects()
        return [
            {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'decision_maker': project.decision_maker,
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat(),
                'n_alternatives': len(project.alternatives),
                'n_criteria': len(project.criteria),
                'n_results': len(project.results)
            }
            for project in projects
        ]
    
    def delete_project(self, project_id: str) -> bool:
        if self._current_project and self._current_project.id == project_id:
            self._current_project = None
        
        return self._project_service.delete_project(project_id)
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        projects = self._project_service.search_projects(query)
        return [
            {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'decision_maker': project.decision_maker,
                'created_at': project.created_at.isoformat(),
                'updated_at': project.updated_at.isoformat(),
                'n_alternatives': len(project.alternatives),
                'n_criteria': len(project.criteria),
                'n_results': len(project.results)
            }
            for project in projects
        ]
    
    def export_project(self, file_path: str, format_type: str = 'json') -> None:
        if self._current_project is None:
            raise ValueError("There is no current project to export")
        
        format_type = format_type.lower()
        if format_type == 'json':
            self._project_service.export_to_json(self._current_project, file_path)
        elif format_type == 'excel':
            self._project_service.export_to_excel(self._current_project, file_path)
        elif format_type == 'csv':
            self._project_service.export_to_csv(self._current_project, file_path)
        elif format_type == 'pdf':
            self._project_service.export_to_pdf(self._current_project, file_path)
        else:
            raise ValueError(f"Export format not supported: {format_type}")       

    def import_project(self, file_path: str, format_type: Optional[str] = None) -> Project:
        if format_type is None:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.json':
                format_type = 'json'
            elif ext == '.csv':
                format_type = 'csv'
            elif ext in ['.xlsx', '.xls']:
                format_type = 'excel'
            else:
                raise ValueError(f"Cannot infer the format from the extension: {ext}")
        else:
            format_type = format_type.lower()
        
        if format_type == 'json':
            project = self._project_service.import_from_json(file_path)
        elif format_type == 'excel':
            project = self._project_service.import_from_excel(file_path)
        elif format_type == 'csv':
            project = self._project_service.import_from_csv(file_path)
        else:
            raise ValueError(f"Importation format not supported: {format_type}")
        
        self._current_project = project
        return project
    
    def duplicate_project(self, project_id: str, new_name: Optional[str] = None) -> Project:
        project = self._project_service.duplicate_project(project_id, new_name)
        self._current_project = project
        return project
    
    def add_alternative(self, id: str, name: str, description: str= "",
                        metadata: Optional[Dict] = None) -> Alternative:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        return self._decision_service.add_alternative(
            project=self._current_project,
            id=id,
            name=name,
            description=description,
            metadata=metadata
        )
    
    def get_alternative(self, alternative_id: str) -> Dict[str, Any]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        try:
            alternative = self._current_project.get_alternative_by_id(alternative_id)

            return {
                'id': alternative.id,
                'name': alternative.name,
                'description': alternative.description,
                'metadata': alternative.metadata
            }
        
        except ValueError as e:
            raise ValueError(f"Alternative not found: {str(e)}")
    
    def get_all_alternatives(self) -> List[Dict[str, Any]]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        alternatives = self._current_project.alternatives
        
        return [
            {
                'id': alt.id,
                'name': alt.name,
                'description': alt.description,
                'metadata': alt.metadata
            }
            for alt in alternatives
        ]
    
    def remove_alternative(self, alternative_id: str) -> None:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        try:
            self._current_project.remove_alternative(alternative_id)
        except ValueError as e:
            raise ValueError(f"Error removing alternative: {str(e)}")
        
    def add_criteria(self, id: str, name: str, description: str = "",
                   optimization_type: str = "maximize",
                   scale_type: str = "quantitative",
                   weight: float = 1.0, unit: str = "",
                   metadata: Optional[Dict] = None) -> Criteria:
        
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        return self._decision_service.add_criteria(
            project=self._current_project,
            id=id,
            name=name,
            description=description,
            optimization_type=optimization_type,
            scale_type=scale_type,
            weight=weight,
            unit=unit,
            metadata=metadata
        )
    
    def get_criteria(self, criteria_id: str) -> Dict[str, Any]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        try:
            criteria = self._current_project.get_criteria_by_id(criteria_id)
            
            return {
                'id': criteria.id,
                'name': criteria.name,
                'description': criteria.description,
                'optimization_type': criteria.optimization_type.value,
                'scale_type': criteria.scale_type.value,
                'weight': criteria.weight,
                'unit': criteria.unit,
                'metadata': criteria.metadata
            }
            
        except ValueError as e:
            raise ValueError(f"Criterion not found: {str(e)}")
    
    def get_all_criteria(self) -> List[Dict[str, Any]]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        criteria_list = self._current_project.criteria
        
        return [
            {
                'id': crit.id,
                'name': crit.name,
                'description': crit.description,
                'optimization_type': crit.optimization_type.value,
                'scale_type': crit.scale_type.value,
                'weight': crit.weight,
                'unit': crit.unit,
                'metadata': crit.metadata
            }
            for crit in criteria_list
        ]
    
    def remove_criteria(self, criteria_id: str) -> None:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        try:
            self._current_project.remove_criteria(criteria_id)
        except ValueError as e:
            raise ValueError(f"Error removing criterion: {str(e)}")
    
    def create_decision_matrix(self, name: Optional[str] = None,
                             values: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        matrix = self._decision_service.create_decision_matrix(
            project=self._current_project,
            name=name,
            values=values
        )
        
        return {
            'name': matrix.name,
            'shape': matrix.shape,
            'alternatives': [alt.name for alt in matrix.alternative],
            'criteria': [crit.name for crit in matrix.criteria],
            'has_values': matrix.values.size > 0
        }
    
    def set_matrix_value(self, alternative_id: str, criteria_id: str, value: float) -> None:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        self._decision_service.set_matrix_value(
            project=self._current_project,
            alternative_id=alternative_id,
            criteria_id=criteria_id,
            value=value
        )
    
    def get_decision_matrix(self) -> Dict[str, Any]:
        if self._current_project is None:
            raise ValueError("There is no current project")
    
        if self._current_project.decision_matrix is None:
            raise ValueError("The project has no decision matrix")
        
        matrix = self._current_project.decision_matrix
    
        result = {
            'name': matrix.name,
            'shape': matrix.shape,
            'alternatives': [
                {'id': alt.id, 'name': alt.name}
                for alt in matrix.alternative
            ],
            'criteria': [
                {
                    'id': crit.id, 
                    'name': crit.name,
                    'optimization_type': crit.optimization_type.value,
                    'weight': crit.weight
                }
                for crit in matrix.criteria
            ],
            'values': matrix.values.tolist()
        }
        
        return result
    
    def get_available_methods(self) -> List[Dict[str, Any]]:
        method_names = self._decision_service.get_available_methods()
        
        methods_info = []
        for name in method_names:
            try:
                info = self._decision_service.get_method_info(name)
                methods_info.append(info)
            except ServiceError:
                pass
        
        return methods_info
    
    def execute_method(self, method_name: str, 
                     parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        result = self._decision_service.execute_method(
            project=self._current_project,
            method_name=method_name,
            parameters=parameters
        )
        
        return self._format_result(result)
    
    def execute_all_methods(self, 
                         parameters: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        results = self._decision_service.execute_all_methods(
            project=self._current_project,
            parameters=parameters
        )
        
        formatted_results = {}
        for method_name, result in results.items():
            formatted_results[method_name] = self._format_result(result)
        
        return formatted_results
    
    def compare_methods(self, method_names: Optional[List[str]] = None) -> Dict[str, Any]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        comparison = self._decision_service.compare_methods(
            project=self._current_project,
            method_names=method_names
        )
        
        return comparison
    
    def perform_sensitivity_analysis(self, method_name: str, criteria_id: str,
                                  weight_range: Tuple[float, float] = (0.1, 1.0),
                                  steps: int = 10) -> Dict[str, Any]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        sensitivity_results = self._decision_service.perform_sensitivity_analysis(
            project=self._current_project,
            method_name=method_name,
            criteria_id=criteria_id,
            weight_range=weight_range,
            steps=steps
        )
        
        return sensitivity_results
    
    def get_result(self, method_name: str) -> Optional[Dict[str, Any]]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        result = self._current_project.get_result(method_name)
        
        if result is None:
            return None
        
        return self._format_result(result)
    
    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        if self._current_project is None:
            raise ValueError("There is no current project")
        
        results = self._current_project.results
       
        formatted_results = {}
        for method_name, result in results.items():
            formatted_results[method_name] = self._format_result(result)
        
        return formatted_results
    
    def _format_result(self, result: Result) -> Dict[str, Any]:
        best_id, best_name, best_score = result.get_best_alternative()
        
        formatted = {
            'method_name': result.method_name,
            'execution_time': result.execution_time,
            'parameters': result.parameters,
            'best_alternative': {
                'id': best_id,
                'name': best_name,
                'score': best_score
            },
            'alternatives': result.get_sorted_alternatives(),
            'rankings': result.rankings.tolist(),
            'scores': result.scores.tolist(),
            'created_at': result.created_at.isoformat(),
            'metadata': result.metadata
        }
        
        return formatted
        
            

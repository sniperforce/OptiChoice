from utils.api_client import ApiClient
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ProjectController:
    def __init__(self):
        self.api_client = ApiClient()
        self.current_project_id = None
    
    def get_current_project(self):
        """Get current project data"""
        if self.current_project_id:
            return self.api_client.get_project(self.current_project_id)
        return None

    def create_project(self, name, description="", decision_maker=""):
        """Create a new project"""
        result = self.api_client.create_project(name, description, decision_maker)
        if result:
            self.current_project_id = result.get("id")
            print(f"Project created with ID: {self.current_project_id}")
            return True
        return False
    
    def load_project(self, project_id):
        """Load an existing project"""
        project = self.api_client.get_project(project_id)
        if project:
            self.current_project_id = project_id
            return project
        return None
    
    def update_project(self, name=None, description=None, decision_maker=None):
        """Update basic project information"""
        if not self.current_project_id:
            return False
        
        data = {}
        if name is not None:
            data['name'] = name
        if description is not None:
            data['description'] = description
        if decision_maker is not None:
            data["decision_maker"] = decision_maker
        
        return self.api_client.update_project(self.current_project_id, data)
    
    def save_project(self, project_data: Dict[str, Any]) -> bool:
        """
        Save project data to backend
        
        Args:
            project_data: Complete project data including alternatives, criteria, matrix, and results
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.current_project_id:
                return False
            
            # Update project via API
            return self.api_client.update_project(self.current_project_id, project_data)
            
        except Exception as e:
            logger.error(f"Error saving project: {str(e)}")

    def save_complete_project(self, alternatives=None, criteria=None):
        """Save the complete project with all data from UI"""
        if not self.current_project_id:
            return False
        
        return self.api_client.save_project_complete(
            self.current_project_id, 
            alternatives=alternatives, 
            criteria=criteria
        )

    def get_all_projects(self):
        """Get all projects"""
        return self.api_client.get_projects()
    
    def delete_project(self, project_id=None):
        """Delete a project"""
        if project_id is None:
            project_id = self.current_project_id
        
        if not project_id:
            return False
        
        result = self.api_client.delete_project(project_id)

        if result and project_id == self.current_project_id:
            self.current_project_id = None
        
        return result
    
    def get_alternatives(self):
        """Get alternatives for current project"""
        print(f"DEBUG: get_alternatives called with project_id: {self.current_project_id}")
        
        if not self.current_project_id:
            print("DEBUG: No current project ID")
            return []
        
        result = self.api_client.get_alternatives(self.current_project_id)
        print(f"DEBUG: API returned alternatives: {result}")
        return result
    
    def get_criteria(self):
        print(f"DEBUG: get_criteria called with project_id: {self.current_project_id}")
        
        if not self.current_project_id:
            return []
            
        result = self.api_client.get_criteria(self.current_project_id)
        return result
    
    def get_decision_matrix(self):
        """Get decision matrix for current project"""
        if not self.current_project_id:
            return {}
        return self.api_client.get_decision_matrix(self.current_project_id)

    def save_decision_matrix(self, matrix_data, criteria_config):
        """Save decision matrix for current project"""
        if not self.current_project_id:
            return False
        return self.api_client.save_decision_matrix(
            self.current_project_id, matrix_data, criteria_config
        )

    def create_decision_matrix(self, name=None, values=None):
        """Create decision matrix for current project"""
        if not self.current_project_id:
            return None
        return self.api_client.create_decision_matrix(
            self.current_project_id, name, values
        )

    def update_matrix_values(self, updates):
        """Update matrix values for current project"""
        if not self.current_project_id:
            return False
        return self.api_client.update_matrix_values(self.current_project_id, updates)
    
    def get_available_methods(self) -> List[Dict[str, Any]]:
        """
        Get list of available MCDM methods
        
        Returns:
            List of method information dictionaries
        """
        try:
            # Try to get from API first
            methods = self.api_client.get_available_methods()
            if methods:
                return methods
        except Exception as e:
            logger.warning(f"Could not get methods from API: {e}")
        
        # Return default methods if API fails
        return [
            {
                'name': 'TOPSIS',
                'full_name': 'Technique for Order of Preference by Similarity to Ideal Solution',
                'description': 'TOPSIS is based on the concept that the chosen alternative should have the shortest geometric distance from the positive ideal solution and the longest geometric distance from the negative ideal solution.',
                'default_parameters': {
                    'normalization_method': 'minmax',
                    'distance_metric': 'euclidean'
                }
            },
            {
                'name': 'AHP',
                'full_name': 'Analytic Hierarchy Process',
                'description': 'AHP is a structured technique for organizing and analyzing complex decisions, based on mathematics and psychology.',
                'default_parameters': {
                    'consistency_ratio_threshold': 0.1,
                    'weight_calculation_method': 'eigenvector'
                }
            },
            {
                'name': 'PROMETHEE',
                'full_name': 'Preference Ranking Organization Method for Enrichment of Evaluations',
                'description': 'PROMETHEE is an outranking method based on pairwise comparisons and preference functions.',
                'default_parameters': {
                    'variant': 'II',
                    'default_preference_function': 'usual'
                }
            },
            {
                'name': 'ELECTRE',
                'full_name': 'Elimination and Choice Expressing Reality',
                'description': 'ELECTRE is based on concordance and discordance indices to establish outranking relations.',
                'default_parameters': {
                    'variant': 'III',
                    'concordance_threshold': 0.65,
                    'discordance_threshold': 0.35
                }
            }
        ]

    def execute_method(self, method_name, parameters=None):
        """Execute a specific MCDM method on current project"""
        if not self.current_project_id:
            return None
        return self.api_client.execute_method(self.current_project_id, method_name, parameters)

    def execute_all_methods(self, parameters=None):
        """Execute all MCDM methods on current project"""
        if not self.current_project_id:
            return {}
        return self.api_client.execute_all_methods(self.current_project_id, parameters)

    def compare_methods(self, method_names=None):
        """Compare results from multiple methods"""
        if not self.current_project_id:
            return {}
        return self.api_client.compare_methods(self.current_project_id, method_names)

    def get_method_results(self, method_name=None):
        """Get results for a specific method or all methods"""
        if not self.current_project_id:
            return {}
        return self.api_client.get_method_results(self.current_project_id, method_name)

    def perform_sensitivity_analysis(self, method_name, criteria_id, 
                                min_weight=0.1, max_weight=1.0, steps=10):
        """Perform sensitivity analysis on current project"""
        if not self.current_project_id:
            return {}
        return self.api_client.perform_sensitivity_analysis(
            self.current_project_id, method_name, criteria_id, 
            min_weight, max_weight, steps
        )
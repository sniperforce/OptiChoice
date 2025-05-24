import requests
import json

class ApiClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_projects(self):
        """Get all projects"""
        try:
            response = self.session.get(f"{self.base_url}/projects")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error getting projects: {e}")
            return []
    
    def create_project(self, name, description="", decision_maker=""):
        """Create a new project"""
        data = {
            "name": name,
            "description": description,
            "decision_maker": decision_maker
        }
        try:
            response = self.session.post(f"{self.base_url}/projects", json=data)
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Error creating project: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception creating project: {e}")
            return None
    
    def get_project(self, project_id):
        """Get a specific project"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error getting project: {e}")
            return None
    
    def update_project(self, project_id, data):
        """Update basic project information"""
        try:
            response = self.session.put(f"{self.base_url}/projects/{project_id}", json=data)
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"Error updating project: {e}")
            return None
    
    def delete_project(self, project_id):
        """Delete a project"""
        try:
            response = self.session.delete(f"{self.base_url}/projects/{project_id}")
            return response.status_code == 204
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False

    def save_project_complete(self, project_id, alternatives=None, criteria=None):
        """Save complete project with all components"""
        try:
            data = {}
            if alternatives:
                data['alternatives'] = alternatives
            if criteria:
                data['criteria'] = criteria
                
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/save-complete",
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error saving complete project: {e}")
            return False
    
    def get_alternatives(self, project_id):
        """Get alternatives for a project"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}/alternatives")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error getting alternatives: {e}")
            return []
    
    def get_criteria(self, project_id):
        """Get criteria for a project"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}/criteria")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error getting criteria: {e}")
            return []

    def get_decision_matrix(self, project_id):
        """Get decision matrix for a project"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}/matrix")
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"Error getting decision matrix: {e}")
            return {}

    def save_decision_matrix(self, project_id, matrix_data, criteria_config):
        """Save decision matrix for a project"""
        try:
            data = {
                'matrix_data': matrix_data,
                'criteria_config': criteria_config
            }
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/matrix",
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error saving decision matrix: {e}")
            return False

    def create_decision_matrix(self, project_id, name=None, values=None):
        """Create a new decision matrix"""
        try:
            data = {}
            if name:
                data['name'] = name
            if values:
                data['values'] = values
                
            response = self.session.post(
                f"{self.base_url}/projects/{project_id}/matrix/create",
                json=data
            )
            return response.json() if response.status_code == 201 else None
        except Exception as e:
            print(f"Error creating decision matrix: {e}")
            return None

    def update_matrix_values(self, project_id, updates):
        """Update specific matrix values"""
        try:
            data = {'updates': updates}
            response = self.session.put(
                f"{self.base_url}/projects/{project_id}/matrix/values",
                json=data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error updating matrix values: {e}")
            return False
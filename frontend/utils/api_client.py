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

    def save_project_complete(self, project_id):
        """Save complete project with all components"""
        try:
            response = self.session.post(f"{self.base_url}/projects/{project_id}/save-complete")
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
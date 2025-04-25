import requests
import json

class ApiClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_projects(self):
        response = self.session.get(f"{self.base_url}/projects")
        return response.json if response.status_code == 200 else []
    
    def create_project(self, name, description="", decision_maker=""):
        data={
            "name": name,
            "description": description,
            "decision_maker": decision_maker
        }
        response = self.session.post(f"{self.base_url}/projects", json=data)
        return response.json() if response.status_code == 201 else None
    
    def get_project(self, project_id):
        response = self.session.get(f"{self.base_url}/projects/{project_id}")
        return response.json() if response.status_code == 200 else None
    
    def update_project(self, project_id, data):
        response = self.session.put(f"{self.base_url}/projects/{project_id}", json=data)
        return response.json() if response.status_code == 200 else None
    
    def delete_project(self, project_id):
        response = self.session.delete(f"{self.base_url}/projects/{project_id}")
        return response.status_code == 204

    # Alternatives endpoints
    def get_alternatives(self, project_id):
        response = self.session.get(f"{self.base_url}/projects/{project_id}/alternatives")
        return response.json() if response.status_code == 200 else []

    def add_alternative(self, project_id, alt_id, name, description=""):
        data={
            'id': alt_id,
            'name':name,
            'description': description
        }
        response = self.session.post(f"{self.base_url}/projects/{project_id}/alternatives", json=data)
        return response.json() if response.status_code == 201 else None
    
    def update_alternative(self, project_id, alt_id, data):
        response = self.session.put(f"{self.base_url}/projects/{project_id}/alternatives/{alt_id}", json=data)
        return response.json() if response.status_code == 200 else None
    
    def delete_alternative(self, project_id, alt_id):
        response = self.session.delete(f"{self.base_url}/projects/{project_id}/alternatives/{alt_id}")
        return response.status_code == 204
    
    # Criteria endpoints
    def get_criteria(self, project_id):
        response = self.session.get(f"{self.base_url}/projects/{project_id}/criteria")
        return response.json() if response.status_code == 200 else []
    
    def add_criterion(self, project_id, crit_id, name, optimization_type="maximize",
                      scale_type="quantitative", weight=1.0, unit=""):
        data={
            "id": crit_id,
            "name": name,
            "description": "",
            "optimization_type": optimization_type,
            "scale_type": scale_type,
            "weight": weight,
            "unit": unit
        }
        response = self.session.post(f"{self.base_url}/projects/{project_id}/criteria", json=data)
        return response.json() if response.status_code == 201 else None
    
    def update_criterion(self, project_id, crit_id, data):
        response = self.session.put(f"{self.base_url}/projects/{project_id}/criteria/{crit_id}", json=data)
        return response.json() if response.status_code == 200 else None
    
    def delete_criterion(self, project_id, crit_id):
        response = self.session.delete(f"{self.base_url}/projects/{project_id}/criteria/{crit_id}")
        return response.status_code == 204



    
        
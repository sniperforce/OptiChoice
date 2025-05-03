import requests
import json

class ApiClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def get_projects(self):
        response = self.session.get(f"{self.base_url}/projects")
        return response.json() if response.status_code == 200 else []
    
    def create_project(self, name, description="", decision_maker=""):
        data = {
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

    def save_project(self, project_id):
        """Explicitly save a project after alternatives and criteria have been added"""
        try:
            response = self.session.post(f"{self.base_url}/projects/{project_id}/save")
            
            if response.status_code == 400:
                # Error de validación - podríamos registrar esto o mostrar más información
                error_data = response.json()
                error_details = error_data.get('details', [])
                print(f"Validation errors: {error_details}")
                
            return response.status_code == 200
        except Exception as e:
            print(f"Error saving project: {str(e)}")
            return False
    
    # Alternatives endpoints
    def get_alternatives(self, project_id):
        response = self.session.get(f"{self.base_url}/projects/{project_id}/alternatives")
        return response.json() if response.status_code == 200 else []

    def add_alternative(self, project_id, alt_id, name, description=""):
        if not alt_id or not name:
            print("Error: Alternative ID and name are required")
            return None
            
        data = {
            'id': alt_id,
            'name': name,
            'description': description
        }
        
        try:
            response = self.session.post(f"{self.base_url}/projects/{project_id}/alternatives", json=data)
            
            if response.status_code == 201:
                return response.json()
            else:
                error_data = response.json() if response.text else {"error": "Unknown error"}
                print(f"Error adding alternative: {error_data.get('error', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"Exception when adding alternative: {str(e)}")
            return None
    
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


    
        
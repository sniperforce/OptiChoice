from utils.api_client import ApiClient

class ProjectController:
    def __init__(self):
        self.api_client = ApiClient()
        self.current_project_id = None
    
    @property
    def current_project(self):
        if self.current_project_id:
            return self.api_client.get_project(self.current_project_id)
        return None

    def create_project(self, name, description="", decision_maker=""):
        result = self.api_client.create_project(name, description, decision_maker)
        if result:
            self.current_project_id = result.get("id")
            return True
        return False
    
    def load_project(self, project_id):
        project = self.api_client.get_project(project_id)
        if project:
            self.current_project_id = project_id
            return project
        return None
    
    def update_project(self, name=None, description=None, decision_maker=None):
        if not self.current_project_id:
            return False
        
        data={}
        if name is not None:
            data['name'] = name
        if description is not None:
            data['description'] = description
        if decision_maker is not None:
            data["decision_maker"] = decision_maker
        
        return self.api_client.update_project(self.current_project_id, data)
    
    def save_project(self):
        """Explicitly save the current project"""
        if not self.current_project_id:
            return False
        
        response = self.api_client.save_project(self.current_project_id)
        return response

    def get_all_projects(self):
        return self.api_client.get_projects()
    
    def delete_project(self, project_id=None):
        if project_id is None:
            project_id = self.current_project_id
        
        if not project_id:
            return False
        
        result = self.api_client.delete_project(project_id)

        if result and project_id == self.current_project_id:
            self.current_project_id = None
        
        return result
    
    def get_alternative(self):
        if not self.current_project_id:
            return []
        
        return self.api_client.get_alternatives(self.current_project_id)
    
    def add_alternative(self, alt_id, name, description=""):
        if not self.current_project_id:
            return None
        
        return self.api_client.add_alternative(self.current_project_id, alt_id, name, description)
    
    def update_alternative(self, alt_id, name=None, description=None):
        if not self.current_project_id:
            return False
        
        data = {}
        if name is not None:
            data['name'] = name
        if description is not None:
            data['description'] = description
        
        return self.api_client.update_alternative(self.current_project_id, alt_id, data)
    
    def delete_alternative(self, alt_id):
        if not self.current_project_id:
            return False
        return self.api_client.delete_alternative(self.current_project_id, alt_id)
    
    def get_criteria(self):
        if not self.current_project_id:
            return []
        return self.api_client.get_criteria(self.current_project_id)
    
    def add_criterion(self, crit_id, name, optimization_type="maximize", 
                     scale_type="quantitative", weight=1.0, unit=""):
        if not self.current_project_id:
            return None
        return self.api_client.add_criterion(
            self.current_project_id, crit_id, name, 
            optimization_type, scale_type, weight, unit)
    
    def update_criterion(self, crit_id, name=None, optimization_type=None, 
                        scale_type=None, weight=None, unit=None):
        if not self.current_project_id:
            return False
        
        data = {}
        if name is not None:
            data['name'] = name
        if optimization_type is not None:
            data['optimization_type'] = optimization_type
        if scale_type is not None:
            data['scale_type'] = scale_type
        if weight is not None:
            data['weight'] = weight
        if unit is not None:
            data['unit'] = unit
        
        return self.api_client.update_criterion(
            self.current_project_id, crit_id, data)
    
    def delete_criterion(self, crit_id):
        if not self.current_project_id:
            return False
        return self.api_client.delete_criterion(
            self.current_project_id, crit_id) 
    
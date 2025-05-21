from utils.api_client import ApiClient

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
    
    def save_complete_project(self):
        """Save the complete project with all data from UI"""
        if not self.current_project_id:
            return False
        
        # Get data from the problem tab
        from views.main_window import MCDMApplication
        # This is a bit hacky but necessary to get the table data
        # In a better architecture, we'd pass this data as parameters
        
        return self.api_client.save_project_complete(self.current_project_id)

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
        if not self.current_project_id:
            return []
        
        return self.api_client.get_alternatives(self.current_project_id)
    
    def get_criteria(self):
        """Get criteria for current project"""
        if not self.current_project_id:
            return []
        return self.api_client.get_criteria(self.current_project_id)
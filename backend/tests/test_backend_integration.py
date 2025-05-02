# backend/tests/integration/test_backend_integration.py
import pytest
import json
import os
import tempfile
import shutil
from main import app
from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from infrastructure.persistence.file_project_repository import FileProjectRepository
from presentation.controllers.main_controller import MainController
from application.services.project_service import ProjectService

@pytest.fixture
def test_client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_project():
    """Create a mock project for testing."""
    project = Project(name="Test Project", description="Test Description")
    
    # Add alternatives
    project.add_alternative(Alternative(id="alt1", name="Alternative 1"))
    project.add_alternative(Alternative(id="alt2", name="Alternative 2"))
    
    # Add criteria
    project.add_criteria(Criteria(
        id="crit1", 
        name="Criteria 1", 
        optimization_type=OptimizationType.MAXIMIZE, 
        weight=0.6
    ))
    project.add_criteria(Criteria(
        id="crit2", 
        name="Criteria 2", 
        optimization_type=OptimizationType.MINIMIZE, 
        weight=0.4
    ))
    
    # Create decision matrix
    project.create_decision_matrix(values=[[1.0, 2.0], [3.0, 4.0]])
    
    return project

class TestBackendIntegration:
    def test_methods(self, test_client):
        """Test GET /api/methods endpoint."""
        response = test_client.get('/api/methods')
        assert response.status_code == 200
        
        # Check response data
        result = json.loads(response.data)
        assert isinstance(result, list)
        
        # Check that key methods are included
        method_names = [method['name'] for method in result]
        assert 'TOPSIS' in method_names
        assert 'AHP' in method_names
        assert 'ELECTRE' in method_names
        assert 'PROMETHEE' in method_names
    
    def test_project_service(self, mock_project):
        """Test project service functionality."""
        # Create a temporary repo
        temp_dir = tempfile.mkdtemp()
        try:
            # Create repository and services
            repo = FileProjectRepository(base_dir=temp_dir)
            project_service = ProjectService(repo)
            
            # Test save_project
            saved_project = project_service.save_project(mock_project)
            assert saved_project.id == mock_project.id
            assert saved_project.name == "Test Project"
            
            # Test get_project
            retrieved_project = project_service.get_project(saved_project.id)
            assert retrieved_project.id == saved_project.id
            assert retrieved_project.name == saved_project.name
            assert len(retrieved_project.alternatives) == 2
            assert len(retrieved_project.criteria) == 2
            
            # Test get_all_projects
            projects = project_service.get_all_projects()
            assert len(projects) == 1
            
            # Test updating a project
            retrieved_project.name = "Updated Project"
            updated_project = project_service.save_project(retrieved_project)
            assert updated_project.name == "Updated Project"
            
            # Test search_projects
            search_results = project_service.search_projects("Updated")
            assert len(search_results) == 1
            assert search_results[0].name == "Updated Project"
            
            # Test delete_project
            assert project_service.delete_project(saved_project.id) is True
            
            projects_after_delete = project_service.get_all_projects()
            assert len(projects_after_delete) == 0
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_controller_functionality(self):
        """Test controller functionality directly."""
        # Create a temporary repo
        temp_dir = tempfile.mkdtemp()
        try:
            # Create repository and controller
            repo = FileProjectRepository(base_dir=temp_dir)
            controller = MainController(repo)
            
            # Test new_project
            project = controller.new_project(
                name="Test Project", 
                description="Test Description", 
                decision_maker="Test User"
            )
            assert project.name == "Test Project"
            assert project.description == "Test Description"
            
            # Add alternatives (required for validation)
            controller.add_alternative(
                id="alt1",
                name="Alternative 1",
                description="Test alternative"
            )
            controller.add_alternative(
                id="alt2",
                name="Alternative 2",
                description="Second test alternative"
            )
            
            # Add criteria (required for validation)
            controller.add_criteria(
                id="crit1",
                name="Criteria 1",
                optimization_type="maximize",
                weight=0.6
            )
            controller.add_criteria(
                id="crit2",
                name="Criteria 2",
                optimization_type="minimize",
                weight=0.4
            )
            
            # Now save_project should work
            saved_project = controller.save_project()
            project_id = saved_project.id
            
            # Test load_project
            loaded_project = controller.load_project(project_id)
            assert loaded_project.id == project_id
            assert loaded_project.name == "Test Project"
            
            # Test get_alternative
            alternatives = controller.get_all_alternatives()
            assert len(alternatives) == 2
            assert alternatives[0]['id'] == "alt1"
            
            # Test get_criteria
            criteria = controller.get_all_criteria()
            assert len(criteria) == 2
            assert criteria[0]['id'] == "crit1"
            
            # Test create_decision_matrix
            matrix = controller.create_decision_matrix(
                name="Test Matrix",
                values=[[1.0, 2.0], [3.0, 4.0]]
            )
            assert matrix['name'] == "Test Matrix"
            assert matrix['shape'] == (2, 2)
            
            # Test get_matrix
            matrix_data = controller.get_decision_matrix()
            assert matrix_data['name'] == "Test Matrix"
            assert len(matrix_data['alternatives']) == 2
            assert len(matrix_data['criteria']) == 2
            
            # Test get_all_projects
            projects = controller.get_all_projects()
            assert len(projects) == 1
            
            # Test delete_project
            assert controller.delete_project(project_id) is True
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_export_import(self, mock_project):
        """Test export and import functionality."""
        # Create a temporary dir for exported files
        temp_dir = tempfile.mkdtemp()
        try:
            # Create repository and services
            repo = FileProjectRepository(base_dir=temp_dir)
            project_service = ProjectService(repo)
            
            # Save the mock project
            saved_project = project_service.save_project(mock_project)
            
            # Test export_to_json
            json_path = os.path.join(temp_dir, "test_project.json")
            project_service.export_to_json(saved_project, json_path)
            assert os.path.exists(json_path)
            
            # Test import_from_json
            imported_project = project_service.import_from_json(json_path)
            assert imported_project.name == mock_project.name
            assert len(imported_project.alternatives) == len(mock_project.alternatives)
            assert len(imported_project.criteria) == len(mock_project.criteria)
            
            # Test export_to_excel
            excel_path = os.path.join(temp_dir, "test_project.xlsx")
            project_service.export_to_excel(saved_project, excel_path)
            assert os.path.exists(excel_path)
            
            # Test export_to_csv
            csv_path = os.path.join(temp_dir, "test_project.csv")
            project_service.export_to_csv(saved_project, csv_path)
            assert os.path.exists(os.path.join(temp_dir, "test_project_info.csv"))
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
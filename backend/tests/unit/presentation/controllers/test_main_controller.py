import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from presentation.controllers.main_controller import MainController
from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from domain.repositories.project_repository import ProjectRepository
from application.services.project_service import ProjectService
from application.services.decision_service import DecisionService
from utils.exceptions import ServiceError

class TestMainController:
    
    @pytest.fixture
    def mock_repository(self):
        """Fixture providing a mock project repository."""
        repository = Mock(spec=ProjectRepository)
        repository.get_by_id.return_value = None
        repository.save.return_value = None
        repository.delete.return_value = True
        repository.get_all.return_value = []
        repository.search.return_value = []
        return repository
    
    @pytest.fixture
    def mock_project_service(self, mock_repository):
        """Fixture providing a mock project service."""
        service = Mock(spec=ProjectService)
        service._repository = mock_repository
        return service
    
    @pytest.fixture
    def mock_decision_service(self):
        """Fixture providing a mock decision service."""
        service = Mock(spec=DecisionService)
        service.get_available_methods.return_value = ['TOPSIS', 'AHP', 'ELECTRE', 'PROMETHEE']
        return service
    
    @pytest.fixture
    def main_controller(self, mock_repository, mock_project_service, mock_decision_service):
        """Fixture providing a main controller with mocked dependencies."""
        with patch('presentation.controllers.main_controller.ProjectService', return_value=mock_project_service):
            with patch('presentation.controllers.main_controller.DecisionService', return_value=mock_decision_service):
                controller = MainController(mock_repository)
                controller._project_service = mock_project_service
                controller._decision_service = mock_decision_service
                return controller
    
    @pytest.fixture
    def sample_project(self):
        """Fixture providing a sample project for testing."""
        project = Project(name="Test Project", description="Test Description")
        project.add_alternative(Alternative(id="alt1", name="Alternative 1"))
        project.add_alternative(Alternative(id="alt2", name="Alternative 2"))
        project.add_criteria(Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE))
        project.add_criteria(Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE))
        return project
    
    @pytest.fixture
    def sample_result(self):
        """Fixture providing a sample result for testing."""
        return Result(
            method_name="TOPSIS",
            alternative_ids=["alt1", "alt2"],
            alternative_names=["Alternative 1", "Alternative 2"],
            scores=np.array([0.7, 0.5])
        )
    
    def test_new_project(self, main_controller, mock_decision_service):
        """Test creating a new project."""
        mock_project = Mock(spec=Project)
        mock_project.id = "123"
        mock_decision_service.create_project.return_value = mock_project
        
        project = main_controller.new_project(
            name="Test Project",
            description="Test Description",
            decision_maker="Test User"
        )
        
        assert project == mock_project
        assert main_controller.current_project == mock_project
        mock_decision_service.create_project.assert_called_once_with(
            name="Test Project",
            description="Test Description",
            decision_maker="Test User"
        )
    
    def test_save_project_no_current_project(self, main_controller):
        """Test saving project when no current project exists."""
        main_controller._current_project = None
        
        with pytest.raises(ValueError, match="There is no current project to save"):
            main_controller.save_project()
    
    def test_save_project_success(self, main_controller, mock_project_service, sample_project):
        """Test successful project saving."""
        main_controller._current_project = sample_project
        mock_project_service.save_project.return_value = sample_project
        
        saved_project = main_controller.save_project()
        
        assert saved_project == sample_project
        mock_project_service.save_project.assert_called_once_with(sample_project)
    
    def test_load_project(self, main_controller, mock_project_service, sample_project):
        """Test loading a project."""
        project_id = str(uuid4())
        mock_project_service.get_project.return_value = sample_project
        
        loaded_project = main_controller.load_project(project_id)
        
        assert loaded_project == sample_project
        assert main_controller.current_project == sample_project
        mock_project_service.get_project.assert_called_once_with(project_id)
    
    def test_get_all_projects(self, main_controller, mock_project_service, sample_project):
        """Test getting all projects."""
        mock_project_service.get_all_projects.return_value = [sample_project]
        
        projects = main_controller.get_all_projects()
        
        assert len(projects) == 1
        assert projects[0]['name'] == "Test Project"
        assert projects[0]['n_alternatives'] == 2
        assert projects[0]['n_criteria'] == 2
    
    def test_delete_project(self, main_controller, mock_project_service, sample_project):
        """Test deleting a project."""
        project_id = str(uuid4())
        sample_project.id = project_id
        main_controller._current_project = sample_project
        mock_project_service.delete_project.return_value = True
        
        result = main_controller.delete_project(project_id)
        
        assert result is True
        assert main_controller.current_project is None
        mock_project_service.delete_project.assert_called_once_with(project_id)
    
    def test_add_alternative(self, main_controller, mock_decision_service, sample_project):
        """Test adding an alternative to the current project."""
        main_controller._current_project = sample_project
        new_alternative = Alternative(id="alt3", name="Alternative 3")
        mock_decision_service.add_alternative.return_value = new_alternative
        
        result = main_controller.add_alternative(
            id="alt3",
            name="Alternative 3",
            description="Test description"
        )
        
        assert result == new_alternative
        mock_decision_service.add_alternative.assert_called_once()
    
    def test_add_alternative_no_current_project(self, main_controller):
        """Test adding alternative when no current project exists."""
        main_controller._current_project = None
        
        with pytest.raises(ValueError, match="There is no current project"):
            main_controller.add_alternative("alt1", "Alternative 1")
    
    def test_add_criteria(self, main_controller, mock_decision_service, sample_project):
        """Test adding a criterion to the current project."""
        main_controller._current_project = sample_project
        new_criteria = Criteria(id="crit3", name="Criteria 3")
        mock_decision_service.add_criteria.return_value = new_criteria
        
        result = main_controller.add_criteria(
            id="crit3",
            name="Criteria 3",
            optimization_type="maximize",
            weight=1.0
        )
        
        assert result == new_criteria
        mock_decision_service.add_criteria.assert_called_once()
    
    def test_create_decision_matrix(self, main_controller, mock_decision_service, sample_project):
        """Test creating a decision matrix."""
        main_controller._current_project = sample_project
        mock_matrix = Mock(spec=DecisionMatrix)
        mock_matrix.name = "Test Matrix"
        mock_matrix.shape = (2, 2)
        mock_matrix.alternatives = sample_project.alternatives
        mock_matrix.criteria = sample_project.criteria
        mock_matrix.values = Mock()
        mock_matrix.values.size = 4
        
        mock_decision_service.create_decision_matrix.return_value = mock_matrix
        
        result = main_controller.create_decision_matrix()
        
        assert result['name'] == "Test Matrix"
        assert result['shape'] == (2, 2)
        assert result['has_values'] is True
    
    def test_execute_method(self, main_controller, mock_decision_service, sample_project, sample_result):
        """Test executing a specific MCDM method."""
        main_controller._current_project = sample_project
        mock_decision_service.execute_method.return_value = sample_result
        
        result = main_controller.execute_method("TOPSIS", {"normalization": "vector"})
        
        assert result['method_name'] == "TOPSIS"
        assert result['best_alternative']['id'] == "alt1"
        assert result['best_alternative']['score'] == 0.7
        mock_decision_service.execute_method.assert_called_once_with(
            project=sample_project,
            method_name="TOPSIS",
            parameters={"normalization": "vector"}
        )
    
    def test_execute_all_methods(self, main_controller, mock_decision_service, sample_project, sample_result):
        """Test executing all MCDM methods."""
        main_controller._current_project = sample_project
        mock_decision_service.execute_all_methods.return_value = {
            "TOPSIS": sample_result,
            "AHP": sample_result
        }
        
        results = main_controller.execute_all_methods()
        
        assert len(results) == 2
        assert "TOPSIS" in results
        assert "AHP" in results
        assert results["TOPSIS"]["method_name"] == "TOPSIS"
    
    def test_compare_methods(self, main_controller, mock_decision_service, sample_project):
        """Test comparing different MCDM methods."""
        main_controller._current_project = sample_project
        comparison_data = {
            'methods': ['TOPSIS', 'AHP'],
            'alternatives': {},
            'rankings_correlation': {},
            'best_alternatives': {}
        }
        mock_decision_service.compare_methods.return_value = comparison_data
        
        result = main_controller.compare_methods(['TOPSIS', 'AHP'])
        
        assert result == comparison_data
        mock_decision_service.compare_methods.assert_called_once_with(
            project=sample_project,
            method_names=['TOPSIS', 'AHP']
        )
    
    def test_sensitivity_analysis(self, main_controller, mock_decision_service, sample_project):
        """Test performing sensitivity analysis."""
        main_controller._current_project = sample_project
        sensitivity_data = {
            'method': 'TOPSIS',
            'criteria': {'id': 'crit1', 'name': 'Criteria 1'},
            'weight_range': [0.1, 1.0],
            'weights_tested': [0.1, 0.3, 0.5, 0.7, 0.9],
            'rankings': [],
            'scores': [],
            'stability': {}
        }
        mock_decision_service.perform_sensitivity_analysis.return_value = sensitivity_data
        
        result = main_controller.perform_sensitivity_analysis(
            method_name='TOPSIS',
            criteria_id='crit1',
            weight_range=(0.1, 1.0),
            steps=5
        )
        
        assert result == sensitivity_data
        mock_decision_service.perform_sensitivity_analysis.assert_called_once()
    
    def test_export_project(self, main_controller, mock_project_service, sample_project):
        """Test exporting project to different formats."""
        main_controller._current_project = sample_project
        
        # Test JSON export
        main_controller.export_project('test.json', 'json')
        mock_project_service.export_to_json.assert_called_once()
        
        # Test Excel export
        main_controller.export_project('test.xlsx', 'excel')
        mock_project_service.export_to_excel.assert_called_once()
        
        # Test CSV export
        main_controller.export_project('test.csv', 'csv')
        mock_project_service.export_to_csv.assert_called_once()
        
        # Test PDF export
        main_controller.export_project('test.pdf', 'pdf')
        mock_project_service.export_to_pdf.assert_called_once()
    
    def test_import_project(self, main_controller, mock_project_service, sample_project):
        """Test importing project from different formats."""
        mock_project_service.import_from_json.return_value = sample_project
        mock_project_service.import_from_excel.return_value = sample_project
        mock_project_service.import_from_csv.return_value = sample_project
        
        # Test JSON import
        project = main_controller.import_project('test.json', 'json')
        assert project == sample_project
        assert main_controller.current_project == sample_project
        
        # Test Excel import
        project = main_controller.import_project('test.xlsx', 'excel')
        assert project == sample_project
        
        # Test CSV import
        project = main_controller.import_project('test.csv', 'csv')
        assert project == sample_project
    
    def test_format_result(self, main_controller, sample_result):
        """Test formatting a result for output."""
        formatted = main_controller._format_result(sample_result)
        
        assert formatted['method_name'] == "TOPSIS"
        assert formatted['best_alternative']['id'] == "alt1"
        assert formatted['best_alternative']['score'] == 0.7
        assert len(formatted['alternatives']) == 2
        assert formatted['rankings'] == sample_result.rankings.tolist()
        assert formatted['scores'] == sample_result.scores.tolist()
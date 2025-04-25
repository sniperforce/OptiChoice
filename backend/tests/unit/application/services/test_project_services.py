import pytest
import os
import json
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from application.services.project_service import ProjectService
from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from domain.repositories.project_repository import ProjectRepository
from utils.exceptions import ServiceError, ValidationError, RepositoryError

class TestProjectService:
    
    @pytest.fixture
    def mock_repository(self):
        """Fixture providing a mock project repository."""
        repository = Mock(spec=ProjectRepository)
        return repository
    
    @pytest.fixture
    def project_service(self, mock_repository):
        """Fixture providing a project service instance with mock repository."""
        return ProjectService(mock_repository)
    
    @pytest.fixture
    def sample_project(self):
        """Fixture providing a sample project for testing."""
        project = Project(name="Test Project", description="Test Description")
        
        # Add alternatives
        alternatives = [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2")
        ]
        for alt in alternatives:
            project.add_alternative(alt)
        
        # Add criteria
        criteria = [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE, weight=0.6),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE, weight=0.4)
        ]
        for crit in criteria:
            project.add_criteria(crit)
        
        # Create decision matrix
        project.create_decision_matrix(values=[[1.0, 2.0], [3.0, 4.0]])
        
        # Add result
        result = Result(
            method_name="TOPSIS",
            alternative_ids=["alt1", "alt2"],
            alternative_names=["Alternative 1", "Alternative 2"],
            scores=[0.7, 0.5]
        )
        project.add_result("TOPSIS", result)
        
        return project
    
    def test_save_project_success(self, project_service, mock_repository, sample_project):
        """Test successful project saving."""
        mock_repository.save.return_value = sample_project
        
        saved_project = project_service.save_project(sample_project)
        
        assert saved_project == sample_project
        mock_repository.save.assert_called_once_with(sample_project)
    
    def test_save_project_validation_error(self, project_service, mock_repository):
        """Test project saving with validation error."""
        invalid_project = Project(name="")  # Empty name should be invalid
        
        with pytest.raises(ServiceError) as exc_info:
            project_service.save_project(invalid_project)
        
        assert "Validation error when saving project" in str(exc_info.value)
        mock_repository.save.assert_not_called()
    
    def test_save_project_repository_error(self, project_service, mock_repository, sample_project):
        """Test project saving with repository error."""
        mock_repository.save.side_effect = RepositoryError("Database error")
        
        with pytest.raises(ServiceError) as exc_info:
            project_service.save_project(sample_project)
        
        assert "Error saving project to repository" in str(exc_info.value)
    
    def test_get_project_success(self, project_service, mock_repository, sample_project):
        """Test successful project retrieval."""
        project_id = str(uuid4())
        mock_repository.get_by_id.return_value = sample_project
        
        retrieved_project = project_service.get_project(project_id)
        
        assert retrieved_project == sample_project
        mock_repository.get_by_id.assert_called_once_with(project_id)
    
    def test_get_project_not_found(self, project_service, mock_repository):
        """Test project retrieval when project not found."""
        project_id = str(uuid4())
        mock_repository.get_by_id.return_value = None
        
        with pytest.raises(ServiceError) as exc_info:
            project_service.get_project(project_id)
        
        assert f"No project found with ID: {project_id}" in str(exc_info.value)
    
    def test_get_all_projects_success(self, project_service, mock_repository, sample_project):
        """Test successful retrieval of all projects."""
        mock_repository.get_all.return_value = [sample_project]
        
        projects = project_service.get_all_projects()
        
        assert len(projects) == 1
        assert projects[0] == sample_project
        mock_repository.get_all.assert_called_once()
    
    def test_delete_project_success(self, project_service, mock_repository):
        """Test successful project deletion."""
        project_id = str(uuid4())
        mock_repository.delete.return_value = True
        
        result = project_service.delete_project(project_id)
        
        assert result == True
        mock_repository.delete.assert_called_once_with(project_id)
    
    def test_search_projects_success(self, project_service, mock_repository, sample_project):
        """Test successful project search."""
        query = "test"
        mock_repository.search.return_value = [sample_project]
        
        projects = project_service.search_projects(query)
        
        assert len(projects) == 1
        assert projects[0] == sample_project
        mock_repository.search.assert_called_once_with(query)
    
    def test_duplicate_project_success(self, project_service, mock_repository, sample_project):
        """Test successful project duplication."""
        project_id = str(uuid4())
        new_name = "Copy of Test Project"
        
        mock_repository.get_by_id.return_value = sample_project
        def mock_save(project):
            return project
        
        mock_repository.save.side_effect = mock_save
        
        duplicated_project = project_service.duplicate_project(project_id, new_name)
        
        assert duplicated_project.name == new_name
        mock_repository.get_by_id.assert_called_once_with(project_id)
        mock_repository.save.assert_called_once()
    
    @patch('application.services.project_service.Workbook')
    def test_export_to_excel_success(self, mock_workbook, project_service, sample_project, tmp_path):
        """Test successful project export to Excel."""
        file_path = tmp_path / "test_project.xlsx"
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb
        
        def create_sheet(title):
            sheet = MagicMock()
            sheet.title = title
            return sheet

        mock_wb.create_sheet.side_effect = create_sheet
        project_service.export_to_excel(sample_project, str(file_path))
        mock_workbook.assert_called_once()
        mock_wb.save.assert_called_once_with(str(file_path))
    
    def test_export_to_csv_success(self, project_service, sample_project, tmp_path):
        """Test successful project export to CSV."""
        file_path = tmp_path / "test_project.csv"
        
        project_service.export_to_csv(sample_project, str(file_path))
        
        # Check that files were created
        assert os.path.exists(tmp_path / "test_project_info.csv")
        assert os.path.exists(tmp_path / "test_project_alternatives.csv")
        assert os.path.exists(tmp_path / "test_project_criteria.csv")
    
    @patch('application.services.project_service.SimpleDocTemplate') 
    @patch('application.services.project_service.Table')
    @patch('application.services.project_service.Paragraph')
    @patch('application.services.project_service.Spacer')
    @patch('application.services.project_service.getSampleStyleSheet')
    def test_export_to_pdf_success(self, mock_get_styles, mock_spacer, mock_paragraph, 
                                    mock_table, mock_doc_template, project_service, 
                                    sample_project, tmp_path):
        """Test successful project export to PDF."""
        file_path = tmp_path / "test_project.pdf"
        mock_doc = MagicMock()
        mock_doc_template.return_value = mock_doc
        
        mock_styles = MagicMock()
        mock_get_styles.return_value = mock_styles
        
        mock_paragraph.return_value = MagicMock()
        mock_spacer.return_value = MagicMock()
        mock_table.return_value = MagicMock()
        
        project_service.export_to_pdf(sample_project, str(file_path))
        
        mock_doc_template.assert_called_once()

        mock_doc.build.assert_called_once()
    
    def test_export_to_json_success(self, project_service, sample_project, tmp_path):
        """Test successful project export to JSON."""
        file_path = tmp_path / "test_project.json"
        
        project_service.export_to_json(sample_project, str(file_path))
        
        # Check that file was created and contains correct data
        assert os.path.exists(file_path)
        with open(file_path, 'r') as f:
            data = json.load(f)
        assert data['name'] == "Test Project"
    
    def test_import_from_json_success(self, project_service, sample_project, tmp_path):
        """Test successful project import from JSON."""
        file_path = tmp_path / "test_project.json"
        
        # First export to create a valid JSON file
        project_data = sample_project.to_dict()
        with open(file_path, 'w') as f:
            json.dump(project_data, f)
        
        imported_project = project_service.import_from_json(str(file_path))
        
        assert imported_project.name == sample_project.name
        assert len(imported_project.alternatives) == len(sample_project.alternatives)
        assert len(imported_project.criteria) == len(sample_project.criteria)
    
    def test_import_from_json_file_not_found(self, project_service):
        """Test import from non-existent JSON file."""
        with pytest.raises(ServiceError) as exc_info:
            project_service.import_from_json("nonexistent.json")
        
        assert "Unexpected error when importing project" in str(exc_info.value)
    
    @patch('pandas.ExcelFile')
    @patch('pandas.read_excel')
    def test_import_from_excel_success(self, mock_read_excel, mock_excel_file, project_service):
        """Test successful project import from Excel."""
        # Mock Excel file structure
        mock_excel_file.return_value.sheet_names = [
            "Project Information", "Alternatives", "Criteria", "Decision Matrix"
        ]
        
        # Mock data frames
        info_df = pd.DataFrame({
            0: ["Name", "Description", "Decision Maker"],
            1: ["Test Project", "Test Description", "John Doe"]
        })
        
        alternatives_df = pd.DataFrame({
            "ID": ["alt1", "alt2"],
            "Name": ["Alternative 1", "Alternative 2"],
            "Description": ["Desc 1", "Desc 2"]
        })
        
        criteria_df = pd.DataFrame({
            "ID": ["crit1", "crit2"],
            "Name": ["Criteria 1", "Criteria 2"],
            "Optimization Type": ["maximize", "minimize"],
            "Scale Type": ["quantitative", "quantitative"],
            "Weight": [0.6, 0.4],
            "Unit": ["unit1", "unit2"]
        })

        matrix_df = pd.DataFrame({
            "Alternative": ["Alternative 1", "Alternative 2"],
            "Criteria 1": [1.0, 3.0],
            "Criteria 2": [2.0, 4.0]
        })
        
        mock_read_excel.side_effect = [info_df, alternatives_df, criteria_df, matrix_df]
        
        imported_project = project_service.import_from_excel("test.xlsx")
        
        assert imported_project.name == "Test Project"
        assert len(imported_project.alternatives) == 2
        assert len(imported_project.criteria) == 2
    
    def test_import_from_csv_success(self, project_service, tmp_path):
        """Test successful project import from CSV."""
        base_path = tmp_path / "test_project"
        
        # Create CSV files with test data
        info_path = tmp_path / "test_project_info.csv"
        
        with open(info_path, 'w', newline='') as f:
            f.write("Field,Value\n")
            f.write("Name,Test Project\n")
            f.write("Description,Test Description\n")
        
        alternatives_path = tmp_path / "test_project_alternatives.csv"
        with open(alternatives_path, 'w', newline='') as f:
            f.write("ID,Name,Description\n")
            f.write("alt1,Alternative 1,Desc 1\n")
            f.write("alt2,Alternative 2,Desc 2\n")
        
        criteria_path = tmp_path / "test_project_criteria.csv"
        with open(criteria_path, 'w', newline='') as f:
            f.write("ID,Name,Description,Optimization Type,Scale Type,Weight,Unit\n")
            f.write("crit1,Criteria 1,Desc 1,maximize,quantitative,0.6,unit1\n")
            f.write("crit2,Criteria 2,Desc 2,minimize,quantitative,0.4,unit2\n")
        
        imported_project = project_service.import_from_csv(str(base_path))
        
        assert imported_project.name == "Test Project"
        assert len(imported_project.alternatives) == 2
        assert len(imported_project.criteria) == 2
    
    def test_import_from_csv_missing_info_file(self, project_service, tmp_path):
        """Test import from CSV with missing info file."""
        base_path = tmp_path / "test_project.csv"
        
        with pytest.raises(ServiceError) as exc_info:
            project_service.import_from_csv(str(base_path))
        
        assert "Information file not found" in str(exc_info.value)
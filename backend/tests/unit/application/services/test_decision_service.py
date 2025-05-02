
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from application.services.decision_service import DecisionService
from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType, ScaleType
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result
from application.methods.method_interface import MCDMMethodInterface
from utils.exceptions import ServiceError, ValidationError, MethodError

class TestDecisionService:
    
    @pytest.fixture
    def decision_service(self):
        """Fixture providing a DecisionService instance."""
        return DecisionService()
    
    @pytest.fixture
    def sample_project(self):
        """Fixture providing a sample project with alternatives and criteria."""
        project = Project(name="Test Project")
        
        # Add alternatives
        alternatives = [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
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
        values = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
        project.create_decision_matrix(values=values)
        
        return project
    
    @pytest.fixture
    def mock_method(self):
        """Fixture providing a mock MCDM method."""
        method = Mock(spec=MCDMMethodInterface)
        method.name = "MockMethod"
        result = Result(
            method_name="MockMethod",
            alternative_ids=["alt1", "alt2", "alt3"],
            alternative_names=["Alternative 1", "Alternative 2", "Alternative 3"],
            scores=np.array([0.5, 0.7, 0.3])
        )
        method.execute.return_value = result
        return method
    
    def test_get_available_methods(self, decision_service):
        """Test getting available MCDM methods."""
        with patch('application.services.decision_service.MCDMMethodFactory.get_available_methods',
                  return_value=['TOPSIS', 'AHP', 'ELECTRE', 'PROMETHEE']):
            methods = decision_service.get_available_methods()
            assert len(methods) == 4
            assert 'TOPSIS' in methods
            assert 'AHP' in methods
    
    def test_get_method_info(self, decision_service):
        """Test getting method information."""
        expected_info = {
            'name': 'TOPSIS',
            'full_name': 'Technique for Order of Preference by Similarity to Ideal Solution',
            'description': 'Test description',
            'default_parameters': {}
        }
        
        with patch('application.services.decision_service.MCDMMethodFactory.get_method_info',
                  return_value=expected_info):
            info = decision_service.get_method_info('TOPSIS')
            assert info['name'] == 'TOPSIS'
            assert 'full_name' in info
    
    def test_get_method_info_error(self, decision_service):
        """Test error when getting method info."""
        with patch('application.services.decision_service.MCDMMethodFactory.get_method_info',
                  side_effect=ValidationError("Method not found")):
            with pytest.raises(ServiceError) as exc_info:
                decision_service.get_method_info('NonExistent')
            assert "Error retrieving method information" in str(exc_info.value)
    
    def test_execute_method_success(self, decision_service, sample_project, mock_method):
        """Test successful method execution."""
        with patch('application.services.decision_service.MCDMMethodFactory.create_method_with_params',
                  return_value=mock_method):
            result = decision_service.execute_method(
                sample_project, "MockMethod", {"param": "value"})
            
            assert result.method_name == "MockMethod"
            assert len(result.alternative_ids) == 3
            mock_method.execute.assert_called_once()
    
    def test_execute_method_no_matrix(self, decision_service):
        """Test error when project has no decision matrix."""
        project = Project(name="Empty Project")
        
        with pytest.raises(ServiceError) as exc_info:
            decision_service.execute_method(project, "TOPSIS")
        assert "The project has no decision matrix" in str(exc_info.value)
    
    def test_execute_method_validation_error(self, decision_service, sample_project):
        """Test error when method validation fails."""
        with patch('application.services.decision_service.MCDMMethodFactory.create_method_with_params',
                  side_effect=ValidationError("Invalid parameters")):
            with pytest.raises(ServiceError) as exc_info:
                decision_service.execute_method(sample_project, "TOPSIS", {"invalid": "param"})
            assert "Error executing method TOPSIS" in str(exc_info.value)
    
    def test_execute_all_methods_success(self, decision_service, sample_project, mock_method):
        """Test successful execution of all methods."""
        with patch('application.services.decision_service.MCDMMethodFactory.get_available_methods',
                  return_value=['Method1', 'Method2']):
            with patch('application.services.decision_service.MCDMMethodFactory.create_method_with_params',
                      return_value=mock_method):
                results = decision_service.execute_all_methods(sample_project)
                
                assert len(results) == 2
                assert 'Method1' in results
                assert 'Method2' in results
    
    def test_execute_all_methods_partial_failure(self, decision_service, sample_project, mock_method):
        """Test partial failure when executing multiple methods."""
        def create_method_side_effect(name, params):
            if name == 'TOPSIS':
                return mock_method
            else:
                raise ValidationError("Method not available")
        
        with patch('application.services.decision_service.MCDMMethodFactory.get_available_methods',
                  return_value=['TOPSIS', 'AHP']):
            with patch('application.services.decision_service.MCDMMethodFactory.create_method_with_params',
                      side_effect=create_method_side_effect):
                results = decision_service.execute_all_methods(sample_project)
                
                assert len(results) == 1
                assert 'TOPSIS' in results
                assert 'AHP' not in results
    
    def test_compare_methods_success(self, decision_service, sample_project):
        """Test successful method comparison."""
        # Add results to the project for comparison
        result1 = Result(
            method_name="TOPSIS",
            alternative_ids=["alt1", "alt2", "alt3"],
            alternative_names=["Alternative 1", "Alternative 2", "Alternative 3"],
            scores=np.array([0.7, 0.5, 0.3])
        )
        result2 = Result(
            method_name="AHP",
            alternative_ids=["alt1", "alt2", "alt3"],
            alternative_names=["Alternative 1", "Alternative 2", "Alternative 3"],
            scores=np.array([0.6, 0.5, 0.4])
        )
        
        sample_project.add_result("TOPSIS", result1)
        sample_project.add_result("AHP", result2)
        
        comparison = decision_service.compare_methods(sample_project, ["TOPSIS", "AHP"])
        
        assert 'rankings_correlation' in comparison
        assert 'consensus' in comparison
    
    def test_compare_methods_no_results(self, decision_service, sample_project):
        """Test error when comparing methods with no results."""
        with pytest.raises(ServiceError) as exc_info:
            decision_service.compare_methods(sample_project)
        assert "The project has no MCDM method results" in str(exc_info.value)
    
    def test_perform_sensitivity_analysis_success(self, decision_service, sample_project, mock_method):
        """Test successful sensitivity analysis."""
        with patch('application.services.decision_service.MCDMMethodFactory.create_method',
                  return_value=mock_method):
            sensitivity_results = decision_service.perform_sensitivity_analysis(
                sample_project, "MockMethod", "crit1", (0.1, 1.0), 5)
            
            assert 'method' in sensitivity_results
            assert 'criteria' in sensitivity_results
            assert 'weights_tested' in sensitivity_results
            assert len(sensitivity_results['weights_tested']) == 5
    
    def test_perform_sensitivity_analysis_no_matrix(self, decision_service):
        """Test error in sensitivity analysis when no decision matrix."""
        project = Project(name="Empty Project")
        
        with pytest.raises(ServiceError) as exc_info:
            decision_service.perform_sensitivity_analysis(
                project, "TOPSIS", "crit1", (0.1, 1.0))
        assert "The project has no decision matrix" in str(exc_info.value)
    
    def test_perform_sensitivity_analysis_invalid_criteria(self, decision_service, sample_project):
        """Test error when criteria doesn't exist."""
        with pytest.raises(ServiceError) as exc_info:
            decision_service.perform_sensitivity_analysis(
                sample_project, "TOPSIS", "invalid_criteria", (0.1, 1.0))
        assert "Criterion with ID: invalid_criteria not found" in str(exc_info.value)
    
    def test_create_project(self, decision_service):
        """Test project creation."""
        project = decision_service.create_project(
            "Test Project", "Description", "John Doe")
        
        assert project.name == "Test Project"
        assert project.description == "Description"
        assert project.decision_maker == "John Doe"
    
    def test_add_alternative(self, decision_service):
        """Test adding alternative to project."""
        # Create a fresh project for this test
        project = Project(name="Test Project")
        
        alt = decision_service.add_alternative(
            project, "alt1", "Alternative 1", "Test description")
        
        assert alt.id == "alt1"
        assert alt.name == "Alternative 1"
        assert len(project.alternatives) == 1
    
    def test_add_alternative_duplicate_id(self, decision_service, sample_project):
        """Test error when adding alternative with duplicate ID."""
        with pytest.raises(ServiceError) as exc_info:
            decision_service.add_alternative(sample_project, "alt1", "Duplicate")
        assert "Error adding alternative" in str(exc_info.value)
    
    def test_add_criteria(self, decision_service):
        """Test adding criteria to project."""
        # Create a fresh project for this test
        project = Project(name="Test Project")
        
        crit = decision_service.add_criteria(
            project, "crit1", "Criteria 1", "", "maximize", 
            "quantitative", 0.5, "units", {"key": "value"})
        
        assert crit.id == "crit1"
        assert crit.name == "Criteria 1"
        assert len(project.criteria) == 1
    
    def test_create_decision_matrix(self, decision_service):
        """Test creating decision matrix."""
        # Create a new project without matrix
        project = Project(name="Test Project")
        project.add_alternative(Alternative(id="alt1", name="Alternative 1"))
        project.add_criteria(Criteria(id="crit1", name="Criteria 1"))
        
        matrix = decision_service.create_decision_matrix(project, "Test Matrix")
        assert matrix.name == "Test Matrix"
        assert matrix.shape == (1, 1)
    
    def test_set_matrix_value(self, decision_service, sample_project):
        """Test setting value in decision matrix."""
        decision_service.set_matrix_value(sample_project, "alt1", "crit1", 10.0)
        matrix = sample_project.decision_matrix
        # Corregir el nombre del método aquí
        assert matrix.get_values(0, 0) == 10.0
    
    def test_set_matrix_value_no_matrix(self, decision_service):
        """Test error when setting value with no matrix."""
        project = Project(name="Empty Project")
        
        with pytest.raises(ServiceError) as exc_info:
            decision_service.set_matrix_value(project, "alt1", "crit1", 10.0)
        assert "The project has no decision matrix" in str(exc_info.value)
    
    def test_calculate_ranking_correlation(self, decision_service, sample_project):
        """Test internal method for calculating ranking correlation."""
        # Create two results with different rankings
        result1 = Result(
            method_name="Method1",
            alternative_ids=["alt1", "alt2", "alt3"],
            alternative_names=["Alt 1", "Alt 2", "Alt 3"],
            scores=np.array([0.7, 0.5, 0.3])
        )
        result2 = Result(
            method_name="Method2",
            alternative_ids=["alt1", "alt2", "alt3"],
            alternative_names=["Alt 1", "Alt 2", "Alt 3"],
            scores=np.array([0.6, 0.5, 0.4])
        )
        
        sample_project.add_result("Method1", result1)
        sample_project.add_result("Method2", result2)
        
        correlation = decision_service._calculate_ranking_correlation(
            sample_project, ["Method1", "Method2"])
        
        assert 'Method1' in correlation
        assert 'Method2' in correlation
        assert correlation['Method1']['Method1'] == 1.0
        assert 'Method2' in correlation['Method1']
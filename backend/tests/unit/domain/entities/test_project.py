# backend/tests/unit/domain/entities/test_project.py

import pytest
import numpy as np
from datetime import datetime
from uuid import UUID
from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result

class TestProject:
    
    @pytest.fixture
    def sample_alternatives(self):
        """Fixture providing sample alternatives for tests."""
        return [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
        ]
    
    @pytest.fixture
    def sample_criteria(self):
        """Fixture providing sample criteria for tests."""
        return [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE),
            Criteria(id="crit3", name="Criteria 3", optimization_type=OptimizationType.MAXIMIZE)
        ]
    
    @pytest.fixture
    def sample_result(self, sample_alternatives):
        """Fixture providing a sample result for tests."""
        return Result(
            method_name="TOPSIS",
            alternative_ids=[alt.id for alt in sample_alternatives],
            alternative_names=[alt.name for alt in sample_alternatives],
            scores=np.array([0.7, 0.5, 0.9])
        )
    
    def test_project_creation(self):
        """Test basic creation of a Project instance."""
        project = Project(
            name="Test Project",
            description="Test Description",
            decision_maker="Test User"
        )
        
        assert project.name == "Test Project"
        assert project.description == "Test Description"
        assert project.decision_maker == "Test User"
        assert isinstance(project.id, str)
        assert isinstance(datetime.fromisoformat(project.created_at.isoformat()), datetime)
        assert isinstance(datetime.fromisoformat(project.updated_at.isoformat()), datetime)
    
    def test_project_creation_with_id(self):
        """Test project creation with custom ID."""
        custom_id = "550e8400-e29b-41d4-a716-446655440000"
        project = Project(
            name="Test Project",
            project_id=custom_id
        )
        
        assert project.id == custom_id
    
    def test_project_default_values(self):
        """Test project creation with default values."""
        project = Project(name="Test Project")
        
        assert project.description == ""
        assert project.decision_maker == ""
        assert project.alternatives == []
        assert project.criteria == []
        assert project.decision_matrix is None
        assert project.results == {}
        assert project.metadata == {}
    
    def test_property_setters(self):
        """Test property setters update correctly."""
        project = Project(name="Initial Name")
        initial_updated_at = project.updated_at
        
        project.name = "New Name"
        assert project.name == "New Name"
        assert project.updated_at > initial_updated_at
        
        project.description = "New Description"
        assert project.description == "New Description"
        
        project.decision_maker = "New User"
        assert project.decision_maker == "New User"
    
    def test_add_alternative(self, sample_alternatives):
        """Test adding alternatives to the project."""
        project = Project(name="Test Project")
        
        project.add_alternative(sample_alternatives[0])
        assert len(project.alternatives) == 1
        assert project.alternatives[0].id == "alt1"
    
    def test_add_duplicate_alternative(self, sample_alternatives):
        """Test error when adding duplicate alternative."""
        project = Project(name="Test Project")
        
        project.add_alternative(sample_alternatives[0])
        
        with pytest.raises(ValueError, match="Already exist an alternative with ID: alt1"):
            project.add_alternative(sample_alternatives[0])
    
    def test_add_criteria(self, sample_criteria):
        """Test adding criteria to the project."""
        project = Project(name="Test Project")
        
        project.add_criteria(sample_criteria[0])
        assert len(project.criteria) == 1
        assert project.criteria[0].id == "crit1"
    
    def test_add_duplicate_criteria(self, sample_criteria):
        """Test error when adding duplicate criteria."""
        project = Project(name="Test Project")
        
        project.add_criteria(sample_criteria[0])
        
        with pytest.raises(ValueError, match="Already exist a criteria with ID: crit1"):
            project.add_criteria(sample_criteria[0])
    
    def test_remove_alternative(self, sample_alternatives):
        """Test removing alternative from the project."""
        project = Project(name="Test Project")
        project.add_alternative(sample_alternatives[0])
        project.add_alternative(sample_alternatives[1])
        
        project.remove_alternative("alt1")
        
        assert len(project.alternatives) == 1
        assert project.alternatives[0].id == "alt2"
    
    def test_remove_nonexistent_alternative(self):
        """Test error when removing nonexistent alternative."""
        project = Project(name="Test Project")
        
        with pytest.raises(ValueError, match="No alternative were found with the ID: nonexistent"):
            project.remove_alternative("nonexistent")
    
    def test_remove_criteria(self, sample_criteria):
        """Test removing criteria from the project."""
        project = Project(name="Test Project")
        project.add_criteria(sample_criteria[0])
        project.add_criteria(sample_criteria[1])
        
        project.remove_criteria("crit1")
        
        assert len(project.criteria) == 1
        assert project.criteria[0].id == "crit2"
    
    def test_remove_nonexistent_criteria(self):
        """Test error when removing nonexistent criteria."""
        project = Project(name="Test Project")
        
        with pytest.raises(ValueError, match="No criteria were found with the ID: nonexistent"):
            project.remove_criteria("nonexistent")
    
    def test_get_alternative_by_id(self, sample_alternatives):
        """Test getting alternative by ID."""
        project = Project(name="Test Project")
        project.add_alternative(sample_alternatives[0])
        
        alternative = project.get_alternative_by_id("alt1")
        assert alternative.id == "alt1"
        assert alternative.name == "Alternative 1"
    
    def test_get_criteria_by_id(self, sample_criteria):
        """Test getting criteria by ID."""
        project = Project(name="Test Project")
        project.add_criteria(sample_criteria[0])
        
        criteria = project.get_criteria_by_id("crit1")
        assert criteria.id == "crit1"
        assert criteria.name == "Criteria 1"
    
    def test_create_decision_matrix(self, sample_alternatives, sample_criteria):
        """Test creating decision matrix."""
        project = Project(name="Test Project")
        for alt in sample_alternatives:
            project.add_alternative(alt)
        for crit in sample_criteria:
            project.add_criteria(crit)
        
        matrix = project.create_decision_matrix()
        assert matrix is not None
        assert matrix.name == "Matriz de Test Project"
        assert len(matrix.alternative) == 3
        assert len(matrix.criteria) == 3
    
    def test_create_decision_matrix_no_alternatives(self, sample_criteria):
        """Test error when creating matrix without alternatives."""
        project = Project(name="Test Project")
        for crit in sample_criteria:
            project.add_criteria(crit)
        
        with pytest.raises(ValueError, match="There are no alternatives defined in the project"):
            project.create_decision_matrix()
    
    def test_create_decision_matrix_no_criteria(self, sample_alternatives):
        """Test error when creating matrix without criteria."""
        project = Project(name="Test Project")
        for alt in sample_alternatives:
            project.add_alternative(alt)
        
        with pytest.raises(ValueError, match="There are no criterian defined in the project"):
            project.create_decision_matrix()
    
    def test_add_result(self, sample_result):
        """Test adding result to project."""
        project = Project(name="Test Project")
        
        project.add_result("TOPSIS", sample_result)
        assert "TOPSIS" in project.results
        assert project.results["TOPSIS"] == sample_result
    
    def test_get_result(self, sample_result):
        """Test getting result from project."""
        project = Project(name="Test Project")
        project.add_result("TOPSIS", sample_result)
        
        result = project.get_result("TOPSIS")
        assert result == sample_result
    
    def test_remove_result(self, sample_result):
        """Test removing result from project."""
        project = Project(name="Test Project")
        project.add_result("TOPSIS", sample_result)
        
        project.remove_result("TOPSIS")
        assert "TOPSIS" not in project.results
    
    def test_remove_nonexistent_result(self):
        """Test error when removing nonexistent result."""
        project = Project(name="Test Project")
        
        with pytest.raises(KeyError, match="There is no result for the method: TOPSIS"):
            project.remove_result("TOPSIS")
    
    def test_get_available_methods(self, sample_result):
        """Test getting available methods."""
        project = Project(name="Test Project")
        project.add_result("TOPSIS", sample_result)
        project.add_result("AHP", sample_result)
        
        methods = project.get_available_methods()
        assert len(methods) == 2
        assert "TOPSIS" in methods
        assert "AHP" in methods
    
    def test_get_best_alternative(self, sample_alternatives, sample_result):
        """Test getting best alternative for a method."""
        project = Project(name="Test Project")
        project.add_result("TOPSIS", sample_result)
        
        best_id, best_name, best_score = project.get_best_alternative("TOPSIS")
        assert best_id == "alt3"
        assert best_name == "Alternative 3"
        assert best_score == 0.9
    
    def test_get_best_alternative_no_method(self):
        """Test error when getting best alternative for nonexistent method."""
        project = Project(name="Test Project")
        
        with pytest.raises(KeyError, match="There is no result for the method: TOPSIS"):
            project.get_best_alternative("TOPSIS")
    
    def test_to_dict(self, sample_alternatives, sample_criteria, sample_result):
        """Test conversion to dictionary."""
        project = Project(name="Test Project", description="Test Description")
        project.add_alternative(sample_alternatives[0])
        project.add_criteria(sample_criteria[0])
        project.add_result("TOPSIS", sample_result)
        
        project_dict = project.to_dict()
        
        assert project_dict['name'] == "Test Project"
        assert project_dict['description'] == "Test Description"
        assert 'id' in project_dict
        assert 'created_at' in project_dict
        assert len(project_dict['alternatives']) == 1
        assert len(project_dict['criteria']) == 1
        assert 'TOPSIS' in project_dict['results']
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'id': '550e8400-e29b-41d4-a716-446655440000',
            'name': 'Test Project',
            'description': 'Test Description',
            'decision_maker': 'Test User',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'alternatives': [{'id': 'alt1', 'name': 'Alternative 1', 'description': '', 'metadata': {}}],
            'criteria': [{'id': 'crit1', 'name': 'Criteria 1', 'description': '', 
                         'optimization_type': 'maximize', 'scale_type': 'quantitative', 
                         'weight': 1.0, 'unit': '', 'metadata': {}}],
            'metadata': {'key': 'value'},
            'results': {}
        }
        
        project = Project.from_dict(data)
        
        assert project.id == '550e8400-e29b-41d4-a716-446655440000'
        assert project.name == 'Test Project'
        assert project.description == 'Test Description'
        assert len(project.alternatives) == 1
        assert len(project.criteria) == 1
        assert project.metadata == {'key': 'value'}
    
    def test_str_representation(self, sample_alternatives, sample_criteria):
        """Test string representation of project."""
        project = Project(name="Test Project")
        for alt in sample_alternatives:
            project.add_alternative(alt)
        for crit in sample_criteria:
            project.add_criteria(crit)
        
        str_repr = str(project)
        assert "MCDM Porject: Test Project" in str_repr
        assert "3 alternatives" in str_repr
        assert "3 criterian" in str_repr
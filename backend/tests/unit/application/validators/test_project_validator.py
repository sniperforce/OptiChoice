# backend/tests/unit/application/validators/test_project_validator.py

import pytest
import numpy as np
from uuid import uuid4
from application.validators.project_validator import ProjectValidator
from domain.entities.project import Project
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix
from domain.entities.result import Result

class TestProjectValidator:
    
    @pytest.fixture
    def sample_alternatives(self):
        """Fixture providing sample alternatives for testing."""
        return [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
        ]
    
    @pytest.fixture
    def sample_criteria(self):
        """Fixture providing sample criteria for testing."""
        return [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE, weight=0.4),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE, weight=0.3),
            Criteria(id="crit3", name="Criteria 3", optimization_type=OptimizationType.MAXIMIZE, weight=0.3)
        ]
    
    @pytest.fixture
    def sample_decision_matrix(self, sample_alternatives, sample_criteria):
        """Fixture providing a sample decision matrix."""
        values = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ])
        return DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=values
        )
    
    @pytest.fixture
    def sample_result(self, sample_alternatives):
        """Fixture providing a sample result."""
        return Result(
            method_name="TOPSIS",
            alternative_ids=[alt.id for alt in sample_alternatives],
            alternative_names=[alt.name for alt in sample_alternatives],
            scores=np.array([0.7, 0.5, 0.9])
        )
    
    def test_validate_id_valid_uuid(self):
        """Test validation of a valid UUID for project ID."""
        valid_uuid = str(uuid4())
        valid, error = ProjectValidator.validate_id(valid_uuid)
        assert valid == True
        assert error is None
    
    def test_validate_id_empty(self):
        """Test validation of an empty project ID."""
        valid, error = ProjectValidator.validate_id("")
        assert valid == False
        assert error == "Project ID cannot be empty"
    
    def test_validate_id_non_string(self):
        """Test validation of a non-string project ID."""
        valid, error = ProjectValidator.validate_id(123)
        assert valid == False
        assert error == "ID must be a string"
    
    def test_validate_id_invalid_uuid(self):
        """Test validation of an invalid UUID string."""
        valid, error = ProjectValidator.validate_id("not-a-valid-uuid")
        assert valid == False
        assert error == "Project ID must be a valid UUID"
    
    def test_validate_name_valid(self):
        """Test validation of a valid project name."""
        valid, error = ProjectValidator.validate_name("Test Project")
        assert valid == True
        assert error is None
    
    def test_validate_name_empty(self):
        """Test validation of an empty project name."""
        valid, error = ProjectValidator.validate_name("")
        assert valid == False
        assert error == "Project name cannot be empty"
    
    def test_validate_name_non_string(self):
        """Test validation of a non-string project name."""
        valid, error = ProjectValidator.validate_name(123)
        assert valid == False
        assert error == "Name must be a string"
    
    def test_validate_description_valid(self):
        """Test validation of a valid description."""
        valid, error = ProjectValidator.validate_description("Valid description")
        assert valid == True
        assert error is None
    
    def test_validate_description_empty(self):
        """Test validation of an empty description."""
        valid, error = ProjectValidator.validate_description("")
        assert valid == True
        assert error is None
    
    def test_validate_description_non_string(self):
        """Test validation of a non-string description."""
        valid, error = ProjectValidator.validate_description(123)
        assert valid == False
        assert error == "Description must be a string"
    
    def test_validate_decision_maker_valid(self):
        """Test validation of a valid decision maker."""
        valid, error = ProjectValidator.validate_decision_maker("John Doe")
        assert valid == True
        assert error is None
    
    def test_validate_decision_maker_empty(self):
        """Test validation of an empty decision maker."""
        valid, error = ProjectValidator.validate_decision_maker("")
        assert valid == True
        assert error is None
    
    def test_validate_decision_maker_none(self):
        """Test validation of None decision maker."""
        valid, error = ProjectValidator.validate_decision_maker(None)
        assert valid == False
        assert error == "Decision maker cannot be None"
    
    def test_validate_decision_maker_non_string(self):
        """Test validation of a non-string decision maker."""
        valid, error = ProjectValidator.validate_decision_maker(123)
        assert valid == False
        assert error == "Decision maker must be a string"
    
    def test_validate_alternatives_valid(self, sample_alternatives):
        """Test validation of valid alternatives."""
        valid, errors = ProjectValidator.validate_alternatives(sample_alternatives)
        assert valid == True
        assert errors == []
    
    def test_validate_alternatives_empty(self):
        """Test validation of empty alternatives list."""
        valid, errors = ProjectValidator.validate_alternatives([])
        assert valid == False
        assert "Alternatives list cannot be empty" in errors
    
    def test_validate_alternatives_non_list(self):
        """Test validation of non-list alternatives."""
        valid, errors = ProjectValidator.validate_alternatives("not a list")
        assert valid == False
        assert "Alternatives must be in a list" in errors
    
    def test_validate_alternatives_invalid_type(self):
        """Test validation of alternatives with invalid type elements."""
        invalid_alternatives = ["not an alternative", Alternative(id="alt1", name="Valid")]
        valid, errors = ProjectValidator.validate_alternatives(invalid_alternatives)
        assert valid == False
        assert "All elements must be instances of Alternative" in errors
    
    def test_validate_alternatives_duplicate_ids(self, sample_alternatives):
        """Test validation of alternatives with duplicate IDs."""
        duplicate_alternatives = sample_alternatives + [Alternative(id="alt1", name="Duplicate")]
        valid, errors = ProjectValidator.validate_alternatives(duplicate_alternatives)
        assert valid == False
        assert "There are alternatives with duplicate IDs" in errors
    
    def test_validate_criteria_valid(self, sample_criteria):
        """Test validation of valid criteria."""
        valid, errors = ProjectValidator.validate_criteria(sample_criteria)
        assert valid == True
        assert errors == []
    
    def test_validate_criteria_empty(self):
        """Test validation of empty criteria list."""
        valid, errors = ProjectValidator.validate_criteria([])
        assert valid == False
        assert "Criteria list cannot be empty" in errors
    
    def test_validate_criteria_non_list(self):
        """Test validation of non-list criteria."""
        valid, errors = ProjectValidator.validate_criteria("not a list")
        assert valid == False
        assert "Criteria must be in a list" in errors
    
    def test_validate_criteria_negative_weight_sum(self):
        """Test validation of criteria with negative weight sum."""
        criteria = [
            Criteria(id="crit1", name="Criteria 1", weight=0),
            Criteria(id="crit2", name="Criteria 2", weight=0)
        ]
        valid, errors = ProjectValidator.validate_criteria(criteria)
        assert valid == False
        assert "The sum of criteria weights must be greater than zero" in errors
    
    def test_validate_decision_matrix_valid(self, sample_decision_matrix, sample_alternatives, sample_criteria):
        """Test validation of a valid decision matrix."""
        valid, errors = ProjectValidator.validate_decision_matrix(
            sample_decision_matrix, sample_alternatives, sample_criteria
        )
        assert valid == True
        assert errors == []
    
    def test_validate_decision_matrix_none(self, sample_alternatives, sample_criteria):
        """Test validation when decision matrix is None."""
        valid, errors = ProjectValidator.validate_decision_matrix(
            None, sample_alternatives, sample_criteria
        )
        assert valid == True
        assert errors == []
    
    def test_validate_decision_matrix_invalid_type(self, sample_alternatives, sample_criteria):
        """Test validation of decision matrix with invalid type."""
        valid, errors = ProjectValidator.validate_decision_matrix(
            "not a matrix", sample_alternatives, sample_criteria
        )
        assert valid == False
        assert "Decision matrix must be an instance of DecisionMatrix" in errors
    
    def test_validate_decision_matrix_undefined_alternatives(self, sample_alternatives, sample_criteria):
        """Test validation when matrix contains undefined alternatives."""
        undefined_alternatives = [Alternative(id="undefined", name="Undefined")]
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=undefined_alternatives,
            criteria=sample_criteria,
            values=np.zeros((1, 3))
        )
        valid, errors = ProjectValidator.validate_decision_matrix(
            matrix, sample_alternatives, sample_criteria
        )
        assert valid == False
        assert "The matrix contains alternatives not defined in the project" in errors[0]
    
    def test_validate_results_valid(self, sample_result, sample_alternatives):
        """Test validation of valid results."""
        results = {"TOPSIS": sample_result}
        valid, errors = ProjectValidator.validate_results(results, sample_alternatives)
        assert valid == True
        assert errors == []
    
    def test_validate_results_non_dict(self, sample_alternatives):
        """Test validation of non-dictionary results."""
        valid, errors = ProjectValidator.validate_results("not a dict", sample_alternatives)
        assert valid == False
        assert "Results must be in a dictionary" in errors
    
    def test_validate_results_invalid_method_name(self, sample_result, sample_alternatives):
        """Test validation of results with invalid method name."""
        results = {123: sample_result}
        valid, errors = ProjectValidator.validate_results(results, sample_alternatives)
        assert valid == False
        assert "Method name '123' must be a string" in errors
    
    def test_validate_results_invalid_result_type(self, sample_alternatives):
        """Test validation of results with invalid result type."""
        results = {"TOPSIS": "not a result"}
        valid, errors = ProjectValidator.validate_results(results, sample_alternatives)
        assert valid == False
        assert "Result for method 'TOPSIS' must be an instance of Result" in errors
    
    def test_validate_metadata_valid(self):
        """Test validation of valid metadata."""
        valid, error = ProjectValidator.validate_metadata({"key": "value"})
        assert valid == True
        assert error is None
    
    def test_validate_metadata_empty(self):
        """Test validation of empty metadata."""
        valid, error = ProjectValidator.validate_metadata({})
        assert valid == True
        assert error is None
    
    def test_validate_metadata_none(self):
        """Test validation of None metadata."""
        valid, error = ProjectValidator.validate_metadata(None)
        assert valid == False
        assert error == "Metadata cannot be None"
    
    def test_validate_metadata_non_dict(self):
        """Test validation of non-dictionary metadata."""
        valid, error = ProjectValidator.validate_metadata("not a dict")
        assert valid == False
        assert error == "Metadata must be a dictionary"
    
    def test_validate_project_data_all_valid(self, sample_alternatives, sample_criteria, sample_decision_matrix, sample_result):
        """Test validation of all valid project data."""
        project_id = str(uuid4())
        results = {"TOPSIS": sample_result}
        
        valid, errors = ProjectValidator.validate_project_data(
            project_id=project_id,
            name="Test Project",
            description="Test Description",
            decision_maker="John Doe",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            decision_matrix=sample_decision_matrix,
            results=results,
            metadata={"key": "value"}
        )
        assert valid == True
        assert errors == []
    
    def test_validate_project_data_multiple_errors(self):
        """Test validation with multiple errors."""
        valid, errors = ProjectValidator.validate_project_data(
            project_id="invalid-uuid",
            name="",
            description=123,
            decision_maker=None,
            alternatives="not a list",
            criteria="not a list",
            decision_matrix="not a matrix",
            results="not a dict",
            metadata="not a dict"
        )
        assert valid == False
        assert len(errors) >= 7
    
    def test_validate_from_dict_valid(self):
        """Test validation from a valid dictionary."""
        data = {
            'id': str(uuid4()),
            'name': 'Test Project',
            'description': 'Test Description',
            'decision_maker': 'John Doe',
            'alternatives': [],
            'criteria': [],
            'results': {},
            'metadata': {}
        }
        valid, errors = ProjectValidator.validate_from_dict(data)
        assert valid == True
        assert errors == []
    
    def test_validate_from_dict_missing_required(self):
        """Test validation from dictionary missing required fields."""
        data = {
            'description': 'Only description'
        }
        valid, errors = ProjectValidator.validate_from_dict(data)
        assert valid == False
        assert "Field 'id' is required" in errors
        assert "Field 'name' is required" in errors
    
    def test_validate_project_valid(self, sample_alternatives, sample_criteria):
        """Test validation of a valid project instance."""
        project = Project(name="Test Project")
        for alt in sample_alternatives:
            project.add_alternative(alt)
        for crit in sample_criteria:
            project.add_criteria(crit)
            
        valid, errors = ProjectValidator.validate_project(project)
        assert valid == True
        assert errors == []
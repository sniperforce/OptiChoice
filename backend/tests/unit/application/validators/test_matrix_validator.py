import pytest
import numpy as np
from application.validators.matrix_validator import MatrixValidator
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType
from domain.entities.decision_matrix import DecisionMatrix

class TestMatrixValidator:
    
    @pytest.fixture
    def sample_alternatives(self):
        """Fixture that provides sample alternatives for testing."""
        return [
            Alternative(id="alt1", name="Alternative 1"),
            Alternative(id="alt2", name="Alternative 2"),
            Alternative(id="alt3", name="Alternative 3")
        ]
    
    @pytest.fixture
    def sample_criteria(self):
        """Fixture that provides sample criteria for testing."""
        return [
            Criteria(id="crit1", name="Criteria 1", optimization_type=OptimizationType.MAXIMIZE),
            Criteria(id="crit2", name="Criteria 2", optimization_type=OptimizationType.MINIMIZE),
            Criteria(id="crit3", name="Criteria 3", optimization_type=OptimizationType.MAXIMIZE)
        ]
    
    @pytest.fixture
    def sample_values(self):
        """Fixture that provides sample matrix values."""
        return np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ])
    
    def test_validate_name_valid(self):
        """Test validation of a valid matrix name."""
        valid, error = MatrixValidator.validate_name("Test Matrix")
        assert valid == True
        assert error is None
    
    def test_validate_name_empty(self):
        """Test validation of an empty matrix name."""
        valid, error = MatrixValidator.validate_name("")
        assert valid == False
        assert error == "The name of the matrix cannot be empty"
    
    def test_validate_name_non_string(self):
        """Test validation of a non-string matrix name."""
        valid, error = MatrixValidator.validate_name(123)
        assert valid == False
        assert error == "The name must be a text string"
    
    def test_validate_alternatives_valid(self, sample_alternatives):
        """Test validation of valid alternatives."""
        valid, error = MatrixValidator.validate_alternatives(sample_alternatives)
        assert valid == True
        assert error is None
    
    def test_validate_alternatives_empty(self):
        """Test validation of empty alternatives list."""
        valid, error = MatrixValidator.validate_alternatives([])
        assert valid == False
        assert error == "The matrix must contains at least one alternative"
    
    def test_validate_alternatives_non_list(self):
        """Test validation of non-list alternatives."""
        valid, error = MatrixValidator.validate_alternatives("not a list")
        assert valid == False
        assert error == "The alternatives must be in a list"
    
    def test_validate_alternatives_invalid_type(self):
        """Test validation of alternatives with invalid type elements."""
        invalid_alternatives = ["not an alternative", Alternative(id="alt1", name="Valid")]
        valid, error = MatrixValidator.validate_alternatives(invalid_alternatives)
        assert valid == False
        assert error == "All the elements must be instance of Alternative"
    
    def test_validate_alternatives_duplicate_ids(self, sample_alternatives):
        """Test validation of alternatives with duplicate IDs."""
        duplicate_alternatives = sample_alternatives + [Alternative(id="alt1", name="Duplicate")]
        valid, error = MatrixValidator.validate_alternatives(duplicate_alternatives)
        assert valid == False
        assert error == "Exist alternatives with duplicated ID's"
    
    def test_validate_criteria_valid(self, sample_criteria):
        """Test validation of valid criteria."""
        valid, error = MatrixValidator.validate_criteria(sample_criteria)
        assert valid == True
        assert error is None
    
    def test_validate_criteria_empty(self):
        """Test validation of empty criteria list."""
        valid, error = MatrixValidator.validate_criteria([])
        assert valid == False
        assert error == "The matrix must contains at least one criteria"
    
    def test_validate_criteria_non_list(self):
        """Test validation of non-list criteria."""
        valid, error = MatrixValidator.validate_criteria("not a list")
        assert valid == False
        assert error == "The criterian must be in a list"
    
    def test_validate_criteria_invalid_type(self):
        """Test validation of criteria with invalid type elements."""
        invalid_criteria = ["not a criteria", Criteria(id="crit1", name="Valid")]
        valid, error = MatrixValidator.validate_criteria(invalid_criteria)
        assert valid == False
        assert error == "All the elements must be instance of Criteria"
    
    def test_validate_criteria_duplicate_ids(self, sample_criteria):
        """Test validation of criteria with duplicate IDs."""
        duplicate_criteria = sample_criteria + [Criteria(id="crit1", name="Duplicate")]
        valid, error = MatrixValidator.validate_criteria(duplicate_criteria)
        assert valid == False
        assert error == "Exist criterian with duplicated ID's"
    
    def test_validate_values_valid(self, sample_values):
        """Test validation of valid matrix values."""
        valid, error = MatrixValidator.validate_values(sample_values, 3, 3)
        assert valid == True
        assert error is None
    
    def test_validate_values_non_numpy(self):
        """Test validation of non-numpy array values."""
        values_list = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        valid, error = MatrixValidator.validate_values(values_list, 3, 3)
        assert valid == False
        assert error == "The values must be a Numpy Matrix"
    
    def test_validate_values_wrong_dimensions(self, sample_values):
        """Test validation of values with incorrect dimensions."""
        valid, error = MatrixValidator.validate_values(sample_values, 4, 3)
        assert valid == False
        assert "The dimensions of the matrix" in error
    
    def test_validate_values_non_numeric(self):
        """Test validation of values with non-numeric elements."""
        values = np.array([['a', 'b', 'c'], [1, 2, 3]])
        valid, error = MatrixValidator.validate_values(values, 2, 3)
        assert valid == False
        assert error == "All the values of the matrix must be numerical"
    
    def test_validate_values_nan_infinite(self):
        """Test validation of values with NaN or infinite values."""
        values = np.array([[1, 2, np.nan], [4, np.inf, 6], [7, 8, 9]])
        valid, error = MatrixValidator.validate_values(values, 3, 3)
        assert valid == False
        assert error == "The matrix contains not valid values (NaN or Infinite)"
    
    def test_validate_matrix_data_all_valid(self, sample_alternatives, sample_criteria, sample_values):
        """Test validation of all valid matrix data."""
        valid, errors = MatrixValidator.validate_matrix_data(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        assert valid == True
        assert errors == []
    
    def test_validate_matrix_data_multiple_errors(self):
        """Test validation with multiple errors."""
        valid, errors = MatrixValidator.validate_matrix_data(
            name="",
            alternatives=[],
            criteria="not a list",
            values=None
        )
        assert valid == False
        assert len(errors) >= 3
    
    def test_validate_from_dict_valid(self, sample_alternatives, sample_criteria, sample_values):
        """Test validation from a valid dictionary."""
        data = {
            'name': 'Test Matrix',
            'alternatives': [alt.to_dict() for alt in sample_alternatives],
            'criteria': [crit.to_dict() for crit in sample_criteria],
            'values': sample_values.tolist()
        }
        valid, errors = MatrixValidator.validate_from_dict(data)
        assert valid == True
        assert errors == []
    
    def test_validate_from_dict_missing_required(self):
        """Test validation from dictionary missing required fields."""
        data = {
            'name': 'Test Matrix'
        }
        valid, errors = MatrixValidator.validate_from_dict(data)
        assert valid == False
        assert len(errors) == 3  # Missing alternatives, criteria, and values
    
    def test_validate_from_dict_invalid_types(self):
        """Test validation from dictionary with invalid field types."""
        data = {
            'name': 'Test Matrix',
            'alternatives': "not a list",
            'criteria': {},
            'values': "not a list"
        }
        valid, errors = MatrixValidator.validate_from_dict(data)
        assert valid == False
        assert len(errors) >= 3
    
    def test_validate_consistency_valid(self, sample_alternatives, sample_criteria, sample_values):
        """Test consistency validation of a valid matrix."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        valid, errors = MatrixValidator.validate_consistency(matrix)
        assert valid == True
        assert errors == []
    
    def test_validate_consistency_wrong_dimensions(self, sample_alternatives, sample_criteria):
        """Test consistency validation with wrong dimensions."""
        wrong_values = np.zeros((4, 4))  # Wrong dimensions
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=wrong_values
        )
        valid, errors = MatrixValidator.validate_consistency(matrix)
        assert valid == False
        assert len(errors) == 1
        assert "The dimensions of the matrix" in errors[0]
    
    def test_validate_consistency_invalid_values(self, sample_alternatives, sample_criteria):
        """Test consistency validation with invalid values."""
        invalid_values = np.array([
            [1, 2, np.nan],
            [4, np.inf, 6],
            [7, 8, 9]
        ])
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=invalid_values
        )
        valid, errors = MatrixValidator.validate_consistency(matrix)
        assert valid == False
        assert len(errors) == 1
        assert "The matrix contains unvalid values (NaN or infinite)" in errors[0]
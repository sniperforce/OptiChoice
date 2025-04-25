import pytest
import numpy as np
from domain.entities.alternative import Alternative
from domain.entities.criteria import Criteria, OptimizationType, ScaleType
from domain.entities.decision_matrix import DecisionMatrix

class TestDecisionMatrix:
    
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
    def sample_values(self):
        """Fixture providing sample matrix values."""
        return np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ])
    
    def test_matrix_creation(self, sample_alternatives, sample_criteria, sample_values):
        """Test basic creation of a DecisionMatrix instance."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        assert matrix.name == "Test Matrix"
        assert len(matrix.alternative) == 3
        assert len(matrix.criteria) == 3
        assert matrix.shape == (3, 3)
    
    def test_matrix_creation_default_values(self, sample_alternatives, sample_criteria):
        """Test matrix creation with default zero values."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria
        )
        
        assert matrix.values.shape == (3, 3)
        assert np.array_equal(matrix.values, np.zeros((3, 3)))
    
    def test_matrix_creation_from_list(self, sample_alternatives, sample_criteria):
        """Test matrix creation from a list of lists."""
        values_list = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=values_list
        )
        
        assert matrix.values.shape == (3, 3)
        assert np.array_equal(matrix.values, np.array(values_list))
    
    def test_name_setter(self, sample_alternatives, sample_criteria):
        """Test the setter for name property."""
        matrix = DecisionMatrix(
            name="Initial Name",
            alternatives=sample_alternatives,
            criteria=sample_criteria
        )
        matrix.name = "New Name"
        assert matrix.name == "New Name"
    
    def test_values_immutability(self, sample_alternatives, sample_criteria, sample_values):
        """Test that the values getter returns a copy."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        values_copy = matrix.values
        values_copy[0, 0] = 999
        
        assert matrix.values[0, 0] == 1.0
        assert values_copy[0, 0] == 999
    
    def test_get_values(self, sample_alternatives, sample_criteria, sample_values):
        """Test the get_values method."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        assert matrix.get_values(0, 0) == 1.0
        assert matrix.get_values(1, 1) == 5.0
        assert matrix.get_values(2, 2) == 9.0
    
    def test_set_values(self, sample_alternatives, sample_criteria, sample_values):
        """Test the set_values method."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        matrix.set_values(0, 0, 100.0)
        assert matrix.get_values(0, 0) == 100.0
    
    def test_get_alternative_values(self, sample_alternatives, sample_criteria, sample_values):
        """Test getting values for a specific alternative."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        alt_values = matrix.get_alternative_values(0)
        assert np.array_equal(alt_values, np.array([1.0, 2.0, 3.0]))
    
    def test_get_criteria_values(self, sample_alternatives, sample_criteria, sample_values):
        """Test getting values for a specific criterion."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        crit_values = matrix.get_criteria_values(0)
        assert np.array_equal(crit_values, np.array([1.0, 4.0, 7.0]))
    
    def test_get_alternative_by_id(self, sample_alternatives, sample_criteria):
        """Test getting alternative by ID."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria
        )
        
        idx, alternative = matrix.get_alternative_by_id("alt2")
        assert idx == 1
        assert alternative.id == "alt2"
        assert alternative.name == "Alternative 2"
    
    def test_get_alternative_by_id_not_found(self, sample_alternatives, sample_criteria):
        """Test error when alternative ID is not found."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria
        )
        
        with pytest.raises(ValueError, match="Dont find any alternative with ID: nonexistent"):
            matrix.get_alternative_by_id("nonexistent")
    
    def test_get_criteria_by_id(self, sample_alternatives, sample_criteria):
        """Test getting criterion by ID."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria
        )
        
        idx, criterion = matrix.get_criteria_by_id("crit2")
        assert idx == 1
        assert criterion.id == "crit2"
        assert criterion.name == "Criteria 2"
    
    def test_get_criteria_by_id_not_found(self, sample_alternatives, sample_criteria):
        """Test error when criterion ID is not found."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria
        )
        
        with pytest.raises(ValueError, match="Dont find any criteria with ID: nonexistent"):
            matrix.get_criteria_by_id("nonexistent")
    
    def test_add_alternative(self, sample_alternatives, sample_criteria):
        """Test adding a new alternative."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives[:2],
            criteria=sample_criteria
        )
        
        new_alternative = Alternative(id="alt4", name="Alternative 4")
        values = [10.0, 11.0, 12.0]
        
        matrix.add_alternative(new_alternative, values)
        
        assert len(matrix.alternative) == 3
        assert matrix.shape == (3, 3)
        assert matrix.get_alternative_values(2).tolist() == values
    
    def test_add_alternative_no_values(self, sample_alternatives, sample_criteria):
        """Test adding a new alternative without values."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives[:2],
            criteria=sample_criteria
        )
        
        new_alternative = Alternative(id="alt4", name="Alternative 4")
        matrix.add_alternative(new_alternative)
        
        assert len(matrix.alternative) == 3
        assert matrix.shape == (3, 3)
        assert np.array_equal(matrix.get_alternative_values(2), np.zeros(3))
    
    def test_add_criteria(self, sample_alternatives, sample_criteria):
        """Test adding a new criterion."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria[:2]
        )
        
        new_criterion = Criteria(id="crit4", name="Criteria 4")
        values = [10.0, 11.0, 12.0]
        
        matrix.add_criteria(new_criterion, values)
        
        assert len(matrix.criteria) == 3
        assert matrix.shape == (3, 3)
        assert matrix.get_criteria_values(2).tolist() == values
    
    def test_remove_alternative(self, sample_alternatives, sample_criteria, sample_values):
        """Test removing an alternative."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        matrix.remove_alternative(1)  # Remove second alternative
        
        assert len(matrix.alternative) == 2
        assert matrix.shape == (2, 3)
        assert matrix.alternative[0].id == "alt1"
        assert matrix.alternative[1].id == "alt3"
    
    def test_remove_criteria(self, sample_alternatives, sample_criteria, sample_values):
        """Test removing a criterion."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        matrix.remove_criteria(1)  # Remove second criterion
        
        assert len(matrix.criteria) == 2
        assert matrix.shape == (3, 2)
        assert matrix.criteria[0].id == "crit1"
        assert matrix.criteria[1].id == "crit3"
    
    def test_normalize(self, sample_alternatives, sample_criteria, sample_values):
        """Test matrix normalization."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        normalized_matrix = matrix.normalize(method='minimax')
        
        assert normalized_matrix.name == "Test Matrix (Normalizada - minimax)"
        assert normalized_matrix.shape == matrix.shape
        assert not np.array_equal(normalized_matrix.values, matrix.values)
    
    def test_weighted_matrix(self, sample_alternatives, sample_criteria, sample_values):
        """Test creation of weighted matrix."""
        # Set specific weights for criteria
        sample_criteria[0].weight = 0.3
        sample_criteria[1].weight = 0.5
        sample_criteria[2].weight = 0.2
        
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        weighted_matrix = matrix.weighted_matrix()
        
        assert weighted_matrix.name == "Test Matrix (Weighted)"
        assert weighted_matrix.shape == matrix.shape
        assert not np.array_equal(weighted_matrix.values, matrix.values)
    
    def test_to_dict(self, sample_alternatives, sample_criteria, sample_values):
        """Test conversion to dictionary."""
        matrix = DecisionMatrix(
            name="Test Matrix",
            alternatives=sample_alternatives,
            criteria=sample_criteria,
            values=sample_values
        )
        
        matrix_dict = matrix.to_dict()
        
        assert matrix_dict['name'] == "Test Matrix"
        assert len(matrix_dict['alternatives']) == 3
        assert len(matrix_dict['criteria']) == 3
        assert matrix_dict['values'] == sample_values.tolist()
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'name': 'Test Matrix',
            'alternatives': [
                {'id': 'alt1', 'name': 'Alternative 1', 'description': '', 'metadata': {}},
                {'id': 'alt2', 'name': 'Alternative 2', 'description': '', 'metadata': {}}
            ],
            'criteria': [
                {'id': 'crit1', 'name': 'Criteria 1', 'description': '', 
                 'optimization_type': 'maximize', 'scale_type': 'quantitative', 
                 'weight': 1.0, 'unit': '', 'metadata': {}},
                {'id': 'crit2', 'name': 'Criteria 2', 'description': '', 
                 'optimization_type': 'minimize', 'scale_type': 'quantitative', 
                 'weight': 1.0, 'unit': '', 'metadata': {}}
            ],
            'values': [[1.0, 2.0], [3.0, 4.0]]
        }
        
        matrix = DecisionMatrix.from_dict(data)
        
        assert matrix.name == 'Test Matrix'
        assert len(matrix.alternative) == 2
        assert len(matrix.criteria) == 2
        assert matrix.shape == (2, 2)
        assert np.array_equal(matrix.values, np.array([[1.0, 2.0], [3.0, 4.0]]))
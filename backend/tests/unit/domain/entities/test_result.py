import pytest
import numpy as np
from datetime import datetime
from domain.entities.result import Result

class TestResult:
    
    @pytest.fixture
    def sample_data(self):
        """Fixture providing sample data for tests."""
        return {
            'method_name': 'TOPSIS',
            'alternative_ids': ['alt1', 'alt2', 'alt3', 'alt4'],
            'alternative_names': ['Alternative 1', 'Alternative 2', 'Alternative 3', 'Alternative 4'],
            'scores': np.array([0.7, 0.5, 0.9, 0.3]),
            'execution_time': 1.5,
            'parameters': {'normalization': 'vector', 'weights': [0.3, 0.4, 0.3]},
            'metadata': {'details': 'test metadata'}
        }
    
    def test_result_creation(self, sample_data):
        """Test basic creation of a Result instance."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores'],
            execution_time=sample_data['execution_time'],
            parameters=sample_data['parameters'],
            metadata=sample_data['metadata']
        )
        
        assert result.method_name == 'TOPSIS'
        assert result.alternative_ids == ['alt1', 'alt2', 'alt3', 'alt4']
        assert result.alternative_names == ['Alternative 1', 'Alternative 2', 'Alternative 3', 'Alternative 4']
        assert np.array_equal(result.scores, np.array([0.7, 0.5, 0.9, 0.3]))
        assert result.execution_time == 1.5
        assert result.parameters == {'normalization': 'vector', 'weights': [0.3, 0.4, 0.3]}
        assert result.metadata == {'details': 'test metadata'}
    
    def test_result_default_values(self, sample_data):
        """Test result creation with default values."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        assert result.execution_time == 0.0
        assert result.parameters == {}
        assert result.metadata == {}
        assert isinstance(result.created_at, datetime)
    
    def test_rankings_calculation(self, sample_data):
        """Test that rankings are calculated correctly from scores."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        expected_rankings = np.array([2, 3, 1, 4])  # Based on scores [0.7, 0.5, 0.9, 0.3]
        assert np.array_equal(result.rankings, expected_rankings)
    
    def test_rankings_with_ties(self):
        """Test rankings calculation with tied scores."""
        result = Result(
            method_name='TOPSIS',
            alternative_ids=['alt1', 'alt2', 'alt3'],
            alternative_names=['Alternative 1', 'Alternative 2', 'Alternative 3'],
            scores=np.array([0.7, 0.7, 0.9])
        )
        
        expected_rankings = np.array([2, 2, 1])  # Alternatives 1 and 2 have the same rank
        assert np.array_equal(result.rankings, expected_rankings)
    
    def test_property_immutability(self, sample_data):
        """Test that properties return copies, not references."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        # Test alternative_ids immutability
        alt_ids = result.alternative_ids
        alt_ids.append('alt5')
        assert 'alt5' not in result.alternative_ids
        
        # Test scores immutability
        scores_copy = result.scores
        scores_copy[0] = 999
        assert result.scores[0] != 999
    
    def test_get_alternative_info(self, sample_data):
        """Test getting information for a specific alternative."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        name, score, ranking = result.get_alternative_info('alt2')
        assert name == 'Alternative 2'
        assert score == 0.5
        assert ranking == 3
    
    def test_get_alternative_info_not_found(self, sample_data):
        """Test error when alternative ID is not found."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        with pytest.raises(ValueError, match="No alternative was found with ID: nonexistent"):
            result.get_alternative_info('nonexistent')
    
    def test_get_ranking_by_id(self, sample_data):
        """Test getting ranking for a specific alternative."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        ranking = result.get_ranking_by_id('alt3')
        assert ranking == 1  # Alternative 3 has the highest score (0.9)
    
    def test_get_score_by_id(self, sample_data):
        """Test getting score for a specific alternative."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        score = result.get_score_by_id('alt1')
        assert score == 0.7
    
    def test_get_best_alternative(self, sample_data):
        """Test getting the best alternative."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        best_id, best_name, best_score = result.get_best_alternative()
        assert best_id == 'alt3'
        assert best_name == 'Alternative 3'
        assert best_score == 0.9
    
    def test_get_worst_alternative(self, sample_data):
        """Test getting the worst alternative."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        worst_id, worst_name, worst_score = result.get_worst_alternative()
        assert worst_id == 'alt4'
        assert worst_name == 'Alternative 4'
        assert worst_score == 0.3
    
    def test_get_sorted_alternatives(self, sample_data):
        """Test getting alternatives sorted by score."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        sorted_alts = result.get_sorted_alternatives()
        
        assert len(sorted_alts) == 4
        assert sorted_alts[0]['id'] == 'alt3'  # Highest score
        assert sorted_alts[0]['score'] == 0.9
        assert sorted_alts[0]['ranking'] == 1
        assert sorted_alts[-1]['id'] == 'alt4'  # Lowest score
        assert sorted_alts[-1]['score'] == 0.3
        assert sorted_alts[-1]['ranking'] == 4
    
    def test_compare_alternatives(self, sample_data):
        """Test comparing two alternatives."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        comparison = result.compare_alternatives('alt1', 'alt2')
        
        assert comparison['alternative_a']['id'] == 'alt1'
        assert comparison['alternative_b']['id'] == 'alt2'
        assert comparison['difference']['score'] == pytest.approx(0.2)  # 0.7 - 0.5
        assert comparison['difference']['ranking'] == 1  # rank 3 - rank 2
        assert comparison['better_alternative'] == 'alt1'
    
    def test_set_and_get_metadata(self, sample_data):
        """Test setting and getting metadata."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        result.set_metadata('new_key', 'new_value')
        assert result.get_metadata('new_key') == 'new_value'
        assert result.get_metadata('nonexistent') is None
        assert result.get_metadata('nonexistent', 'default') == 'default'
    
    def test_to_dict(self, sample_data):
        """Test conversion to dictionary."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores'],
            execution_time=sample_data['execution_time'],
            parameters=sample_data['parameters'],
            metadata=sample_data['metadata']
        )
        
        result_dict = result.to_dict()
        
        assert result_dict['method_name'] == 'TOPSIS'
        assert result_dict['alternative_ids'] == ['alt1', 'alt2', 'alt3', 'alt4']
        assert result_dict['scores'] == [0.7, 0.5, 0.9, 0.3]
        assert result_dict['rankings'] == [2, 3, 1, 4]
        assert 'created_at' in result_dict
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'method_name': 'TOPSIS',
            'alternative_ids': ['alt1', 'alt2'],
            'alternative_names': ['Alternative 1', 'Alternative 2'],
            'scores': [0.7, 0.5],
            'rankings': [1, 2],
            'execution_time': 1.5,
            'parameters': {'key': 'value'},
            'created_at': datetime.now().isoformat(),
            'metadata': {'detail': 'test'}
        }
        
        result = Result.from_dict(data)
        
        assert result.method_name == 'TOPSIS'
        assert result.alternative_ids == ['alt1', 'alt2']
        assert np.array_equal(result.scores, np.array([0.7, 0.5]))
        assert result.execution_time == 1.5
        assert result.parameters == {'key': 'value'}
    
    def test_str_representation(self, sample_data):
        """Test string representation of result."""
        result = Result(
            method_name=sample_data['method_name'],
            alternative_ids=sample_data['alternative_ids'],
            alternative_names=sample_data['alternative_names'],
            scores=sample_data['scores']
        )
        
        str_repr = str(result)
        assert 'Resultado de TOPSIS' in str_repr
        assert '4 alternativas evaluadas' in str_repr
        assert 'Alternative 3' in str_repr  # Best alternative
        assert '0.9000' in str_repr  # Best score
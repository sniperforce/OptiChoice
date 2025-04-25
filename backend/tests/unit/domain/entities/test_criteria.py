import pytest
from domain.entities.criteria import Criteria, OptimizationType, ScaleType

class TestCriteria:
    
    def test_criteria_creation(self):
        """Test basic creation of a Criteria instance."""
        criteria = Criteria(
            id="crit1",
            name="Criterio 1",
            description="Descripción de prueba",
            optimization_type=OptimizationType.MAXIMIZE,
            scale_type=ScaleType.QUANTITATIVE,
            weight=2.5,
            unit="kg",
            metadata={"key": "value"}
        )
        
        assert criteria.id == "crit1"
        assert criteria.name == "Criterio 1"
        assert criteria.description == "Descripción de prueba"
        assert criteria.optimization_type == OptimizationType.MAXIMIZE
        assert criteria.scale_type == ScaleType.QUANTITATIVE
        assert criteria.weight == 2.5
        assert criteria.unit == "kg"
        assert criteria.metadata == {"key": "value"}
    
    def test_criteria_default_values(self):
        """Test that default values are assigned correctly."""
        criteria = Criteria(id="crit1", name="Criterio 1")
        
        assert criteria.description == ""
        assert criteria.optimization_type == OptimizationType.MAXIMIZE
        assert criteria.scale_type == ScaleType.QUANTITATIVE
        assert criteria.weight == 1.0
        assert criteria.unit == ""
        assert criteria.metadata == {}
    
    def test_name_setter(self):
        """Test the setter for name property."""
        criteria = Criteria(id="crit1", name="Nombre inicial")
        criteria.name = "Nuevo nombre"
        assert criteria.name == "Nuevo nombre"
    
    def test_description_setter(self):
        """Test the setter for description property."""
        criteria = Criteria(id="crit1", name="Criterio 1")
        criteria.description = "Nueva descripción"
        assert criteria.description == "Nueva descripción"
    
    def test_optimization_type_setter(self):
        """Test the setter for optimization_type property."""
        criteria = Criteria(id="crit1", name="Criterio 1")
        criteria.optimization_type = OptimizationType.MINIMIZE
        assert criteria.optimization_type == OptimizationType.MINIMIZE
    
    def test_scale_type_setter(self):
        """Test the setter for scale_type property."""
        criteria = Criteria(id="crit1", name="Criterio 1")
        criteria.scale_type = ScaleType.FUZZY
        assert criteria.scale_type == ScaleType.FUZZY
    
    def test_weight_setter(self):
        """Test the setter for weight property."""
        criteria = Criteria(id="crit1", name="Criterio 1")
        criteria.weight = 3.5
        assert criteria.weight == 3.5
    
    def test_unit_setter(self):
        """Test the setter for unit property."""
        criteria = Criteria(id="crit1", name="Criterio 1")
        criteria.unit = "m/s"
        assert criteria.unit == "m/s"
    
    def test_metadata_immutability(self):
        """Test that the metadata getter returns a copy."""
        criteria = Criteria(id="crit1", name="Criterio 1", metadata={"key": "value"})
        metadata_copy = criteria.metadata
        metadata_copy["new_key"] = "new_value"
        
        assert "new_key" not in criteria.metadata
        assert criteria.metadata == {"key": "value"}
    
    def test_set_metadata(self):
        """Test the set_metadata method."""
        criteria = Criteria(id="crit1", name="Criterio 1")
        criteria.set_metadata("new_key", "new_value")
        
        assert criteria.metadata["new_key"] == "new_value"
    
    def test_get_metadata(self):
        """Test the get_metadata method."""
        criteria = Criteria(id="crit1", name="Criterio 1", metadata={"key": "value"})
        
        # Existing case
        assert criteria.get_metadata("key") == "value"
        
        # Non-existent case without default
        assert criteria.get_metadata("nonexistent") is None
        
        # Non-existent case with default
        assert criteria.get_metadata("nonexistent", "default") == "default"
    
    def test_is_benefit_criteria(self):
        """Test the is_benefit_criteria method."""
        criteria_benefit = Criteria(id="crit1", name="Benefit", optimization_type=OptimizationType.MAXIMIZE)
        criteria_cost = Criteria(id="crit2", name="Cost", optimization_type=OptimizationType.MINIMIZE)
        
        assert criteria_benefit.is_benefit_criteria() is True
        assert criteria_cost.is_benefit_criteria() is False
    
    def test_is_cost_criteria(self):
        """Test the is_cost_criteria method."""
        criteria_benefit = Criteria(id="crit1", name="Benefit", optimization_type=OptimizationType.MAXIMIZE)
        criteria_cost = Criteria(id="crit2", name="Cost", optimization_type=OptimizationType.MINIMIZE)
        
        assert criteria_benefit.is_cost_criteria() is False
        assert criteria_cost.is_cost_criteria() is True
    
    def test_str_representation(self):
        """Test the string representation of criteria."""
        criteria = Criteria(id="crit1", name="Criterio 1", weight=2.5, optimization_type=OptimizationType.MAXIMIZE)
        expected_str = "Criterio 1 (maximize, peso: 2.5)"
        assert str(criteria) == expected_str
    
    def test_repr_representation(self):
        """Test the repr representation of criteria."""
        criteria = Criteria(id="crit1", name="Criterio 1", weight=2.5, optimization_type=OptimizationType.MAXIMIZE)
        repr_string = repr(criteria)
        
        assert "Criteria" in repr_string
        assert "id='crit1'" in repr_string
        assert "name='Criterio 1'" in repr_string
        assert "opt_type=maximize" in repr_string
        assert "weight=2.5" in repr_string
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        criteria = Criteria(
            id="crit1",
            name="Criterio 1",
            description="Descripción",
            optimization_type=OptimizationType.MAXIMIZE,
            scale_type=ScaleType.QUANTITATIVE,
            weight=2.5,
            unit="kg",
            metadata={"key": "value"}
        )
        
        expected_dict = {
            'id': 'crit1',
            'name': 'Criterio 1',
            'description': 'Descripción',
            'optimization_type': 'maximize',
            'scale_type': 'quantitative',
            'weight': 2.5,
            'unit': 'kg',
            'metadata': {'key': 'value'}
        }
        
        assert criteria.to_dict() == expected_dict
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'id': 'crit1',
            'name': 'Criterio 1',
            'description': 'Descripción',
            'optimization_type': 'maximize',
            'scale_type': 'quantitative',
            'weight': 2.5,
            'unit': 'kg',
            'metadata': {'key': 'value'}
        }
        
        criteria = Criteria.from_dict(data)
        
        assert criteria.id == 'crit1'
        assert criteria.name == 'Criterio 1'
        assert criteria.description == 'Descripción'
        assert criteria.optimization_type == OptimizationType.MAXIMIZE
        assert criteria.scale_type == ScaleType.QUANTITATIVE
        assert criteria.weight == 2.5
        assert criteria.unit == 'kg'
        assert criteria.metadata == {'key': 'value'}
    
    def test_from_dict_with_enum_objects(self):
        """Test creation from dictionary with enum objects instead of strings."""
        data = {
            'id': 'crit1',
            'name': 'Criterio 1',
            'optimization_type': OptimizationType.MAXIMIZE,
            'scale_type': ScaleType.QUANTITATIVE
        }
        
        criteria = Criteria.from_dict(data)
        
        assert criteria.optimization_type == OptimizationType.MAXIMIZE
        assert criteria.scale_type == ScaleType.QUANTITATIVE
    
    def test_from_dict_missing_optional_fields(self):
        """Test creation from dictionary without optional fields."""
        data = {
            'id': 'crit1',
            'name': 'Criterio 1'
        }
        
        criteria = Criteria.from_dict(data)
        
        assert criteria.id == 'crit1'
        assert criteria.name == 'Criterio 1'
        assert criteria.description == ''
        assert criteria.optimization_type == OptimizationType.MAXIMIZE
        assert criteria.scale_type == ScaleType.QUANTITATIVE
        assert criteria.weight == 1.0
        assert criteria.unit == ''
        assert criteria.metadata == {}
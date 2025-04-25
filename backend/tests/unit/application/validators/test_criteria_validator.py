import pytest
from application.validators.criteria_validator import CriteriaValidator
from domain.entities.criteria import OptimizationType, ScaleType

class TestCriteriaValidator:
    
    def test_validate_id_valid(self):
        """Test validation of a valid ID."""
        valid, error = CriteriaValidator.validate_id("crit1")
        assert valid == True
        assert error is None
    
    def test_validate_id_empty(self):
        """Test validation of an empty ID."""
        valid, error = CriteriaValidator.validate_id("")
        assert valid == False
        assert error == "The criteria identifier cannot be empty"
    
    def test_validate_id_non_string(self):
        """Test validation of a non-string ID."""
        valid, error = CriteriaValidator.validate_id(123)
        assert valid == False
        assert error == "The  identifier must be a text string"
    
    def test_validate_name_valid(self):
        """Test validation of a valid name."""
        valid, error = CriteriaValidator.validate_name("Criteria 1")
        assert valid == True
        assert error is None
    
    def test_validate_name_empty(self):
        """Test validation of an empty name."""
        valid, error = CriteriaValidator.validate_name("")
        assert valid == False
        assert error == "The criteria name cannot be empty"
    
    def test_validate_name_non_string(self):
        """Test validation of a non-string name."""
        valid, error = CriteriaValidator.validate_name(123)
        assert valid == False
        assert error == "The name must be a text string"
    
    def test_validate_description_valid(self):
        """Test validation of a valid description."""
        valid, error = CriteriaValidator.validate_description("Valid description")
        assert valid == True
        assert error is None
    
    def test_validate_description_empty(self):
        """Test validation of an empty description."""
        valid, error = CriteriaValidator.validate_description("")
        assert valid == True
        assert error is None
    
    def test_validate_description_non_string(self):
        """Test validation of a non-string description."""
        valid, error = CriteriaValidator.validate_description(123)
        assert valid == False
        assert error == "The description must be a text string"
    
    def test_validate_optimization_type_valid_enum(self):
        """Test validation of a valid optimization type enum."""
        valid, error = CriteriaValidator.validate_optimization_type(OptimizationType.MAXIMIZE)
        assert valid == True
        assert error is None
    
    def test_validate_optimization_type_valid_string(self):
        """Test validation of a valid optimization type string."""
        valid, error = CriteriaValidator.validate_optimization_type("maximize")
        assert valid == True
        assert error is None
    
    def test_validate_optimization_type_invalid_string(self):
        """Test validation of an invalid optimization type string."""
        valid, error = CriteriaValidator.validate_optimization_type("invalid")
        assert valid == False
        assert "Invalid optimization type: invalid. Must be 'maximize' or 'minimize'" in error
    
    def test_validate_optimization_type_invalid_type(self):
        """Test validation of an invalid optimization type."""
        valid, error = CriteriaValidator.validate_optimization_type(123)
        assert valid == False
        assert error == "The optimization type must be a value of the enum Optimization Type"
    
    def test_validate_scale_type_valid_enum(self):
        """Test validation of a valid scale type enum."""
        valid, error = CriteriaValidator.validate_scale_type(ScaleType.QUANTITATIVE)
        assert valid == True
        assert error is None
    
    def test_validate_scale_type_valid_string(self):
        """Test validation of a valid scale type string."""
        valid, error = CriteriaValidator.validate_scale_type("quantitative")
        assert valid == True
        assert error is None
    
    def test_validate_scale_type_invalid_string(self):
        """Test validation of an invalid scale type string."""
        valid, error = CriteriaValidator.validate_scale_type("invalid")
        assert valid == False
        assert "Invalid scale type: invalid. Must be 'quantitative', 'qualitative' or 'fuzzy'" in error
    
    def test_validate_scale_type_invalid_type(self):
        """Test validation of an invalid scale type."""
        valid, error = CriteriaValidator.validate_scale_type(123)
        assert valid == False
        assert error == "The scale type must be a value of the enum ScaleType"
    
    def test_validate_weight_valid_float(self):
        """Test validation of a valid float weight."""
        valid, error = CriteriaValidator.validate_weight(2.5)
        assert valid == True
        assert error is None
    
    def test_validate_weight_valid_int(self):
        """Test validation of a valid integer weight."""
        valid, error = CriteriaValidator.validate_weight(5)
        assert valid == True
        assert error is None
    
    def test_validate_weight_valid_string(self):
        """Test validation of a valid string weight."""
        valid, error = CriteriaValidator.validate_weight("3.14")
        assert valid == True
        assert error is None
    
    def test_validate_weight_invalid_string(self):
        """Test validation of an invalid string weight."""
        valid, error = CriteriaValidator.validate_weight("invalid")
        assert valid == False
        assert error == "The weight must be a number"
    
    def test_validate_weight_negative(self):
        """Test validation of a negative weight."""
        valid, error = CriteriaValidator.validate_weight(-1.5)
        assert valid == False
        assert error == "The weight cannot be negative"
    
    def test_validate_unit_valid(self):
        """Test validation of a valid unit."""
        valid, error = CriteriaValidator.validate_unit("kg")
        assert valid == True
        assert error is None
    
    def test_validate_unit_empty(self):
        """Test validation of an empty unit."""
        valid, error = CriteriaValidator.validate_unit("")
        assert valid == True
        assert error is None
    
    def test_validate_unit_none(self):
        """Test validation of None unit."""
        valid, error = CriteriaValidator.validate_unit(None)
        assert valid == False
        assert error == "The unit cannot be None"
    
    def test_validate_unit_non_string(self):
        """Test validation of a non-string unit."""
        valid, error = CriteriaValidator.validate_unit(123)
        assert valid == False
        assert error == "The unit must be a text string"
    
    def test_validate_metadata_valid(self):
        """Test validation of valid metadata."""
        valid, error = CriteriaValidator.validate_metadata({"key": "value"})
        assert valid == True
        assert error is None
    
    def test_validate_metadata_empty(self):
        """Test validation of empty metadata."""
        valid, error = CriteriaValidator.validate_metadata({})
        assert valid == True
        assert error is None
    
    def test_validate_metadata_non_dict(self):
        """Test validation of non-dictionary metadata."""
        valid, error = CriteriaValidator.validate_metadata("not a dict")
        assert valid == False
        assert error == "The metadata must be a dictionary"
    
    def test_validate_criteria_data_all_valid(self):
        """Test validation of all valid criteria data."""
        valid, errors = CriteriaValidator.validate_criteria_data(
            id="crit1",
            name="Criteria 1",
            description="Valid description",
            optimization_type=OptimizationType.MAXIMIZE,
            scale_type=ScaleType.QUANTITATIVE,
            weight=2.5,
            unit="kg",
            metadata={"key": "value"}
        )
        assert valid == True
        assert errors == []
    
    def test_validate_criteria_data_multiple_errors(self):
        """Test validation with multiple errors."""
        valid, errors = CriteriaValidator.validate_criteria_data(
            id="",
            name=123,
            description=456,
            optimization_type="invalid",
            scale_type="invalid",
            weight="invalid",
            unit=None,
            metadata="not a dict"
        )
        assert valid == False
        assert len(errors) == 8
    
    def test_validate_criteria_data_defaults(self):
        """Test validation with default values."""
        valid, errors = CriteriaValidator.validate_criteria_data(
            id="crit1",
            name="Criteria 1"
        )
        assert valid == True
        assert errors == []
    
    def test_validate_from_dict_valid(self):
        """Test validation from a valid dictionary."""
        data = {
            'id': 'crit1',
            'name': 'Criteria 1',
            'description': 'Valid description',
            'optimization_type': 'maximize',
            'scale_type': 'quantitative',
            'weight': 2.5,
            'unit': 'kg',
            'metadata': {'key': 'value'}
        }
        valid, errors = CriteriaValidator.validate_from_dict(data)
        assert valid == True
        assert errors == []
    
    def test_validate_from_dict_missing_required(self):
        """Test validation from dictionary missing required fields."""
        data = {
            'description': 'Only description'
        }
        valid, errors = CriteriaValidator.validate_from_dict(data)
        assert valid == False
        assert len(errors) == 2
        assert "El campo 'id' es requerido" in errors
        assert "El campo 'name' es requerido" in errors
    
    def test_validate_from_dict_minimal_valid(self):
        """Test validation from dictionary with minimal required fields."""
        data = {
            'id': 'crit1',
            'name': 'Criteria 1'
        }
        valid, errors = CriteriaValidator.validate_from_dict(data)
        assert valid == True
        assert errors == []
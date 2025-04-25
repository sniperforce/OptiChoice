# backend/tests/unit/application/validators/test_alternative_validator.py

import pytest
from application.validators.alternative_validator import AlternativeValidator

class TestAlternativeValidator:
    
    def test_validate_id_valid(self):
        """Test validation of a valid ID."""
        valid, error = AlternativeValidator.validate_id("alt1")
        assert valid == True
        assert error is None
    
    def test_validate_id_empty(self):
        """Test validation of an empty ID."""
        valid, error = AlternativeValidator.validate_id("")
        assert valid == False
        assert error == "El identificador de la alternativa no puede estar vacío"
    
    def test_validate_id_non_string(self):
        """Test validation of a non-string ID."""
        valid, error = AlternativeValidator.validate_id(123)
        assert valid == False
        assert error == "El identificador debe ser una cadena de texto"
    
    def test_validate_name_valid(self):
        """Test validation of a valid name."""
        valid, error = AlternativeValidator.validate_name("Alternative 1")
        assert valid == True
        assert error is None
    
    def test_validate_name_empty(self):
        """Test validation of an empty name."""
        valid, error = AlternativeValidator.validate_name("")
        assert valid == False
        assert error == "El nombre de la alternativa no puede estar vacío"
    
    def test_validate_name_non_string(self):
        """Test validation of a non-string name."""
        valid, error = AlternativeValidator.validate_name(123)
        assert valid == False
        assert error == "El nombre debe ser una cadena de texto"
    
    def test_validate_description_valid(self):
        """Test validation of a valid description."""
        valid, error = AlternativeValidator.validate_description("This is a valid description")
        assert valid == True
        assert error is None
    
    def test_validate_description_empty(self):
        """Test validation of an empty description."""
        valid, error = AlternativeValidator.validate_description("")
        assert valid == True
        assert error is None
    
    def test_validate_description_non_string(self):
        """Test validation of a non-string description."""
        valid, error = AlternativeValidator.validate_description(123)
        assert valid == False
        assert error == "La descripción debe ser una cadena de texto"
    
    def test_validate_metadata_valid(self):
        """Test validation of valid metadata."""
        valid, error = AlternativeValidator.validate_metadata({"key": "value"})
        assert valid == True
        assert error is None
    
    def test_validate_metadata_empty(self):
        """Test validation of empty metadata."""
        valid, error = AlternativeValidator.validate_metadata({})
        assert valid == True
        assert error is None
    
    def test_validate_metadata_none(self):
        """Test validation of None metadata."""
        valid, error = AlternativeValidator.validate_metadata(None)
        assert valid == False
        assert error == "Los metadatos no pueden ser None"
    
    def test_validate_metadata_non_dict(self):
        """Test validation of non-dictionary metadata."""
        valid, error = AlternativeValidator.validate_metadata("not a dict")
        assert valid == False
        assert error == "Los metadatos deben ser un diccionario"
    
    def test_validate_alternative_data_all_valid(self):
        """Test validation of all valid alternative data."""
        valid, errors = AlternativeValidator.validate_alternative_data(
            id="alt1",
            name="Alternative 1",
            description="Valid description",
            metadata={"key": "value"}
        )
        assert valid == True
        assert errors == []
    
    def test_validate_alternative_data_multiple_errors(self):
        """Test validation with multiple errors."""
        valid, errors = AlternativeValidator.validate_alternative_data(
            id="",
            name=123,
            description=456,
            metadata="not a dict"
        )
        assert valid == False
        assert len(errors) == 4
        assert "El identificador de la alternativa no puede estar vacío" in errors
        assert "El nombre debe ser una cadena de texto" in errors
        assert "La descripción debe ser una cadena de texto" in errors
        assert "Los metadatos deben ser un diccionario" in errors
    
    def test_validate_alternative_data_defaults(self):
        """Test validation with default values."""
        valid, errors = AlternativeValidator.validate_alternative_data(
            id="alt1",
            name="Alternative 1"
        )
        assert valid == True
        assert errors == []
    
    def test_validate_from_dict_valid(self):
        """Test validation from a valid dictionary."""
        data = {
            'id': 'alt1',
            'name': 'Alternative 1',
            'description': 'Valid description',
            'metadata': {'key': 'value'}
        }
        valid, errors = AlternativeValidator.validate_from_dict(data)
        assert valid == True
        assert errors == []
    
    def test_validate_from_dict_missing_required(self):
        """Test validation from dictionary missing required fields."""
        data = {
            'description': 'Only description'
        }
        valid, errors = AlternativeValidator.validate_from_dict(data)
        assert valid == False
        assert len(errors) == 2
        assert "El campo 'id' es requerido" in errors
        assert "El campo 'name' es requerido" in errors
    
    def test_validate_from_dict_minimal_valid(self):
        """Test validation from dictionary with minimal required fields."""
        data = {
            'id': 'alt1',
            'name': 'Alternative 1'
        }
        valid, errors = AlternativeValidator.validate_from_dict(data)
        assert valid == True
        assert errors == []
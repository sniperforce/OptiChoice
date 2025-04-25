import pytest
from domain.entities.alternative import Alternative

class TestAlternative:
    
    def test_alternative_creation(self):
        """Prueba la creación básica de una instancia de Alternative."""
        alternative = Alternative(
            id="alt1",
            name="Alternativa 1",
            description="Descripción de prueba",
            metadata={"key": "value"}
        )
        
        assert alternative.id == "alt1"
        assert alternative.name == "Alternativa 1"
        assert alternative.description == "Descripción de prueba"
        assert alternative.metadata == {"key": "value"}
    
    def test_alternative_default_values(self):
        """Prueba que los valores por defecto se asignan correctamente."""
        alternative = Alternative(id="alt1", name="Alternativa 1")
        
        assert alternative.description == ""
        assert alternative.metadata == {}
    
    def test_name_setter(self):
        """Prueba el setter para la propiedad name."""
        alternative = Alternative(id="alt1", name="Nombre inicial")
        alternative.name = "Nuevo nombre"
        assert alternative.name == "Nuevo nombre"
    
    def test_description_setter(self):
        """Prueba el setter para la propiedad description."""
        alternative = Alternative(id="alt1", name="Alternativa 1")
        alternative.description = "Nueva descripción"
        assert alternative.description == "Nueva descripción"
    
    def test_metadata_immutability(self):
        """Prueba que el getter de metadata devuelve una copia."""
        alternative = Alternative(id="alt1", name="Alternativa 1", metadata={"key": "value"})
        metadata_copy = alternative.metadata
        metadata_copy["new_key"] = "new_value"
        
        assert "new_key" not in alternative.metadata
        assert alternative.metadata == {"key": "value"}
    
    def test_set_metadata(self):
        """Prueba el método set_metadata."""
        alternative = Alternative(id="alt1", name="Alternativa 1")
        alternative.set_metadata("new_key", "new_value")
        
        assert alternative.metadata["new_key"] == "new_value"
    
    def test_get_metadata(self):
        """Prueba el método get_metadata."""
        alternative = Alternative(id="alt1", name="Alternativa 1", metadata={"key": "value"})
        
        # Caso existente
        assert alternative.get_metadata("key") == "value"
        
        # Caso no existente sin valor por defecto
        assert alternative.get_metadata("nonexistent") is None
        
        # Caso no existente con valor por defecto
        assert alternative.get_metadata("nonexistent", "default") == "default"
    
    def test_str_representation(self):
        """Prueba la representación string de la alternativa."""
        alternative = Alternative(id="alt1", name="Alternativa 1")
        assert str(alternative) == "Alternativa 1 (ID: alt1)"
    
    def test_repr_representation(self):
        """Prueba la representación repr de la alternativa."""
        alternative = Alternative(id="alt1", name="Alternativa 1", description="Una descripción muy larga más allá de 20 caracteres")
        repr_string = repr(alternative)
        
        assert "Alternative" in repr_string
        assert "id='alt1'" in repr_string
        assert "name='Alternativa 1'" in repr_string
        assert "..." in repr_string  # Verifica que se trunca la descripción larga
    
    def test_repr_short_description(self):
        """Prueba que la representación repr no trunca descripciones cortas."""
        alternative = Alternative(id="alt1", name="Alternativa 1", description="Corta")
        repr_string = repr(alternative)
        
        assert "Corta" in repr_string
        assert "..." not in repr_string
    
    def test_to_dict(self):
        """Prueba la conversión a diccionario."""
        alternative = Alternative(
            id="alt1",
            name="Alternativa 1",
            description="Descripción",
            metadata={"key": "value"}
        )
        
        expected_dict = {
            'id': 'alt1',
            'name': 'Alternativa 1',
            'description': 'Descripción',
            'metadata': {'key': 'value'}
        }
        
        assert alternative.to_dict() == expected_dict
    
    def test_from_dict(self):
        """Prueba la creación desde diccionario."""
        data = {
            'id': 'alt1',
            'name': 'Alternativa 1',
            'description': 'Descripción',
            'metadata': {'key': 'value'}
        }
        
        alternative = Alternative.from_dict(data)
        
        assert alternative.id == 'alt1'
        assert alternative.name == 'Alternativa 1'
        assert alternative.description == 'Descripción'
        assert alternative.metadata == {'key': 'value'}
    
    def test_from_dict_missing_optional_fields(self):
        """Prueba la creación desde diccionario sin campos opcionales."""
        data = {
            'id': 'alt1',
            'name': 'Alternativa 1'
        }
        
        alternative = Alternative.from_dict(data)
        
        assert alternative.id == 'alt1'
        assert alternative.name == 'Alternativa 1'
        assert alternative.description == ''
        assert alternative.metadata == {}
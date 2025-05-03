from typing import Dict, List, Optional, Tuple, Union

class AlternativeValidator:
    @staticmethod
    def validate_id(id:str) -> Tuple[bool, Optional[str]]:
        if not id:
            return False, "Alternative ID cannot be empty"
        
        if not isinstance(id, str):
            return False, "ID must be a string"
        
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', id):
            return False, "ID must contain only letters, numbers, underscores, and hyphens"
        
        return True, None
    
    @staticmethod
    def validate_name(name:str) -> Tuple[bool, Optional[str]]:
        if not name:
            return False, "El nombre de la alternativa no puede estar vacío"
        
        if not isinstance(name, str):
            return False, "El nombre debe ser una cadena de texto"
        
        return True, None
    
    @staticmethod
    def validate_description(description: str) -> Tuple[bool, Optional[str]]:
        if not isinstance(description, str):
            return False, "La descripción debe ser una cadena de texto"
        
        return True, None
    
    @staticmethod
    def validate_metadata(metadata: Dict) -> Tuple[bool, Optional[str]]:
        if metadata is None:
            return False, "Los metadatos no pueden ser None"
        
        if not isinstance(metadata, dict):
            return False, "Los metadatos deben ser un diccionario"
        
        return True, None
    
    @classmethod
    def validate_alternative_data(cls, id: str, name: str, description: str = "", 
                                  metadata: Optional[Dict] = None) -> Tuple[bool, List[str]]:
        errors = []

        id_valid, id_error = cls.validate_id(id)
        if not id_valid:
            errors.append(id_error)
        
        name_valid, name_error = cls.validate_name(name)
        if not name_valid:
            errors.append(name_error)
        
        desc_valid, desc_error = cls.validate_description(description)
        if not desc_valid:
            errors.append(desc_error)
        
        metadata = metadata or {}
        meta_valid, meta_error = cls.validate_metadata(metadata)
        if not meta_valid:
            errors.append(meta_error)
        
        return len(errors) == 0, errors
    
    @classmethod
    def validate_from_dict(cls, data: Dict) -> Tuple[bool, List[str]]:
        errors = []

        if 'id' not in data:
            errors.append("El campo 'id' es requerido")
        
        if 'name' not in data:
            errors.append("El campo 'name' es requerido")
        
        if errors:
            return False, errors
        
        return cls.validate_alternative_data(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )


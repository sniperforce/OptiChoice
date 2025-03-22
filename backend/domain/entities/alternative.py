"""
    This module define an Alternative class for represents alternatives in MCDM problems

    An alternative represents an available option for the decision maker.
"""

class Alternative:
    def __init__(self, id, name, description="", metadata=None):
        self._id = id
        self._name = name
        self._description = description
        self._metadata = metadata or {}

    @property
    def id(self):
        return self._id
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, value):
        self._description = value
    
    @property
    def metadata(self):
        return self._metadata.copy()
    
    def set_metadata(self, key, value):
        self._metadata[key] = value
    
    def get_metadata(self, key, default=None):
        return self._metadata.get(key, default)
    
    def __str__(self):
        return f"{self._name} (ID: {self._id})"
    
    def __repr__(self):
        return f"Alternative(id='{self._id}', name='{self._name}', description='{self._description[:20]}{'...' if len(self._description) > 20 else ''}')"
    
    def to_dict(self):
        return {
            'id': self._id,
            'name': self._name,
            'description': self._description,
            'metadata': self._metadata
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            _id=data['id'],
            _name=data['name'],
            _description=data.get('description', ''),
            _metadata=data.get('metadata', {})
        )
    
        
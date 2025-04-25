"""
    Module thats  define the Criteria class to represents criterian in MCDM problems

    A criteria is a dimension or aspect that is evaluated for each alternative
"""

from enum import Enum

class OptimizationType(Enum):
    """ This define the type of optimization for a criteria """
    MAXIMIZE = 'maximize'
    MINIMIZE = 'minimize'

class ScaleType(Enum):
    """ This define the type of measurement scale for a criteria """
    QUANTITATIVE = 'quantitative'       # Numeric Data
    QUALITATIVE = 'qualitative'         # Categorical Data
    FUZZY = 'fuzzy'                     # Fuzzy Data

class Criteria:

    def __init__(self, id, name, description="",
                 optimization_type=OptimizationType.MAXIMIZE,
                 scale_type=ScaleType.QUANTITATIVE, weight=1.0,
                 unit="", metadata=None):
        self._id = id
        self._name = name
        self._description = description
        self._optimization_type = optimization_type
        self._scale_type = scale_type
        self._weight = weight
        self._unit = unit
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
        self._description = value or ""
    
    @property
    def optimization_type(self):
        return self._optimization_type
    

    @optimization_type.setter
    def optimization_type(self, value):
        self._optimization_type = value

    @property
    def scale_type(self):
        return self._scale_type
    
    @scale_type.setter
    def scale_type(self, value):
        self._scale_type = value
    
    @property
    def weight(self):
        return self._weight
    
    @weight.setter
    def weight(self, value):
        self._weight = value
    
    @property
    def unit(self):
        return self._unit
    
    @unit.setter
    def unit(self, value):
        self._unit = value

    @property
    def metadata(self):
        return self._metadata.copy()
    
    def set_metadata(self, key, value):
        self._metadata[key] = value
    
    def get_metadata(self, key, default=None):
        return self._metadata.get(key, default)
    
    def is_benefit_criteria(self):
        return self._optimization_type == OptimizationType.MAXIMIZE
    
    def is_cost_criteria(self):
        return self._optimization_type == OptimizationType.MINIMIZE
    
    def __str__(self):
        return f"{self._name} ({self._optimization_type.value}, peso: {self._weight})"
    
    def __repr__(self):
        return (f"Criteria(id='{self._id}', name='{self._name}',"
                f"opt_type={self._optimization_type.value}, weight={self._weight}")
    
    def to_dict(self):
        return {
            'id': self._id,
            'name': self._name,
            'description': self._description,
            'optimization_type': self._optimization_type.value,
            'scale_type': self._scale_type.value,
            'weight': self._weight,
            'unit': self._unit,
            'metadata': self._metadata
        }
    
    @classmethod
    def from_dict(cls, data):
        opt_type = data.get('optimization_type', OptimizationType.MAXIMIZE.value)
        if isinstance(opt_type, str):
            opt_type = OptimizationType(opt_type)
            
        scale_type = data.get('scale_type', ScaleType.QUANTITATIVE.value)
        if isinstance(scale_type, str):
            scale_type = ScaleType(scale_type)
        
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            optimization_type=opt_type,
            scale_type=scale_type,
            weight=data.get('weight', 1.0),
            unit=data.get('unit', ''),
            metadata=data.get('metadata', {})
        )
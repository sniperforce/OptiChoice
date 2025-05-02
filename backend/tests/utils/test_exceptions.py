# test_exceptions.py

import pytest
from utils.exceptions import (
    MCDMBaseException, ValidationError, RepositoryError,
    MethodError, NormalizationError, ImportExportError, ServiceError
)

class TestExceptions:
    
    def test_base_exception(self):
        """Prueba la excepción base."""
        exception = MCDMBaseException()
        assert str(exception) == "Error in the MCDM system"
        
        custom_msg = "Custom error message"
        exception = MCDMBaseException(custom_msg)
        assert str(exception) == custom_msg
    
    def test_validation_error(self):
        """Prueba ValidationError."""
        errors = ["Field 'name' is required", "Value must be positive"]
        exception = ValidationError("Invalid data", errors)
        
        assert exception.message == "Invalid data"
        assert exception.errors == errors
        assert "Invalid data: Field 'name' is required; Value must be positive" in str(exception)
        
        # Sin errores específicos
        exception = ValidationError("Invalid data")
        assert str(exception) == "Invalid data"
    
    def test_repository_error(self):
        """Prueba RepositoryError."""
        cause = ValueError("Original error")
        exception = RepositoryError("Error accessing repository", cause)
        
        assert exception.message == "Error accessing repository"
        assert exception.cause == cause
        assert "Error accessing repository - Cause: Original error" in str(exception)
        
        # Sin causa
        exception = RepositoryError("Error accessing repository")
        assert str(exception) == "Error accessing repository"
    
    def test_method_error(self):
        """Prueba MethodError."""
        exception = MethodError("Calculation error", "TOPSIS")
        assert "Calculation error in method 'TOPSIS'" in str(exception)
        
        # Sin nombre de método
        exception = MethodError("Calculation error")
        assert str(exception) == "Calculation error"
    
    def test_normalization_error(self):
        """Prueba NormalizationError."""
        exception = NormalizationError("Invalid values", "vector")
        assert "Invalid values using method 'vector'" in str(exception)
        
        # Sin método
        exception = NormalizationError("Invalid values")
        assert str(exception) == "Invalid values"
    
    def test_import_export_error(self):
        """Prueba ImportExportError."""
        exception = ImportExportError("Error importing data", "data.csv")
        assert "Error importing data - File: 'data.csv'" in str(exception)
        
        # Sin archivo
        exception = ImportExportError("Error importing data")
        assert str(exception) == "Error importing data"
    
    def test_service_error(self):
        """Prueba ServiceError."""
        exception = ServiceError("Operation failed", "DecisionService")
        assert "Operation failed in service 'DecisionService'" in str(exception)
        
        # Sin nombre de servicio
        exception = ServiceError("Operation failed")
        assert str(exception) == "Operation failed"
class MCDMBaseException(Exception):
    def __init__(self, message: str = "Error in the MCDM system"):
        self.message = message
        super().__init__(self.message)


class ValidationError(MCDMBaseException):
    def __init__(self, message: str = "Validation error", errors: list = None):
        self.errors = errors or []
        super().__init__(message)

    def __str__(self):
        if self.errors:
            return f"{self.message}: {'; '.join(self.errors)}"
        return self.message


class RepositoryError(MCDMBaseException):
    def __init__(self, message: str = "Repository error", cause: Exception = None):
        self.cause = cause
        super().__init__(message)

    def __str__(self):
        if self.cause:
            return f"{self.message} - Cause: {str(self.cause)}"
        return self.message


class MethodError(MCDMBaseException):
    def __init__(self, message: str = "Error in MCDM method", method_name: str = None):
        self.method_name = method_name
        msg = f"{message} in method '{method_name}'" if method_name else message
        super().__init__(msg)


class NormalizationError(MCDMBaseException):
    def __init__(self, message: str = "Error in normalization", method: str = None):
        self.method = method
        msg = f"{message} using method '{method}'" if method else message
        super().__init__(msg)


class ImportExportError(MCDMBaseException):
    def __init__(self, message: str = "Error in import/export", file_path: str = None):
        self.file_path = file_path
        msg = f"{message} - File: '{file_path}'" if file_path else message
        super().__init__(msg)


class ServiceError(MCDMBaseException):
    def __init__(self, message: str = "Error in service", service_name: str = None):
        self.service_name = service_name
        msg = f"{message} in service '{service_name}'" if service_name else message
        super().__init__(msg)
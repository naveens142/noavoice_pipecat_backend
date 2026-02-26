"""
Custom exception classes for the application.
Provides structured error handling with logging integration.
"""
from typing import Optional, Any, Dict
from app.config.logging import error_logger


class NoavoiceException(Exception):
    """
    Base exception class for all Noavoice exceptions.
    All custom exceptions should inherit from this.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        log_error: bool = True
    ):
        """
        Initialize exception with structured information.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional context information
            log_error: Whether to log this error
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        
        if log_error:
            error_logger.error(
                f"{error_code}: {message}",
                extra={"details": self.details}
            )
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class DatabaseError(NoavoiceException):
    """Exception for database-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "DB_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)


class DatabaseSchemaError(DatabaseError):
    """Exception for database schema-related errors."""
    
    def __init__(
        self,
        message: str,
        schema_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if schema_name:
            details['schema'] = schema_name
        
        super().__init__(
            message,
            error_code="DB_SCHEMA_ERROR",
            details=details
        )


class SchemaNotFoundError(DatabaseSchemaError):
    """Exception raised when required schema does not exist."""
    
    def __init__(self, schema_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Database schema '{schema_name}' not found. Please create it manually before starting the application."
        if details is None:
            details = {}
        details['action'] = 'CREATE SCHEMA manually'
        details['sql'] = f"CREATE SCHEMA {schema_name};"
        
        super().__init__(message, schema_name, details)


class DatabaseConnectionError(DatabaseError):
    """Exception raised when unable to connect to database."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code="DB_CONNECTION_ERROR",
            details=details
        )


class ValidationError(NoavoiceException):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if field:
            details['field'] = field
        
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class ConfigurationError(NoavoiceException):
    """Exception for configuration-related errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            details=details
        )


class AuthenticationError(NoavoiceException):
    """Exception for authentication errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            error_code="AUTH_ERROR",
            details=details
        )


class ExternalServiceError(NoavoiceException):
    """Exception for external service integration errors."""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        details['service'] = service_name
        if status_code:
            details['status_code'] = status_code
        
        super().__init__(
            f"{service_name}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details
        )

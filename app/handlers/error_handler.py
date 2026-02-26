"""
FastAPI error handlers for custom exceptions.
Provides structured error responses and logging.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.handlers.exceptions import (
    NoavoiceException,
    DatabaseError,
    ValidationError,
    ConfigurationError
)
from app.config.logging import app_logger, error_logger


async def noavoice_exception_handler(request: Request, exc: NoavoiceException):
    """Handle Noavoice custom exceptions."""
    error_logger.error(
        f"Noavoice Exception: {exc.error_code}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": exc.error_code
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    error_logger.error(
        f"Database Error: {exc.error_code}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    app_logger.warning(
        f"Validation Error: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "field": exc.details.get("field")
        }
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


async def configuration_error_handler(request: Request, exc: ConfigurationError):
    """Handle configuration errors."""
    error_logger.critical(
        f"Configuration Error: {exc.error_code}",
        exc_info=True,
        extra={
            "config_key": exc.details.get("config_key")
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details
        }
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions."""
    error_logger.warning(
        f"HTTP Exception: {exc.status_code}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail
        }
    )


async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    app_logger.warning(
        "Request validation failed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": errors
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": {"errors": errors}
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    error_logger.critical(
        "Unexpected exception occurred",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please contact support."
        }
    )


def register_exception_handlers(app: FastAPI):
    """
    Register all exception handlers with the FastAPI app.
    
    Call this during application initialization:
    
    Example:
        app = FastAPI()
        register_exception_handlers(app)
    """
    app.add_exception_handler(NoavoiceException, noavoice_exception_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(ConfigurationError, configuration_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

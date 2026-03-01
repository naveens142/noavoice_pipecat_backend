"""
Logger utility for easy import and use throughout the application.
"""
from app.config.logging import app_logger, db_logger, error_logger

def get_logger(name: str = None):
    """Get a logger instance. Returns app_logger by default."""
    return app_logger

__all__ = ["app_logger", "db_logger", "error_logger", "get_logger"]

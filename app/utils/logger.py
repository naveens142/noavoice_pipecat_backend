"""
Logger utility for easy import and use throughout the application.
"""
from app.config.logging import app_logger, db_logger, error_logger

__all__ = ["app_logger", "db_logger", "error_logger"]

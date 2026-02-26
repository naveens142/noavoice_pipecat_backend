"""
Production-level logging configuration.
Supports file and console logging with different levels and formats.
"""
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from app.config.settings import settings

# Ensure logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Log file names
MAIN_LOG_FILE = LOG_DIR / "application.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
DB_LOG_FILE = LOG_DIR / "database.log"

# Log format
DETAILED_FORMAT = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

JSON_FORMAT = logging.Formatter(
    fmt='{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "file": "%(filename)s", "line": %(lineno)d}'
)

def get_logger(name: str, log_file: Path = None, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional file path to log to
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # Keep 5 backup files
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(DETAILED_FORMAT)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def setup_loggers():
    """
    Initialize all application loggers.
    Call this during application startup.
    """
    # Main application logger
    globals()['app_logger'] = get_logger(
        'noavoice',
        log_file=MAIN_LOG_FILE,
        level=logging.DEBUG if settings.DEBUG else logging.INFO
    )
    
    # Database logger
    globals()['db_logger'] = get_logger(
        'noavoice.database',
        log_file=DB_LOG_FILE,
        level=logging.DEBUG if settings.DEBUG else logging.WARNING
    )
    
    # Error logger
    globals()['error_logger'] = get_logger(
        'noavoice.error',
        log_file=ERROR_LOG_FILE,
        level=logging.ERROR
    )

# Initialize loggers
setup_loggers()

# Export loggers for easy import
app_logger = logging.getLogger('noavoice')
db_logger = logging.getLogger('noavoice.database')
error_logger = logging.getLogger('noavoice.error')

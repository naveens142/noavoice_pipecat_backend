"""
Utility functions for structured logging with automatic context.
Makes logging even easier with helper functions.
"""
import functools
import time
from typing import Any, Callable
from app.config.logging import app_logger, db_logger, error_logger


def log_operation(operation_name: str, logger=app_logger):
    """
    Decorator to automatically log function entry/exit and timing.
    
    Usage:
        @log_operation("user_creation")
        async def create_user(self, user_data):
            # Automatically logs start, end, and duration
            return await self.service.create(user_data)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(
                f"Starting {operation_name}",
                extra={"operation": operation_name, "function": func.__name__}
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation_name} completed",
                    extra={
                        "operation": operation_name,
                        "duration_seconds": round(duration, 2),
                        "status": "success"
                    }
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation_name} failed",
                    exc_info=True,
                    extra={
                        "operation": operation_name,
                        "duration_seconds": round(duration, 2),
                        "error": str(e)
                    }
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger.debug(
                f"Starting {operation_name}",
                extra={"operation": operation_name, "function": func.__name__}
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"{operation_name} completed",
                    extra={
                        "operation": operation_name,
                        "duration_seconds": round(duration, 2),
                        "status": "success"
                    }
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"{operation_name} failed",
                    exc_info=True,
                    extra={
                        "operation": operation_name,
                        "duration_seconds": round(duration, 2),
                        "error": str(e)
                    }
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_db_operation(operation_type: str, entity: str = None):
    """
    Decorator to log database operations with automatic context.
    
    Usage:
        @log_db_operation("select", "User")
        async def get_user(self, user_id):
            return await self.db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            context = {
                "db_operation": operation_type,
                "entity": entity,
                "function": func.__name__
            }
            
            start_time = time.time()
            db_logger.debug(
                f"DB {operation_type} starting",
                extra=context
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                context["duration_ms"] = round(duration * 1000, 2)
                context["status"] = "success"
                
                db_logger.info(
                    f"DB {operation_type} completed",
                    extra=context
                )
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                context["duration_ms"] = round(duration * 1000, 2)
                context["error"] = str(e)
                
                db_logger.error(
                    f"DB {operation_type} failed",
                    exc_info=True,
                    extra=context
                )
                raise
        
        return async_wrapper
    
    return decorator


class OperationLogger:
    """
    Context manager for logging operation blocks.
    
    Usage:
        async with OperationLogger("user_sync") as logger:
            # Automatically logs start
            result = await sync_users()
            logger.add("synced_count", len(result))
            # Automatically logs completion with context
    """
    
    def __init__(self, operation_name: str, logger=app_logger):
        self.operation_name = operation_name
        self.logger = logger
        self.context = {"operation": operation_name}
        self.start_time = None
    
    async def __aenter__(self):
        self.start_time = time.time()
        self.logger.debug(
            f"Operation started: {self.operation_name}",
            extra=self.context
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.context["duration_seconds"] = round(duration, 2)
        
        if exc_type is None:
            self.context["status"] = "success"
            self.logger.info(
                f"Operation completed: {self.operation_name}",
                extra=self.context
            )
        else:
            self.context["status"] = "failed"
            self.context["error"] = str(exc_val)
            self.logger.error(
                f"Operation failed: {self.operation_name}",
                exc_info=True,
                extra=self.context
            )
        
        return False  # Don't suppress exceptions
    
    def add(self, key: str, value: Any):
        """Add context information to the operation log"""
        self.context[key] = value


# Example usage functions
async def example_operation_logger():
    """Example of using OperationLogger"""
    async with OperationLogger("bulk_user_import") as logger:
        users = []
        for i in range(100):
            users.append({"name": f"User {i}", "email": f"user{i}@example.com"})
            
        logger.add("total_users", len(users))
        # Automatically logs: "Operation completed: bulk_user_import" 
        # with duration and total_users in context


def quick_log(message: str, **context):
    """
    Quick logging without extra boilerplate.
    
    Usage:
        quick_log("user_created", user_id="123", email="test@example.com")
    """
    app_logger.info(message, extra=context)


def quick_error(message: str, **context):
    """
    Quick error logging.
    
    Usage:
        quick_error("sync_failed", service="calcom", status_code=500)
    """
    error_logger.error(message, extra=context)


# Performance monitoring
class PerformanceMonitor:
    """
    Monitor and log performance metrics.
    
    Usage:
        pm = PerformanceMonitor("api_call")
        pm.start()
        result = await call_api()
        pm.end()
        pm.log()  # Logs with duration
    """
    
    def __init__(self, operation: str, logger=db_logger):
        self.operation = operation
        self.logger = logger
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start timing"""
        self.start_time = time.time()
        self.logger.debug(f"Monitoring started: {self.operation}")
    
    def end(self):
        """End timing"""
        self.end_time = time.time()
    
    def get_duration_ms(self) -> float:
        """Get duration in milliseconds"""
        if self.start_time and self.end_time:
            return round((self.end_time - self.start_time) * 1000, 2)
        return 0
    
    def log(self, **extra_context):
        """Log performance metrics"""
        duration_ms = self.get_duration_ms()
        
        context = {
            "operation": self.operation,
            "duration_ms": duration_ms,
            **extra_context
        }
        
        if duration_ms > 1000:  # Warn if over 1 second
            self.logger.warning(
                f"Slow operation detected: {self.operation}",
                extra=context
            )
        else:
            self.logger.info(
                f"Operation performance: {self.operation}",
                extra=context
            )


__all__ = [
    "log_operation",
    "log_db_operation",
    "OperationLogger",
    "quick_log",
    "quick_error",
    "PerformanceMonitor"
]

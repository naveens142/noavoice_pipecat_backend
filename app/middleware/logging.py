from fastapi import FastAPI, Request
from app.config.logging import app_logger
import time


def setup_request_logging(app: FastAPI) -> None:
    """
    Setup request/response logging middleware.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # Start timing
        start_time = time.time()
        request_id = request.headers.get("x-request-id", "unknown")
        
        # Log incoming request
        app_logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            app_logger.info(
                f"[{request_id}] {request.method} {request.url.path} {response.status_code} ({process_time:.3f}s)",
                extra={"request_id": request_id, "duration_ms": process_time * 1000}
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            app_logger.error(
                f"[{request_id}] {request.method} {request.url.path} Error: {str(e)} ({process_time:.3f}s)",
                exc_info=True,
                extra={"request_id": request_id}
            )
            raise

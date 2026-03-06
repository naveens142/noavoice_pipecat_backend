from fastapi import FastAPI, Request
from app.config.logging import app_logger
import time
import json
from io import BytesIO


def setup_request_logging(app: FastAPI) -> None:
    """
    Setup request/response logging middleware with detailed parameter and response logging.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        # Start timing
        start_time = time.time()
        request_id = request.headers.get("x-request-id", "unknown")
        
        # Extract query parameters
        query_params = dict(request.query_params) if request.query_params else {}
        
        # Extract request body for POST/PUT/PATCH requests
        request_body = None
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                body = await request.body()
                if body:
                    try:
                        request_body = json.loads(body)
                    except (json.JSONDecodeError, ValueError):
                        request_body = body.decode('utf-8', errors='ignore')
                # Recreate request for downstream processing
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception as e:
                app_logger.debug(f"[{request_id}] Could not read request body: {str(e)}")
        
        # Build request info string
        request_info = f"[{request_id}] 📥 {request.method:6} {request.url.path}"
        
        # Add query parameters to log
        if query_params:
            request_info += f"\n   Query Params: {json.dumps(query_params, indent=2)}"
        
        # Add request body to log
        if request_body:
            body_str = json.dumps(request_body, indent=2) if isinstance(request_body, dict) else str(request_body)
            request_info += f"\n   Body: {body_str}"
        
        app_logger.info(request_info)
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Try to read response body
            response_body = None
            if response.status_code < 400:  # Only log successful responses body to avoid clutter
                try:
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                    
                    if body:
                        try:
                            response_body = json.loads(body)
                        except (json.JSONDecodeError, ValueError):
                            response_body = body.decode('utf-8', errors='ignore')
                    
                    # Recreate response with new body iterator
                    async def send_body():
                        yield body
                    response.body_iterator = send_body()
                except Exception as e:
                    app_logger.debug(f"[{request_id}] Could not read response body: {str(e)}")
            
            # Build response info string
            status_emoji = "✅" if 200 <= response.status_code < 300 else "⚠️" if 300 <= response.status_code < 400 else "❌"
            response_info = f"[{request_id}] 📤 {status_emoji} {request.method:6} {request.url.path} → {response.status_code} ({process_time:.3f}s)"
            
            # Add response body to log (only for successful responses to avoid clutter)
            if response_body and response.status_code < 400:
                body_str = json.dumps(response_body, indent=2)[:500]  # Limit length
                response_info += f"\n   Response: {body_str}"
            
            app_logger.info(response_info)
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            error_msg = f"[{request_id}] 📤 ❌ {request.method:6} {request.url.path} → Error ({process_time:.3f}s)\n   Error: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            raise

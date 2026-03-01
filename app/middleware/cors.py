from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings


def setup_cors(app: FastAPI) -> None:
    """
    Setup CORS middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    if settings.DEBUG:
        # Development: Allow localhost and common dev ports
        allow_origins = [
            "http://localhost:3000",
            "http://localhost:5173",  # Vite default
            "http://localhost:8080",  # Another common port
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:8080",
            "*",  # Allow all in dev as fallback
        ]
    else:
        # Production: Restrict to specific origins
        allow_origins = [
            "https://noavoice.com",
            "https://www.noavoice.com",
        ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

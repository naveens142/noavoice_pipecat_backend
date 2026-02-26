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
        # Development: Allow all origins
        allow_origins = ["*"]
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

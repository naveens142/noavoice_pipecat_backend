from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.config.logging import app_logger
from app.config.database import init_db
from app.handlers.error_handler import register_exception_handlers
from app.middleware.cors import setup_cors
from app.middleware.logging import setup_request_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.
    - Startup: Initialize database, setup logging
    - Shutdown: Cleanup resources
    """
    # Startup
    app_logger.info("═" * 60)
    app_logger.info("🚀 Starting Noavoice LiveKit Backend")
    app_logger.info("═" * 60)
    
    try:
        app_logger.info(f"Initializing database (schema: {settings.DB_SCHEMA})...")
        await init_db()
        app_logger.info("✅ Database initialized successfully")
    except Exception as e:
        app_logger.error(f"❌ Failed to initialize database: {str(e)}", exc_info=True)
        raise
    
    app_logger.info("✅ Application startup complete")
    app_logger.info("═" * 60)
    
    yield
    
    # Shutdown
    app_logger.info("═" * 60)
    app_logger.info("🛑 Shutting down Noavoice LiveKit Backend")
    app_logger.info("═" * 60)


# Create FastAPI application
app = FastAPI(
    title="Noavoice LiveKit Backend",
    description="Backend API for managing video calls with LiveKit integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Register exception handlers (must be done before adding routes)
register_exception_handlers(app)

# Setup middlewares
setup_cors(app)
setup_request_logging(app)

# Include routers
from app.api.v1 import router as v1_router
app.include_router(v1_router.router)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "noavoice-livekit-backend",
        "environment": "production" if not settings.DEBUG else "development"
    }

# Health check endpoint
@app.get("/")
async def home():
    """Home endpoint"""
    return {
        "This is Home page"
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Use our custom logging
    )

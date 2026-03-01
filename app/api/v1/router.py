"""V1 API Router - includes all endpoints"""
from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints import auth

# Create main router
router = APIRouter(prefix="/api/v1")

# Include auth routes
router.include_router(auth.router)

# TODO: Include other routes as needed
# from app.api.v1.endpoints import appointments, livekit, users, webhooks
# router.include_router(appointments.router)
# router.include_router(livekit.router)
# router.include_router(users.router)
# router.include_router(webhooks.router)

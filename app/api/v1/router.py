"""V1 API Router - includes all endpoints"""
from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints import auth, agents, appointments, agent_pipecat, twilio_routes, test_redis

# Create main router
router = APIRouter(prefix="/api/v1")

# Include auth routes
router.include_router(auth.router)
router.include_router(agents.router)
router.include_router(appointments.router)
router.include_router(agent_pipecat.router)
router.include_router(twilio_routes.router)
router.include_router(test_redis.router)
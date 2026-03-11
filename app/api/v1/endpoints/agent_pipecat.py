# api/routers/agent.py

import httpx
import logging
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["Pipecat Agent"])

# Your Pipecat agent base URL (set in env)
AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:7860")


class AgentConnectResponse(BaseModel):
    rtc_url: str          # WebRTC signaling URL the UI connects to
    agent_url: str        # Base agent URL (for health checks etc.)
    session_id: Optional[str] = None


class AgentHealthResponse(BaseModel):
    status: str
    agent_reachable: bool


@router.get("/health", response_model=AgentHealthResponse, responses={
    200: {
        "description": "Agent health check successful",
        "content": {
            "application/json": {
                "example": {
                    "status": "ok",
                    "agent_reachable": True
                }
            }
        }
    },
    503: {
        "description": "Agent is unavailable",
        "content": {
            "application/json": {
                "example": {
                    "status": "degraded",
                    "agent_reachable": False
                }
            }
        }
    }
})
async def agent_health():
    """
    Check if the Pipecat agent is reachable and healthy.
    
    **Returns:**
    - **status**: "ok" or "degraded"
    - **agent_reachable**: true if agent is responding
    
    **Use case:** Called by UI to verify voice agent availability before initiating calls
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{AGENT_BASE_URL}/health")
            return AgentHealthResponse(
                status="ok",
                agent_reachable=resp.status_code == 200
            )
    except Exception:
        return AgentHealthResponse(status="degraded", agent_reachable=False)


@router.post("/connect", response_model=AgentConnectResponse, responses={
    200: {
        "description": "Successfully connected to agent",
        "content": {
            "application/json": {
                "example": {
                    "rtc_url": "http://localhost:7860/api/offer",
                    "agent_url": "http://localhost:7860",
                    "session_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            }
        }
    },
    503: {
        "description": "Agent is not available",
        "content": {
            "application/json": {
                "example": {"detail": "Voice agent is not available. Please try again shortly."}
            }
        }
    }
})
async def connect_to_agent():
    """
    Connect to Pipecat agent for WebRTC voice session.
    
    **Description:**
    Returns the WebRTC signaling URL for the UI to connect directly to the agent.
    The UI uses @pipecat-ai/client-react with this URL to establish
    a WebRTC voice session.

    **Returns:**
    - **rtc_url**: WebRTC signaling endpoint for client connection
    - **agent_url**: Base agent URL (for health checks, etc)
    - **session_id**: Unique session identifier for tracking

    **Session lifecycle:**
    - Sessions are created on WebRTC connection
    - Sessions auto-release on client disconnect
    - Tab close / network drop triggers ICE failure → agent cleans up automatically
    
    **Response Code:** 200 OK (or 503 if agent unavailable)
    """
    try:
        # Verify agent is alive before returning its URL
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{AGENT_BASE_URL}/health")
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Voice agent is not available. Please try again shortly."
        )
    except Exception as e:
        logger.warning(f"Agent health check warning: {e}")
        # Don't block — agent may still accept connections

    # SmallWebRTC transport exposes /api/offer as the signaling endpoint
    rtc_url = f"{AGENT_BASE_URL}/api/offer"
    
    # Generate a session ID for tracking this connection
    session_id = str(uuid.uuid4())

    logger.info(f"Agent connect requested → {rtc_url} (session: {session_id})")

    return AgentConnectResponse(
        rtc_url=rtc_url,
        agent_url=AGENT_BASE_URL,
        session_id=session_id,
    )
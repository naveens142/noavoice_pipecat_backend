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


@router.get("/health", response_model=AgentHealthResponse)
async def agent_health():
    """Check if the Pipecat agent is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{AGENT_BASE_URL}/health")
            return AgentHealthResponse(
                status="ok",
                agent_reachable=resp.status_code == 200
            )
    except Exception:
        return AgentHealthResponse(status="degraded", agent_reachable=False)


@router.post("/connect", response_model=AgentConnectResponse)
async def connect_to_agent():
    """
    Returns the WebRTC signaling URL for the UI to connect directly to the agent.

    The UI uses @pipecat-ai/client-react with this URL to establish
    a WebRTC voice session. No dispatcher needed for single-agent deployments.

    Session lifecycle:
    - Sessions are created on WebRTC connection
    - Sessions auto-release on client disconnect (handled in agent main.py)
    - Tab close / network drop triggers ICE failure → agent cleans up via
      on_client_disconnected event handler
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
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.utils.dependencies import get_current_user
from app.utils.uuid_helpers import normalize_uuid
from app.models.user import User
from app.services.agent_service_async import AgentAsyncService
from app.services.agent_action_service_async import AgentActionAsyncService
from app.schemas.agent import (
CreateAgentRequest,
UpdateAgentRequest,
AgentResponse,
AgentWithActionsResponse,
PaginatedAgentResponse,
)
from app.schemas.agent_action import (
CreateAgentActionRequest,
UpdateAgentActionRequest,
AgentActionResponse,
)
from app.schemas.knowledge_base import (
UploadKnowledgeBaseRequest,
KnowledgeBaseResponse,
AssignKnowledgeBaseRequest,
)
from app.services.knowledge_base_service_async import KnowledgeBaseServiceAsync
router = APIRouter(
prefix="/agents",
tags=["Agents"],
)


# ==================== AGENT ENDPOINTS ====================

@router.post(
"",
response_model=AgentResponse,
status_code=status.HTTP_201_CREATED,
summary="Create new agent",
description="Create a new agent with name and description. Other fields auto-populated with defaults.",
responses={
    201: {
        "description": "Agent successfully created",
        "content": {
            "application/json": {
                "example": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Customer Support Agent",
                    "description": "AI agent to handle customer support inquiries",
                    "voice": "",
                    "language": "EN",
                    "timezone": "America/Detroit",
                    "system_prompt": "",
                    "first_message": "",
                    "end_call_message": "",
                    "voicemail_message": "",
                    "first_message_mode": "assistant-speaks-first",
                    "end_call_function_enabled": True,
                    "recording_enabled": False,
                    "detect_caller_number": False,
                    "multi_lingual_enabled": False,
                    "is_active": True,
                    "created_at": "2026-03-11T08:42:33.011000Z",
                    "updated_at": "2026-03-11T08:42:33.011000Z"
                }
            }
        }
    },
    400: {
        "description": "Invalid request data",
        "content": {
            "application/json": {
                "example": {"detail": "Agent name is required"}
            }
        }
    },
    401: {
        "description": "Unauthorized",
        "content": {
            "application/json": {
                "example": {"detail": "Invalid or expired token"}
            }
        }
    }
}
)
async def create_agent(
    request: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AgentResponse:
    """
    Create a new agent.
    
    **Required fields:**
    - **name**: Agent name (string)
    
    **Optional fields:**
    - **description**: Agent description (string)

    **Auto-populated defaults:**
    - voice: "" (empty)
    - language: "EN"
    - timezone: "America/Detroit"
    - system_prompt: "" (empty)
    - first_message: "" (empty)
    - end_call_message: "" (empty)
    - voicemail_message: "" (empty)
    - first_message_mode: "assistant-speaks-first"
    - end_call_function_enabled: true
    - recording_enabled: false
    - detect_caller_number: false
    - multi_lingual_enabled: false
    - is_active: true
    """
    service = AgentAsyncService(db)
    return await service.create_agent(str(current_user.id), request)

@router.get(
"",
response_model=PaginatedAgentResponse,
summary="List agents",
description="Get paginated list of agents for current user",
responses={
    200: {
        "description": "List of agents",
        "content": {
            "application/json": {
                "example": {
                    "items": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "user_id": "550e8400-e29b-41d4-a716-446655440000",
                            "name": "Customer Support Agent",
                            "description": "AI agent to handle customer support inquiries",
                            "voice": "Xb7hH8MSUJpSbSDYk0k2",
                            "language": "EN",
                            "timezone": "America/Detroit",
                            "system_prompt": "You are a helpful customer support representative...",
                            "first_message": "Hello! How can I help you today?",
                            "end_call_message": "Thank you for contacting us!",
                            "voicemail_message": "Please leave a message after the beep.",
                            "first_message_mode": "assistant-speaks-first",
                            "end_call_function_enabled": True,
                            "recording_enabled": True,
                            "detect_caller_number": False,
                            "multi_lingual_enabled": False,
                            "is_active": True,
                            "created_at": "2026-03-07T08:42:33.011000Z",
                            "updated_at": "2026-03-07T08:42:33.011000Z"
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "page_size": 20,
                    "total_pages": 1
                }
            }
        }
    }
}
)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaginatedAgentResponse:
    """
    Get list of agents for current user with pagination.
    
    **Query parameters:**
    - **skip**: Pagination offset (default: 0)
    - **limit**: Page size (default: 20, max: 100)
    """
    service = AgentAsyncService(db)
    return await service.list_agents(str(current_user.id), skip, limit)


@router.get(
"/search",
response_model=list[AgentResponse],
summary="Search agents",
description="Search agents by name or description",
responses={
    200: {
        "description": "Search results",
        "content": {
            "application/json": {
                "example": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Customer Support Agent",
                        "description": "AI agent to handle customer support inquiries",
                        "voice": "Xb7hH8MSUJpSbSDYk0k2",
                        "language": "EN",
                        "timezone": "America/Detroit",
                        "system_prompt": "You are a helpful customer support representative...",
                        "first_message": "Hello! How can I help you today?",
                        "end_call_message": "Thank you for contacting us!",
                        "voicemail_message": "Please leave a message after the beep.",
                        "first_message_mode": "assistant-speaks-first",
                        "end_call_function_enabled": True,
                        "recording_enabled": True,
                        "detect_caller_number": False,
                        "multi_lingual_enabled": False,
                        "is_active": True,
                        "created_at": "2026-03-07T08:42:33.011000Z",
                        "updated_at": "2026-03-07T08:42:33.011000Z"
                    }
                ]
            }
        }
    }
}
)
async def search_agents(
    q: str = Query(..., min_length=1, description="Search term"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ) -> list[AgentResponse]:
    """
    Search agents by name or description.
    
    **Query parameters:**
    - **q**: Search term (required, min 1 character) - searches agent name and description
    """
    service = AgentAsyncService(db)
    return await service.search_agents(str(current_user.id), q)

@router.get(
"/tools/available",
response_model=list[dict],
summary="Get available tools",
description="Get list of all available tools for agents",
responses={
    200: {
        "description": "List of available tools",
        "content": {
            "application/json": {
                "example": [
                    {
                        "id": "tool-001",
                        "tool_key": "cal_com_appointment",
                        "display_name": "Cal.com Appointment Booking",
                        "category": "appointment",
                        "description": "Book and manage appointments using Cal.com"
                    },
                    {
                        "id": "tool-002",
                        "tool_key": "twilio_sms",
                        "display_name": "Send SMS",
                        "category": "external",
                        "description": "Send SMS messages via Twilio"
                    }
                ]
            }
        }
    }
}
)
async def get_available_tools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict]:
    """
    Get all available tools that can be assigned to agents.
    
    **Returns array with:**
    - **id**: Tool unique identifier
    - **tool_key**: Technical identifier
    - **display_name**: User-friendly name
    - **category**: "appointment" or "external"
    - **description**: Tool description
    """
    service = AgentActionAsyncService(db)
    return await service.get_available_tools()

@router.get(
"/knowledge-bases",
response_model=dict,
summary="List knowledge bases",
description="Get user's uploaded knowledge bases with pagination"
)
async def list_knowledge_bases(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get paginated list of user's knowledge bases.
    """
    service = KnowledgeBaseServiceAsync(db)
    return await service.list_user_knowledge_bases(
        user_id=normalize_uuid(current_user.id),
        skip=skip,
        limit=limit
    )

@router.get(
"/{agent_id}",
response_model=AgentWithActionsResponse,
summary="Get agent details",
description="Get full agent configuration including nested actions and knowledge bases"
)
async def get_agent(
agent_id: str,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> AgentWithActionsResponse:
    """
    Get complete agent configuration.
    Includes:
    - Agent settings (voice, prompts, flags)
    - Assigned tools/actions with custom config
    - Assigned knowledge bases
    - Phone configuration (if set)

    Returns 404 if agent not found or not owned by user.
    """
    # Normalize agent_id (trim whitespace, handle URL encoding, case-insensitive)
    normalized_agent_id = normalize_uuid(agent_id)
    if not normalized_agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent ID format"
        )
    
    service = AgentAsyncService(db)
    return await service.get_agent(str(normalized_agent_id), str(current_user.id), include_relations=True)

@router.put(
"/{agent_id}",
response_model=AgentResponse,
summary="Update agent",
description="Update agent configuration. All fields are optional for partial updates."
)
async def update_agent(
agent_id: str,
request: UpdateAgentRequest,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> AgentResponse:
    """
    Update agent configuration.
    All fields are optional. Only provided fields will be updated.

    Example to update only voice and system_prompt:
    json    {
        "voice": "Xb7hH8MSUJpSbSDYk0k2",
        "system_prompt": "You are Maya, a warm receptionist..."
        }
    Returns 404 if agent not found.
    Returns 403 if not authorized (agent doesn't belong to user).
    """
    # Normalize agent_id (trim whitespace, handle URL encoding, case-insensitive)
    normalized_agent_id = normalize_uuid(agent_id)
    if not normalized_agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent ID format"
        )
    
    service = AgentAsyncService(db)
    return await service.update_agent(str(normalized_agent_id), str(current_user.id), request)


@router.delete(
"/{agent_id}",
status_code=status.HTTP_204_NO_CONTENT,
summary="Delete agent",
description="Soft delete agent (can be restored from database if needed)",
responses={
    204: {
        "description": "Agent successfully deleted"
    },
    404: {
        "description": "Agent not found"
    }
}
)

async def delete_agent(
agent_id: str,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete agent (soft delete).
    
    Agent is marked as deleted but data is preserved in database.
    **Returns 404** if agent not found.
    **Returns 403** if not authorized.
    """
    # Normalize agent_id (trim whitespace, handle URL encoding, case-insensitive)
    normalized_agent_id = normalize_uuid(agent_id)
    if not normalized_agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid agent ID format"
        )
    
    service = AgentAsyncService(db)
    await service.delete_agent(str(normalized_agent_id), str(current_user.id))


# ==================== AGENT ACTIONS/TOOLS ENDPOINTS ====================

@router.post(
"/{agent_id}/actions",
response_model=dict,
status_code=status.HTTP_201_CREATED,
summary="Add tool to agent",
description="Add a tool/action to agent with optional custom configuration"
)
async def add_action_to_agent(
agent_id: str,
request: CreateAgentActionRequest,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> dict:
    """
    Add a tool/action to agent.
    - **tool_id** (required): ID of tool to add (from available tools list)
    - **custom_name** (optional): Override display name for this agent
    - **start_message** (optional): Custom message when action starts
    - **complete_message** (optional): Message when action completes
    - **failed_message** (optional): Message if action fails

    Returns 400 if tool already added to agent.
    Returns 404 if tool not found.
    """
    service = AgentActionAsyncService(db)
    return await service.add_action_to_agent(agent_id, str(current_user.id), request)


@router.put(
"/{agent_id}/actions/{action_id}",
response_model=dict,
summary="Update action config",
description="Update action configuration (custom name, messages, etc.)"
)
async def update_action(
agent_id: str,
action_id: str,
request: UpdateAgentActionRequest,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> dict:
    """
    Update action configuration.
    All fields optional for partial updates.
    """
    service = AgentActionAsyncService(db)
    return await service.update_action(agent_id, action_id, str(current_user.id), request)

@router.delete(
"/{agent_id}/actions/{action_id}",
status_code=status.HTTP_204_NO_CONTENT,
summary="Remove action from agent",
description="Remove tool/action from agent"
)
async def remove_action_from_agent(
agent_id: str,
action_id: str,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> None:
    """
    Remove action/tool from agent.
    Soft deletes the action assignment.
    """
    service = AgentActionAsyncService(db)
    await service.remove_action_from_agent(agent_id, action_id, str(current_user.id))


# ==================== KNOWLEDGE BASE ENDPOINTS ====================

@router.get(
"/knowledge-bases",
response_model=dict,
summary="List user's knowledge bases",
description="Get user's uploaded knowledge bases with pagination"
)
async def list_user_knowledge_bases(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get paginated list of user's knowledge bases.
    - **skip**: Pagination offset (default: 0)
    - **limit**: Page size (default: 20, max: 100)
    """
    service = KnowledgeBaseServiceAsync(db)
    return await service.list_user_knowledge_bases(str(current_user.id), skip, limit)


@router.get(
"/{agent_id}/knowledge-bases",
response_model=list,
summary="Get agent's knowledge bases",
description="Get all knowledge bases assigned to an agent"
)
async def get_agent_knowledge_bases(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list:
    """
    Get all knowledge bases assigned to the agent.
    Includes full knowledge base details for each assignment.
    """
    service = KnowledgeBaseServiceAsync(db)
    return await service.get_agent_knowledge_bases(agent_id, str(current_user.id))
@router.post(
"/knowledge-bases/upload",
response_model=dict,
status_code=status.HTTP_201_CREATED,
summary="Upload knowledge base",
description="Upload a knowledge base document (PDF, TXT, DOCX, XLSX, max 10MB)"
)
async def upload_knowledge_base(
file: UploadFile = File(..., description="Knowledge base file"),
document_name: str = Query(..., min_length=1, description="Display name for document"),
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> dict:
    """
    Upload a knowledge base document.
    - **file** (required): File to upload (PDF, TXT, DOCX, XLSX)
    - **document_name** (required): Display name for the document

    File size limit: 10 MB

    Returns 413 if file too large.
    Returns 400 if file type not allowed.
    """
    service = KnowledgeBaseServiceAsync(db)
    return await service.upload_knowledge_base(file, document_name, str(current_user.id))

@router.post(
"/{agent_id}/knowledge-bases",
response_model=dict,
status_code=status.HTTP_201_CREATED,
summary="Assign knowledge base to agent",
description="Assign a knowledge base document to agent for RAG"
)
async def assign_knowledge_base_to_agent(
agent_id: str,
request: AssignKnowledgeBaseRequest,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> dict:
    """
    Assign knowledge base to agent.
    - **knowledge_base_id** (required): KB ID to assign

    Returns 400 if KB already assigned.
    Returns 404 if KB not found or agent not found.
    """
    service = KnowledgeBaseServiceAsync(db)
    return await service.assign_kb_to_agent(agent_id, request.knowledge_base_id, str(current_user.id))


@router.patch(
"/{agent_id}/knowledge-bases/{kb_id}",
response_model=dict,
summary="Update knowledge base assignment",
description="Update knowledge base assignment status (enable/disable)"
)
async def update_knowledge_base_assignment(
    agent_id: str,
    kb_id: str,
    is_enabled: bool = Query(..., description="Enable or disable this knowledge base for the agent"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Update knowledge base assignment status.
    - **is_enabled** (required): Whether to enable or disable this KB for the agent
    """
    service = KnowledgeBaseServiceAsync(db)
    return await service.update_kb_assignment(agent_id, kb_id, str(current_user.id), is_enabled)

@router.delete(
"/{agent_id}/knowledge-bases/{kb_id}",
status_code=status.HTTP_204_NO_CONTENT,
summary="Remove knowledge base from agent",
description="Remove knowledge base assignment from agent"
)
async def remove_knowledge_base_from_agent(
agent_id: str,
kb_id: str,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> None:
    """
    Remove knowledge base from agent.
    The KB itself is not deleted, just the assignment.
    """
    service = KnowledgeBaseServiceAsync(db)
    await service.remove_kb_from_agent(agent_id, kb_id, str(current_user.id))

@router.delete(
"/knowledge-bases/{kb_id}",
status_code=status.HTTP_204_NO_CONTENT,
summary="Delete knowledge base",
description="Delete uploaded knowledge base"
)
async def delete_knowledge_base(
kb_id: str,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete knowledge base document.
    User must own the KB. This is a soft delete.
    """
    service = KnowledgeBaseServiceAsync(db)
    await service.delete_knowledge_base(kb_id, str(current_user.id))
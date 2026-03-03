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
description="Create a new agent with name and description. Other fields auto-populated with defaults."
)
async def create_agent(
    request: CreateAgentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AgentResponse:
    """
    Create a new agent.
    - **name** (required): Agent name
    - **description** (optional): Agent description

    Auto-populated defaults:
    - voice: "" (empty)
    - language: "EN"
    - timezone: "America/Detroit"
    - system_prompt: "" (empty)
    - first_message: "" (empty)
    - end_call_message: "" (empty)
    - voicemail_message: "" (empty)
    - And other configuration flags with standard defaults
    """
    service = AgentAsyncService(db)
    return await service.create_agent(str(current_user.id), request)

@router.get(
"",
response_model=PaginatedAgentResponse,
summary="List agents",
description="Get paginated list of agents for current user"
)
async def list_agents(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PaginatedAgentResponse:
    """
    Get list of agents for current user with pagination.
    - **skip**: Pagination offset (default: 0)
    - **limit**: Page size (default: 20, max: 100)
    """
    service = AgentAsyncService(db)
    return await service.list_agents(str(current_user.id), skip, limit)


@router.get(
"/search",
response_model=list[AgentResponse],
summary="Search agents",
description="Search agents by name or description"
)
async def search_agents(
    q: str = Query(..., min_length=1, description="Search term"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ) -> list[AgentResponse]:
    """
    Search agents by name or description.
    - **q**: Search term (required, min 1 character)
    """
    service = AgentAsyncService(db)
    return await service.search_agents(str(current_user.id), q)

@router.get(
"/tools/available",
response_model=list[dict],
summary="Get available tools",
description="Get list of all available tools for agents"
)
async def get_available_tools(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict]:
    """
    Get all available tools that can be assigned to agents.
    Returns list with:
    - id: Tool ID
    - tool_key: Technical identifier
    - display_name: User-friendly name
    - category: "appointment" or "external"
    - description: Tool description
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
    return {
        "items": [],
        "total": 0,
        "skip": skip,
        "limit": limit
    }

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
description="Soft delete agent (can be restored from database if needed)"
)

async def delete_agent(
agent_id: str,
db: AsyncSession = Depends(get_db),
current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete agent (soft delete).
    Agent is marked as deleted but data is preserved in database.
    Returns 404 if agent not found.
    Returns 403 if not authorized.
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
    # TODO: Create async version of KnowledgeBaseService
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Knowledge base upload not yet implemented"
    )

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
    # TODO: Create async version of KnowledgeBaseService
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Assign knowledge base not yet implemented"
    )

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
    # TODO: Create async version of KnowledgeBaseService
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Remove knowledge base not yet implemented"
    )

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
    User must own the KB.
    """
    # TODO: Implement knowledge base deletion
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Delete knowledge base not yet implemented"
    )
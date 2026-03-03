"""Async Agent Service"""
from typing import Optional, List
from uuid import uuid4, UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.agent import Agent
from app.repository.agent_async_repository import AgentAsyncRepository
from app.repository.agent_action_async_repository import AgentActionAsyncRepository
from app.repository.agent_tool_async_repository import AgentToolAsyncRepository
from app.schemas.agent import (
    CreateAgentRequest,
    UpdateAgentRequest,
    AgentResponse,
    AgentWithActionsResponse,
    PaginatedAgentResponse,
)
from app.config.logging import app_logger

logger = app_logger


class AgentAsyncService:
    """Async service layer for agent operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_repo = AgentAsyncRepository(db)
        self.agent_action_repo = AgentActionAsyncRepository(db)
        self.tool_repo = AgentToolAsyncRepository(db)

    async def create_agent(
        self,
        user_id: str,
        request: CreateAgentRequest
    ) -> AgentResponse:
        """Create new agent with minimal required fields"""
        logger.info(f"Creating agent for user {user_id}: {request.name}")
        
        # Convert user_id string to UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        
        agent_data = {
            'id': uuid4(),  # Create actual UUID object
            'user_id': user_uuid,  # Use UUID object
            'name': request.name,
            'description': request.description,
            'voice': '',
            'language': 'EN',
            'timezone': 'America/Detroit',
            'system_prompt': '',
            'first_message': '',
            'end_call_message': '',
            'voicemail_message': '',
            'first_message_mode': 'assistant-speaks-first',
            'end_call_function_enabled': True,
            'recording_enabled': False,
            'detect_caller_number': False,
            'multi_lingual_enabled': False,
            'is_active': True,
            'is_deleted': False,
        }
        
        logger.info(f"Agent data: {agent_data}")
        
        agent = await self.agent_repo.create(agent_data)
        
        logger.info(f"Agent created successfully: {agent.id}")
        return self._agent_to_response(agent)

    async def get_agent(
        self,
        agent_id: str,
        user_id: str,
        include_relations: bool = False
    ) -> AgentWithActionsResponse:
        """Get agent by ID with authorization check"""
        try:
            agent = await self.agent_repo.get_by_user_and_id(user_id, agent_id)
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            if include_relations:
                actions = await self.agent_action_repo.get_actions_with_tools(agent_id)
                return AgentWithActionsResponse(
                    **self._agent_to_dict(agent),
                    actions=actions
                )
            
            return self._agent_to_response(agent)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get agent"
            )

    async def list_agents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> PaginatedAgentResponse:
        """List agents for user with pagination"""
        try:
            agents, total = await self.agent_repo.get_by_user_id(user_id, skip, limit)
            
            # Calculate pagination fields
            page = (skip // limit) + 1 if limit > 0 else 1
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            
            return PaginatedAgentResponse(
                items=[self._agent_to_response(agent) for agent in agents],
                total=total,
                page=page,
                page_size=limit,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list agents"
            )

    async def search_agents(
        self,
        user_id: str,
        search_term: str
    ) -> List[AgentResponse]:
        """Search agents by name or description"""
        try:
            agents = await self.agent_repo.search_agents(user_id, search_term)
            return [self._agent_to_response(agent) for agent in agents]
            
        except Exception as e:
            logger.error(f"Error searching agents: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search agents"
            )

    async def update_agent(
        self,
        agent_id: str,
        user_id: str,
        request: UpdateAgentRequest
    ) -> AgentResponse:
        """Update agent configuration"""
        try:
            # Authorization check
            agent = await self.agent_repo.get_by_user_and_id(user_id, agent_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            # Update fields
            update_data = request.dict(exclude_unset=True)
            agent = await self.agent_repo.update(agent_id, update_data)
            await self.db.flush()
            
            logger.info(f"Agent updated: {agent_id}")
            return self._agent_to_response(agent)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update agent"
            )

    async def delete_agent(self, agent_id: str, user_id: str) -> None:
        """Soft delete agent"""
        try:
            # Authorization check
            agent = await self.agent_repo.get_by_user_and_id(user_id, agent_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            await self.agent_repo.soft_delete(agent_id)
            await self.db.flush()
            
            logger.info(f"Agent deleted: {agent_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete agent"
            )

    def _agent_to_response(self, agent: Agent) -> AgentResponse:
        """Convert agent model to response schema"""
        return AgentResponse(
            id=str(agent.id),
            user_id=str(agent.user_id),
            name=agent.name,
            description=agent.description,
            voice=agent.voice,
            language=agent.language,
            timezone=agent.timezone,
            system_prompt=agent.system_prompt,
            first_message=agent.first_message,
            end_call_message=agent.end_call_message,
            voicemail_message=agent.voicemail_message,
            first_message_mode=agent.first_message_mode,
            end_call_function_enabled=agent.end_call_function_enabled,
            recording_enabled=agent.recording_enabled,
            detect_caller_number=agent.detect_caller_number,
            multi_lingual_enabled=agent.multi_lingual_enabled,
            is_active=agent.is_active,
            created_at=agent.created_at,
            updated_at=agent.updated_at,
        )

    def _agent_to_dict(self, agent: Agent) -> dict:
        """Convert agent to dict for response building"""
        return {
            'id': str(agent.id),
            'user_id': str(agent.user_id),
            'name': agent.name,
            'description': agent.description,
            'voice': agent.voice,
            'language': agent.language,
            'timezone': agent.timezone,
            'system_prompt': agent.system_prompt,
            'first_message': agent.first_message,
            'end_call_message': agent.end_call_message,
            'voicemail_message': agent.voicemail_message,
            'first_message_mode': agent.first_message_mode,
            'end_call_function_enabled': agent.end_call_function_enabled,
            'recording_enabled': agent.recording_enabled,
            'detect_caller_number': agent.detect_caller_number,
            'multi_lingual_enabled': agent.multi_lingual_enabled,
            'is_active': agent.is_active,
            'created_at': agent.created_at,
            'updated_at': agent.updated_at,
        }

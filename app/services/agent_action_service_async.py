"""Async Agent Action Service"""
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.agent_tool import AgentTool
from app.repository.agent_async_repository import AgentAsyncRepository
from app.repository.agent_action_async_repository import AgentActionAsyncRepository
from app.repository.agent_tool_async_repository import AgentToolAsyncRepository
from app.schemas.agent_action import (
    CreateAgentActionRequest,
    UpdateAgentActionRequest,
)
from app.config.logging import app_logger

logger = app_logger


class AgentActionAsyncService:
    """Async service for managing agent actions (tools)"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_repo = AgentAsyncRepository(db)
        self.action_repo = AgentActionAsyncRepository(db)
        self.tool_repo = AgentToolAsyncRepository(db)

    async def add_action_to_agent(
        self,
        agent_id: str,
        user_id: str,
        request: CreateAgentActionRequest
    ) -> dict:
        """Add tool/action to agent"""
        logger.info(f"Adding action to agent {agent_id}, tool: {request.tool_id}")
        
        try:
            # 1. Authorization check
            if not await self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized"
                )
            
            # 2. Check tool exists
            tool = await self.tool_repo.get_by_id(request.tool_id)
            if not tool or not tool.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Tool not found"
                )
            
            # 3. Check tool not already added
            if await self.action_repo.tool_already_added(agent_id, request.tool_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tool already added to this agent"
                )
            
            # 4. Create action with UUID objects
            agent_uuid = UUID(agent_id) if isinstance(agent_id, str) else agent_id
            tool_uuid = UUID(request.tool_id) if isinstance(request.tool_id, str) else request.tool_id
            
            action_data = {
                'id': uuid4(),
                'agent_id': agent_uuid,
                'tool_id': tool_uuid,
                'custom_name': request.custom_name,
                'start_message': request.start_message,
                'complete_message': request.complete_message,
                'failed_message': request.failed_message,
                'is_enabled': True,
                'is_deleted': False,
            }
            
            action = await self.action_repo.create(action_data)
            await self.db.refresh(action)
            
            logger.info(f"Action added successfully: {action.id}")
            
            return {
                'id': str(action.id),
                'agent_id': str(action.agent_id),
                'tool_id': str(action.tool_id),
                'tool_key': tool.tool_key,
                'display_name': tool.display_name,
                'custom_name': action.custom_name,
                'is_enabled': action.is_enabled,
                'created_at': action.created_at,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding action: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add action"
            )

    async def update_action(
        self,
        agent_id: str,
        action_id: str,
        user_id: str,
        request: UpdateAgentActionRequest
    ) -> dict:
        """Update action configuration"""
        logger.info(f"Updating action {action_id} for agent {agent_id}")
        
        try:
            # 1. Authorization check
            if not await self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized"
                )
            
            # 2. Get action
            action = await self.action_repo.get_by_id(action_id)
            if not action or action.agent_id != UUID(agent_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Action not found"
                )
            
            # 3. Update fields
            update_data = {}
            if request.custom_name is not None:
                update_data['custom_name'] = request.custom_name
            if request.start_message is not None:
                update_data['start_message'] = request.start_message
            if request.complete_message is not None:
                update_data['complete_message'] = request.complete_message
            if request.failed_message is not None:
                update_data['failed_message'] = request.failed_message
            if request.is_enabled is not None:
                update_data['is_enabled'] = request.is_enabled
            
            if not update_data:
                # No fields to update
                return {
                    'id': str(action.id),
                    'agent_id': str(action.agent_id),
                    'tool_id': str(action.tool_id),
                    'custom_name': action.custom_name,
                    'is_enabled': action.is_enabled,
                }
            
            await self.action_repo.update(action.id, update_data)
            updated_action = await self.action_repo.get_by_id(action.id)
            
            logger.info(f"Action updated successfully: {action.id}")
            
            return {
                'id': str(updated_action.id),
                'agent_id': str(updated_action.agent_id),
                'tool_id': str(updated_action.tool_id),
                'custom_name': updated_action.custom_name,
                'start_message': updated_action.start_message,
                'complete_message': updated_action.complete_message,
                'failed_message': updated_action.failed_message,
                'is_enabled': updated_action.is_enabled,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating action: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update action"
            )

    async def remove_action_from_agent(
        self,
        agent_id: str,
        action_id: str,
        user_id: str
    ) -> None:
        """Remove action from agent (soft delete)"""
        logger.info(f"Removing action {action_id} from agent {agent_id}")
        
        try:
            # 1. Authorization check
            if not await self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized"
                )
            
            # 2. Get action
            action = await self.action_repo.get_by_id(action_id)
            if not action or action.agent_id != UUID(agent_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Action not found"
                )
            
            # 3. Soft delete the action
            await self.action_repo.soft_delete(action.id)
            
            logger.info(f"Action removed successfully: {action.id}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing action: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove action"
            )

    async def get_available_tools(self) -> list:
        """Get all available tools for UI selection"""
        try:
            tools = await self.tool_repo.get_active_tools()
            return [
                {
                    'id': tool.id,
                    'tool_key': tool.tool_key,
                    'display_name': tool.display_name,
                    'category': tool.category,
                    'description': tool.description,
                }
                for tool in tools
            ]
        except Exception as e:
            logger.error(f"Error getting tools: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get tools"
            )

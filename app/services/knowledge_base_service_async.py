"""Async Knowledge Base Service"""
import os
import shutil
from uuid import uuid4
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, UploadFile
from app.models.knowledge_base import KnowledgeBase
from app.repository.knowledge_base_async_repository import KnowledgeBaseAsyncRepository
from app.repository.agent_knowledge_base_async_repository import AgentKnowledgeBaseAsyncRepository
from app.repository.agent_async_repository import AgentAsyncRepository
from app.config.logging import app_logger
from app.config.settings import settings

logger = app_logger


class KnowledgeBaseServiceAsync:
    """Async service for managing knowledge bases"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'xlsx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, db: AsyncSession):
        self.db = db
        self.kb_repo = KnowledgeBaseAsyncRepository(db)
        self.agent_kb_repo = AgentKnowledgeBaseAsyncRepository(db)
        self.agent_repo = AgentAsyncRepository(db)
        self.upload_dir = Path(settings.kb_upload_dir)  # Use property method to get absolute path
        
        # Ensure upload directory exists with proper permissions
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Knowledge base upload directory ready: {self.upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory {self.upload_dir}: {str(e)}")
            raise RuntimeError(f"Cannot create KB upload directory: {str(e)}")

    async def upload_knowledge_base(
        self,
        file: UploadFile,
        document_name: str,
        user_id: str
    ) -> dict:
        """
        Upload knowledge base document.
        
        Args:
            file: Uploaded file
            document_name: Display name for document
            user_id: User uploading (for authorization)
            
        Returns:
            Created KB details
            
        Raises:
            HTTPException for validation errors
        """
        logger.info(f"Uploading KB for user {user_id}: {document_name}")
        
        try:
            # 1. Validate file extension
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File name is required"
                )
            
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in self.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}"
                )
            
            # 2. Validate file size
            content = await file.read()
            if len(content) > self.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large. Maximum 10 MB"
                )
            
            if len(content) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty"
                )
            
            # 3. Create user directory if not exists
            user_kb_dir = self.upload_dir / str(user_id)
            try:
                user_kb_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                logger.error(f"Permission denied creating directory: {user_kb_dir}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Server storage is not writable. Please contact administrator."
                )
            except Exception as e:
                logger.error(f"Error creating user KB directory: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create storage directory"
                )
            
            # 4. Save file with unique name
            unique_filename = f"{uuid4()}_{file.filename}"
            file_path = user_kb_dir / unique_filename
            
            try:
                with open(file_path, 'wb') as f:
                    f.write(content)
            except PermissionError:
                logger.error(f"Permission denied writing file: {file_path}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cannot write to storage. Check file permissions."
                )
            except Exception as e:
                logger.error(f"Error writing file: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save uploaded file"
                )
            
            # 5. Store metadata in DB
            kb_data = {
                'id': str(uuid4()),
                'document_name': document_name,
                'file_name': file.filename,
                'file_path': str(file_path),  # Store full path
                'file_type': file_ext,
                'file_size': len(content),
                'uploaded_by_user_id': user_id,
                'is_active': True,
                'is_deleted': False,
            }
            
            kb = await self.kb_repo.create(kb_data)
            await self.db.commit()
            
            logger.info(f"KB uploaded successfully: {kb.id}")
            
            return {
                'id': str(kb.id),
                'document_name': kb.document_name,
                'file_name': kb.file_name,
                'file_type': kb.file_type,
                'file_size': kb.file_size,
                'created_at': kb.created_at,
            }
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error uploading KB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

    async def assign_kb_to_agent(
        self,
        agent_id: str,
        kb_id: str,
        user_id: str
    ) -> dict:
        """
        Assign knowledge base to agent.
        
        Args:
            agent_id: Agent to assign to
            kb_id: KB to assign
            user_id: Current user (authorization)
            
        Returns:
            Assignment details
        """
        logger.info(f"Assigning KB {kb_id} to agent {agent_id}")
        
        try:
            # 1. Authorization check
            if not await self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this agent"
                )
            
            # 2. Check KB exists and user owns it
            if not await self.kb_repo.kb_belongs_to_user(kb_id, user_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base not found"
                )
            
            # 3. Check not already assigned
            if await self.agent_kb_repo.kb_assigned_to_agent(agent_id, kb_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Knowledge base already assigned to this agent"
                )
            
            # 4. Create assignment
            assignment_data = {
                'id': str(uuid4()),
                'agent_id': agent_id,
                'knowledge_base_id': kb_id,
                'is_enabled': True,
                'is_deleted': False,
            }
            
            assignment = await self.agent_kb_repo.create(assignment_data)
            await self.db.commit()
            
            logger.info(f"KB assigned successfully to agent {agent_id}")
            return {
                'id': str(assignment.id),
                'message': 'Knowledge base assigned successfully'
            }
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error assigning KB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign knowledge base"
            )

    async def remove_kb_from_agent(
        self,
        agent_id: str,
        kb_id: str,
        user_id: str
    ) -> None:
        """Remove KB from agent"""
        
        logger.info(f"Removing KB {kb_id} from agent {agent_id}")
        
        try:
            # Authorization
            if not await self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this agent"
                )
            
            success = await self.agent_kb_repo.remove_kb_from_agent(agent_id, kb_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base assignment not found"
                )
            
            await self.db.commit()
            logger.info(f"KB removed successfully from agent {agent_id}")
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error removing KB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove knowledge base"
            )

    async def list_user_knowledge_bases(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> dict:
        """List all KBs for user"""
        
        logger.info(f"Listing KBs for user {user_id}")
        
        kbs, total = await self.kb_repo.get_by_user_id(user_id, skip, limit)
        
        return {
            'items': [
                {
                    'id': str(kb.id),
                    'document_name': kb.document_name,
                    'file_name': kb.file_name,
                    'file_type': kb.file_type,
                    'file_size': kb.file_size,
                    'created_at': kb.created_at,
                }
                for kb in kbs
            ],
            'total': total,
            'page': (skip // limit) + 1 if limit > 0 else 1,
            'page_size': limit,
            'total_pages': (total + limit - 1) // limit if limit > 0 else 1,
        }

    async def get_agent_knowledge_bases(
        self,
        agent_id: str,
        user_id: str
    ) -> list:
        """Get all KBs assigned to agent"""
        
        logger.info(f"Getting KBs for agent {agent_id}")
        
        try:
            # Authorization check
            if not await self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this agent"
                )
            
            agent_kbs = await self.agent_kb_repo.get_agent_kbs_with_details(agent_id)
            
            return [
                {
                    'id': str(akb.id),
                    'knowledge_base': {
                        'id': str(akb.knowledge_base.id),
                        'document_name': akb.knowledge_base.document_name,
                        'file_name': akb.knowledge_base.file_name,
                        'file_type': akb.knowledge_base.file_type,
                        'file_size': akb.knowledge_base.file_size,
                        'created_at': akb.knowledge_base.created_at,
                    },
                    'is_enabled': akb.is_enabled,
                    'created_at': akb.created_at,
                }
                for akb in agent_kbs
            ]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting agent KBs: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve knowledge bases"
            )

    async def delete_knowledge_base(
        self,
        kb_id: str,
        user_id: str
    ) -> None:
        """Delete knowledge base"""
        
        logger.info(f"Deleting KB {kb_id} for user {user_id}")
        
        try:
            # Check ownership
            if not await self.kb_repo.kb_belongs_to_user(kb_id, user_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base not found"
                )
            
            # Soft delete
            success = await self.kb_repo.soft_delete(kb_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base not found"
                )
            
            await self.db.commit()
            logger.info(f"KB deleted successfully: {kb_id}")
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting KB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete knowledge base"
            )

    async def update_kb_assignment(
        self,
        agent_id: str,
        kb_id: str,
        user_id: str,
        is_enabled: bool
    ) -> dict:
        """Update knowledge base assignment status"""
        
        logger.info(f"Updating KB {kb_id} assignment for agent {agent_id}")
        
        try:
            # Authorization check
            if not await self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this agent"
                )
            
            # Get assignment
            agent_kbs = await self.agent_kb_repo.get_by_agent_id(agent_id)
            assignment = None
            for akb in agent_kbs:
                if str(akb.knowledge_base_id) == kb_id:
                    assignment = akb
                    break
            
            if not assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base assignment not found"
                )
            
            # Update
            assignment.is_enabled = is_enabled
            await self.db.flush()
            await self.db.commit()
            
            logger.info(f"KB assignment updated successfully")
            return {
                'id': str(assignment.id),
                'is_enabled': is_enabled,
                'message': 'Knowledge base assignment updated'
            }
            
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating KB assignment: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update knowledge base"
            )

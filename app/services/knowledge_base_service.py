import os
import shutil
from uuid import uuid4
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, UploadFile
from app.models.knowledge_base import KnowledgeBase
from app.repository.knowledge_base_repository import KnowledgeBaseRepository
from app.repository.agent_knowledge_base_repository import AgentKnowledgeBaseRepository
from app.repository.agent_async_repository import AgentAsyncRepository
from app.config.logging import app_logger
logger = app_logger
from app.config.settings import settings

class KnowledgeBaseService:
    """Service for managing knowledge bases"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx', 'xlsx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def __init__(self, db: Session):
        self.db = db
        self.kb_repo = KnowledgeBaseRepository(db)
        self.agent_kb_repo = AgentKnowledgeBaseRepository(db)
        self.agent_repo = AgentRepository(db)
        self.upload_dir = Path(settings.KB_UPLOAD_DIR)  # "app/knowledge_base"

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
            
            # 3. Create user directory if not exists
            user_kb_dir = self.upload_dir / user_id
            user_kb_dir.mkdir(parents=True, exist_ok=True)
            
            # 4. Save file with unique name
            unique_filename = f"{uuid4()}_{file.filename}"
            file_path = user_kb_dir / unique_filename
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
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
            
            kb = self.kb_repo.create(kb_data)
            self.db.commit()
            
            logger.info(f"KB uploaded successfully: {kb.id}")
            
            return {
                'id': kb.id,
                'document_name': kb.document_name,
                'file_name': kb.file_name,
                'file_type': kb.file_type,
                'file_size': kb.file_size,
                'created_at': kb.created_at,
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error uploading KB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file"
            )

    def assign_kb_to_agent(
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
            if not self.agent_repo.agent_exists_for_user(user_id, agent_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized"
                )
            
            # 2. Check KB exists and user owns it
            if not self.kb_repo.kb_belongs_to_user(kb_id, user_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Knowledge base not found"
                )
            
            # 3. Check not already assigned
            if self.agent_kb_repo.kb_assigned_to_agent(agent_id, kb_id):
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
            
            assignment = self.agent_kb_repo.create(assignment_data)
            self.db.commit()
            
            logger.info(f"KB assigned successfully")
            return {'message': 'Knowledge base assigned successfully'}
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error assigning KB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign knowledge base"
            )

    def remove_kb_from_agent(
        self,
        agent_id: str,
        kb_id: str,
        user_id: str
    ) -> dict:
        """Remove KB from agent"""
        
        logger.info(f"Removing KB {kb_id} from agent {agent_id}")
        
        # Authorization
        if not self.agent_repo.agent_exists_for_user(user_id, agent_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized"
            )
        
        try:
            success = self.agent_kb_repo.remove_kb_from_agent(agent_id, kb_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found"
                )
            
            self.db.commit()
            return {'message': 'Knowledge base removed successfully'}
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error removing KB: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove knowledge base"
            )

    def list_user_knowledge_bases(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> dict:
        """List all KBs for user"""
        
        logger.info(f"Listing KBs for user {user_id}")
        
        kbs, total = self.kb_repo.get_by_user_id(user_id, skip, limit)
        
        return {
            'items': [
                {
                    'id': kb.id,
                    'document_name': kb.document_name,
                    'file_name': kb.file_name,
                    'file_type': kb.file_type,
                    'file_size': kb.file_size,
                    'created_at': kb.created_at,
                }
                for kb in kbs
            ],
            'total': total,
            'page': (skip // limit) + 1,
            'page_size': limit,
            'total_pages': (total + limit - 1) // limit,
        }
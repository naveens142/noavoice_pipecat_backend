from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.agent_knowledge_base import AgentKnowledgeBase
from app.repository.base_repository import BaseRepository


class AgentKnowledgeBaseRepository(BaseRepository[AgentKnowledgeBase]):
    """Agent Knowledge Base repository"""
    
    def __init__(self, db_session: Session):
        super().__init__(db_session, AgentKnowledgeBase)
    
    def get_by_agent_id(self, agent_id: str) -> List[AgentKnowledgeBase]:
        """Get all KBs for agent"""
        return self.db.query(AgentKnowledgeBase).filter(
            and_(
                AgentKnowledgeBase.agent_id == agent_id,
                AgentKnowledgeBase.is_deleted == False
            )
        ).all()
    
    def kb_assigned_to_agent(self, agent_id: str, kb_id: str) -> bool:
        """Check if KB already assigned to agent"""
        return self.db.query(AgentKnowledgeBase).filter(
            and_(
                AgentKnowledgeBase.agent_id == agent_id,
                AgentKnowledgeBase.knowledge_base_id == kb_id,
                AgentKnowledgeBase.is_deleted == False
            )
        ).first() is not None
    
    def remove_kb_from_agent(self, agent_id: str, kb_id: str) -> bool:
        """Remove KB from agent (soft delete)"""
        kb_assignment = self.db.query(AgentKnowledgeBase).filter(
            and_(
                AgentKnowledgeBase.agent_id == agent_id,
                AgentKnowledgeBase.knowledge_base_id == kb_id
            )
        ).first()
        
        if not kb_assignment:
            return False
        
        kb_assignment.is_deleted = True
        self.db.flush()
        return True
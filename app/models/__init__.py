"""Import all models to register them with Base.metadata"""
from app.models.base import Base, BaseModel
from app.models.booking import Booking
from app.models.agent import Agent
from app.models.agent_action import AgentAction
from app.models.agent_tool import AgentTool
from app.models.knowledge_base import KnowledgeBase
from app.models.agent_knowledge_base import AgentKnowledgeBase
from app.models.agent_phone import AgentPhone

__all__ = [
    "Base", 
    "BaseModel",
    "Booking",
    'Agent',
    'AgentAction',
    'AgentTool',
    'KnowledgeBase',
    'AgentKnowledgeBase',
    'AgentPhone'
]

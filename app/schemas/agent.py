from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


# Create Request
class CreateAgentRequest(BaseModel):
    """Create agent request - minimal fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, max_length=5000, description="Agent description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Customer Support Agent",
                "description": "AI-powered agent to handle customer inquiries and support tickets"
            }
        }


# Update Request
class UpdateAgentRequest(BaseModel):
    """Update agent request - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    voice: Optional[str] = Field(None, max_length=255)
    language: Optional[str] = Field(None, min_length=2, max_length=10)
    timezone: Optional[str] = Field(None, max_length=100)
    system_prompt: Optional[str] = Field(None)
    first_message: Optional[str] = Field(None)
    end_call_message: Optional[str] = Field(None)
    voicemail_message: Optional[str] = Field(None)
    first_message_mode: Optional[str] = Field(None, max_length=50)
    end_call_function_enabled: Optional[bool] = None
    recording_enabled: Optional[bool] = None
    detect_caller_number: Optional[bool] = None
    multi_lingual_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Customer Support Agent",
                "description": "Enhanced customer support with AI capabilities",
                "voice": "Xb7hH8MSUJpSbSDYk0k2",
                "language": "EN",
                "timezone": "America/New_York",
                "system_prompt": "You are Maya, a warm and professional customer support representative. Be helpful, polite, and always aim to resolve customer issues quickly.",
                "first_message": "Hello! Thank you for calling. My name is Maya. How can I help you today?",
                "end_call_message": "Thank you for calling! Have a wonderful day!",
                "voicemail_message": "Thank you for calling. Please leave your name and number, and we'll get back to you shortly.",
                "first_message_mode": "assistant-speaks-first",
                "end_call_function_enabled": True,
                "recording_enabled": True,
                "detect_caller_number": True,
                "multi_lingual_enabled": False,
                "is_active": True
            }
        }


# Response DTO
class AgentResponse(BaseModel):
    """Agent response - full details"""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    voice: Optional[str]
    language: str
    timezone: str
    system_prompt: Optional[str]
    first_message: Optional[str]
    end_call_message: Optional[str]
    voicemail_message: Optional[str]
    first_message_mode: str
    end_call_function_enabled: bool
    recording_enabled: bool
    detect_caller_number: bool
    multi_lingual_enabled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Agent with nested relations
class AgentWithActionsResponse(AgentResponse):
    """Agent response with nested actions and knowledge bases"""
    actions: List['AgentActionResponse'] = []
    knowledge_bases: List['KnowledgeBaseResponse'] = []
    phone: Optional['AgentPhoneResponse'] = None


# Pagination
class PaginatedAgentResponse(BaseModel):
    """Paginated agents response"""
    items: List[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AgentActionResponse(BaseModel):
    """Agent action response"""
    id: str
    agent_id: str
    tool_id: str
    tool_key: str
    display_name: str
    custom_name: Optional[str]
    start_message: Optional[str]
    complete_message: Optional[str]
    failed_message: Optional[str]
    is_enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeBaseResponse(BaseModel):
    """Knowledge base response"""
    id: str
    document_name: str
    file_name: str
    file_type: str
    file_size: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentPhoneResponse(BaseModel):
    """Agent phone response"""
    id: str
    phone_number: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
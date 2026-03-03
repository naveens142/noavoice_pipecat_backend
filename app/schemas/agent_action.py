from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class CreateAgentActionRequest(BaseModel):
    """Create/Add action to agent"""
    tool_id: str = Field(..., description="Tool ID to add")
    custom_name: Optional[str] = Field(None, max_length=255)
    start_message: Optional[str] = Field(None)
    complete_message: Optional[str] = Field(None)
    failed_message: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_id": "booking_tool_uuid",
                "custom_name": "Book Appointment",
                "start_message": "Let me book that for you..."
            }
        }


class UpdateAgentActionRequest(BaseModel):
    """Update action configuration"""
    custom_name: Optional[str] = Field(None, max_length=255)
    start_message: Optional[str] = Field(None)
    complete_message: Optional[str] = Field(None)
    failed_message: Optional[str] = Field(None)
    is_enabled: Optional[bool] = None


class AgentActionResponse(BaseModel):
    """Agent action response"""
    id: str
    agent_id: str
    tool_id: str
    custom_name: Optional[str]
    start_message: Optional[str]
    complete_message: Optional[str]
    failed_message: Optional[str]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
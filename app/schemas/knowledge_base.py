from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class UploadKnowledgeBaseRequest(BaseModel):
    """Upload KB document request"""
    document_name: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., pattern="^(pdf|txt|docx|xlsx)$")  # Validate file type
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_name": "Medical Procedures Guide",
                "file_type": "pdf"
            }
        }


class KnowledgeBaseResponse(BaseModel):
    """Knowledge base response"""
    id: str
    document_name: str
    file_name: str
    file_path: str
    file_type: str
    file_size: Optional[int]
    uploaded_by_user_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AssignKnowledgeBaseRequest(BaseModel):
    """Assign KB to agent"""
    knowledge_base_id: str = Field(..., description="KB ID to assign")
    
    class Config:
        json_schema_extra = {
            "example": {
                "knowledge_base_id": "kb_uuid_here"
            }
        }
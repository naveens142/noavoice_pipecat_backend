"""UUID handling utilities"""
from uuid import UUID
from typing import Union
from urllib.parse import unquote


def normalize_uuid(value: Union[str, UUID]) -> Union[UUID, None]:
    """
    Normalize UUID from string or UUID object.
    
    Handles:
    - Leading/trailing whitespace
    - URL encoding (spaces as %20, etc.)
    - Case sensitivity (UUIDs are case-insensitive)
    
    Args:
        value: UUID string or UUID object
        
    Returns:
        UUID object or None if invalid
        
    Examples:
        normalize_uuid("  83b45007-a920-4cd2-9cfc-81e54ae54884  ")
        normalize_uuid("83B45007-A920-4CD2-9CFC-81E54AE54884")
        normalize_uuid(UUID(...))
    """
    if isinstance(value, UUID):
        return value
    
    if value is None:
        return None
    
    try:
        # Convert to string and normalize
        value_str = str(value).strip()
        
        # URL decode if needed (handles %20 and other encoded characters)
        value_str = unquote(value_str).strip()
        
        # Convert to UUID - case insensitive
        return UUID(value_str)
    except (ValueError, TypeError, AttributeError):
        return None

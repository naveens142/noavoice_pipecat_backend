import logging 
from fastapi import APIRouter, HTTPException, UploadFile
from app.utils.redis_client import get_redis
from dotenv import load_dotenv
import os,pypdf

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/redis", tags=["redis"])

@router.get("/redis-test", responses={
    200: {
        "description": "Redis connection successful",
        "content": {
            "application/json": {
                "example": {
                    "redis_value": "Hello Redis"
                }
            }
        }
    },
    503: {
        "description": "Redis connection failed",
        "content": {
            "application/json": {
                "example": {"detail": "Redis connection failed. Check REDIS_URL in settings."}
            }
        }
    }
})
async def redis_test():
    """
    Test Redis connectivity.
    
    **Description:**
    Performs a simple Redis read/write test to verify the connection.
    Useful for health checks and debugging Redis configuration issues.
    
    **Returns:**
    - **redis_value**: The value retrieved from Redis (should be "Hello Redis")
    
    **Use case:** Verify Redis is properly configured and accessible
    """
    try:
        redis = await get_redis()
        await redis.set("test_key", "Hello Redis")
        value = await redis.get("test_key")
        return {"redis_value": value}
    except Exception as e:
        logger.error(f"Redis connection error: {str(e)}")
        raise HTTPException(
            status_code=503, 
            detail=f"Redis connection failed. Check REDIS_URL in settings. Error: {str(e)}"
        )
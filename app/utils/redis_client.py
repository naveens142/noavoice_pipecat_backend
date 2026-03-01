"""
Redis client for storing OAuth state and nonces.

WHY REDIS for OAuth state?
- State param must survive across HTTP requests (stateless FastAPI)
- Must expire automatically (TTL) — stale states = security risk
- Must be one-time use — replay attacks
- Must be fast — auth redirects are latency-sensitive

We use redis for:
  1. oauth_state:{state}  → CSRF protection (5 min TTL)
  2. oauth_nonce:{nonce}  → OIDC replay attack prevention (5 min TTL)
"""
import redis.asyncio as aioredis
from app.config.settings import get_settings

settings = get_settings()

# Module-level client — created once, reused across requests
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create Redis connection pool."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection — called on app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


# ── OAuth State Helpers ───────────────────────────────────────────────────────

STATE_TTL = 300       # 5 minutes — must complete OAuth within this window
NONCE_TTL = 300       # 5 minutes — same window for OIDC nonce


async def store_oauth_state(state: str) -> None:
    """
    Store OAuth state with TTL.
    The value '1' is a placeholder — we only care about key existence.
    """
    r = await get_redis()
    await r.setex(f"oauth_state:{state}", STATE_TTL, "1")


async def verify_and_consume_state(state: str) -> bool:
    """
    Atomically check + delete state.
    Returns True if valid (existed), False if invalid/expired/already used.

    ATOMIC via Redis DEL return value:
    - DEL returns 1 if key existed and was deleted
    - DEL returns 0 if key did not exist
    This prevents race conditions in concurrent requests.
    """
    r = await get_redis()
    deleted = await r.delete(f"oauth_state:{state}")
    return deleted == 1  # 1 = existed and deleted, 0 = never existed or already used


async def store_nonce(nonce: str) -> None:
    """Store OIDC nonce — prevents id_token replay attacks."""
    r = await get_redis()
    await r.setex(f"oauth_nonce:{nonce}", NONCE_TTL, "1")


async def verify_and_consume_nonce(nonce: str) -> bool:
    """Atomically verify and consume nonce — same pattern as state."""
    r = await get_redis()
    deleted = await r.delete(f"oauth_nonce:{nonce}")
    return deleted == 1
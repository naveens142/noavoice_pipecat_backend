"""
Google JWK (JSON Web Key) Cache

WHY WE NEED THIS:
Google signs id_tokens with their PRIVATE RSA key (RS256).
To verify the signature, we need Google's PUBLIC keys.
Google publishes these at a JWK URI (from the OIDC discovery document).

CACHING STRATEGY:
- Google rotates their keys periodically
- We cache keys in memory to avoid fetching on every request
- Cache respects the HTTP Cache-Control / max-age headers Google sends
- On cache miss or expiry → re-fetch from Google
- On kid (key ID) mismatch → force re-fetch (key rotation handling)

This is production-critical:
  ❌ Fetching JWK on every request = latency + Google rate limits
  ❌ Never refreshing = broken verification after key rotation
  ✅ TTL-based cache with forced refresh on unknown kid
"""
import time
import httpx
from authlib.jose.rfc7517 import KeySet, JsonWebKey
from app.config.settings import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# In-memory cache
_jwk_cache: KeySet | None = None
_jwk_cache_expiry: float = 0
_jwk_uri: str | None = None

# Default cache TTL — 1 hour. We re-fetch before expiry automatically.
JWK_CACHE_TTL_SECONDS = 3600


async def _fetch_oidc_discovery() -> dict:
    """Fetch Google's OIDC discovery document."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(settings.GOOGLE_DISCOVERY_URL)
        resp.raise_for_status()
        return resp.json()


async def _fetch_jwk_set(jwks_uri: str) -> KeySet:
    """Fetch Google's public JWK set and parse it."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(jwks_uri)
        resp.raise_for_status()

        # Try to respect Google's cache headers
        global _jwk_cache_expiry
        cache_control = resp.headers.get("Cache-Control", "")
        if "max-age=" in cache_control:
            try:
                max_age = int(cache_control.split("max-age=")[1].split(",")[0].strip())
                _jwk_cache_expiry = time.time() + max_age
            except (ValueError, IndexError):
                _jwk_cache_expiry = time.time() + JWK_CACHE_TTL_SECONDS
        else:
            _jwk_cache_expiry = time.time() + JWK_CACHE_TTL_SECONDS

        # Parse JWKS and create KeySet
        jwks_data = resp.json()
        keys = [JsonWebKey.import_key(key_data) for key_data in jwks_data.get("keys", [])]
        return KeySet(keys)


async def get_google_jwk_set(force_refresh: bool = False) -> KeySet:
    """
    Get Google's JWK set, using cache when possible.

    Args:
        force_refresh: bypass cache — used when we encounter an unknown kid
                       (signals Google rotated their keys)
    """
    global _jwk_cache, _jwk_cache_expiry, _jwk_uri

    now = time.time()
    cache_valid = _jwk_cache is not None and now < _jwk_cache_expiry

    if cache_valid and not force_refresh:
        return _jwk_cache

    logger.info("Fetching Google JWK set (force_refresh=%s)", force_refresh)

    # Fetch JWK URI from discovery document if we don't have it yet
    if not _jwk_uri:
        discovery = await _fetch_oidc_discovery()
        _jwk_uri = discovery["jwks_uri"]

    _jwk_cache = await _fetch_jwk_set(_jwk_uri)
    logger.info("Google JWK set cached, expires in %ds", int(_jwk_cache_expiry - now))
    return _jwk_cache


async def get_google_oidc_config() -> dict:
    """
    Fetch Google's OIDC discovery document.
    Contains: authorization_endpoint, token_endpoint, userinfo_endpoint, jwks_uri, etc.
    """
    return await _fetch_oidc_discovery()
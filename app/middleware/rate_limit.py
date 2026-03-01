"""
Rate limiting for auth endpoints.

WHY RATE LIMIT AUTH ROUTES:
- /login: prevent brute force password attacks
- /register: prevent spam account creation
- /refresh: prevent token farming
- /google: prevent redirect spam

Uses slowapi (Starlette/FastAPI wrapper around limits library).
Limits are per-IP by default.

Production consideration:
If behind a load balancer/proxy, ensure you're reading the real client IP
from X-Forwarded-For or X-Real-IP headers, not the proxy's IP.
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_real_ip(request: Request) -> str:
    """
    Extract real client IP.
    Checks X-Forwarded-For first (set by proxies/load balancers),
    falls back to direct connection IP.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can be "client, proxy1, proxy2" — take the first (client)
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


# Global limiter instance — used as decorator on routes
limiter = Limiter(key_func=_get_real_ip)
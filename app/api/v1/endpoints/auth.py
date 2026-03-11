"""
Auth endpoints — production hardened.

Endpoints:
  POST /auth/register         — local registration
  POST /auth/login            — local login → JWT tokens
  POST /auth/refresh          — refresh access token
  POST /auth/logout           — revoke refresh token
  GET  /auth/google           — start Google OIDC flow
  GET  /auth/google/callback  — Google callback → JWT tokens → redirect to UI
  GET  /auth/me               — get current user info

Security measures per endpoint documented inline.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.settings import get_settings
from app.integrations.google.oauth import google_oidc
from app.middleware.rate_limit import limiter
from app.models.user import AuthProvider
from app.schemas.auth import (
    LoginRequest, RefreshTokenRequest, RegisterRequest,
    TokenResponse, UserResponse,
)
from app.services.auth import AuthService
from app.utils.dependencies import get_current_user

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ─── Local Registration ───────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register with email and password",
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "picture": None,
                        "provider": "local",
                        "is_verified": False,
                        "created_at": "2026-03-11T08:42:33.011000Z",
                        "last_login": None
                    }
                }
            }
        },
        409: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {"detail": "Email already registered"}
                }
            }
        },
        400: {
            "description": "Invalid password or input",
            "content": {
                "application/json": {
                    "example": {"detail": "Password must contain at least one uppercase letter"}
                }
            }
        }
    }
)
@limiter.limit("3/minute")   # prevent account spam
async def register(
    request: Request,           # required by slowapi
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user with email and password.

    **Rate limit:** 3 requests/minute per IP.
    
    **Password requirements:**
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 digit
    """
    try:
        user = await AuthService.register(
            db=db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return user


# ─── Local Login ──────────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
    responses={
        200: {
            "description": "Successfully authenticated",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDE2MDQ1NTMsImlhdCI6MTc0MTYwMzY1M30.ABC123XYZ",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3NDIyMDg0NTN9.DEF456UVW",
                        "token_type": "bearer",
                        "expires_in": 900
                    }
                }
            }
        },
        401: {
            "description": "Invalid email or password",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid email or password"}
                }
            }
        },
        429: {
            "description": "Too many login attempts (rate limited)",
            "content": {
                "application/json": {
                    "example": {"detail": "Rate limit exceeded"}
                }
            }
        }
    }
)
@limiter.limit("5/minute")   # brute force protection
async def login(
    request: Request,
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email and password.

    **Returns:** JWT access token (15 min) + refresh token (7 days)
    
    **Rate limit:** 5 requests/minute per IP
    
    **Security:** Account locks after 5 failed attempts for 15 minutes.
    """
    try:
        user, access_token, refresh_token = await AuthService.login(
            db=db,
            email=payload.email,
            password=payload.password,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as e:
        # Always 401 — never 404 (user enumeration prevention)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ─── Token Refresh ────────────────────────────────────────────────────────────

async def _refresh_token_impl(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession,
):
    """
    Internal implementation for token refresh.
    Used by both /refresh and /refresh-token endpoints.
    """
    try:
        access_token, new_refresh = await AuthService.refresh_tokens(
            db=db,
            raw_refresh_token=payload.refresh_token,
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    responses={
        200: {
            "description": "New tokens issued",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 900
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid refresh token"}
                }
            }
        }
    }
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a refresh token for new access + refresh tokens.

    **Security:** Old refresh token is immediately invalidated (rotation).
    If a stolen/reused token is detected, ALL sessions are revoked.
    """
    return await _refresh_token_impl(request, payload, db)


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    summary="Refresh access token (alias endpoint)",
    responses={
        200: {
            "description": "New tokens issued",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "expires_in": 900
                    }
                }
            }
        }
    }
)
@limiter.limit("10/minute")
async def refresh_token_alias(
    request: Request,
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a refresh token for new access + refresh tokens.
    
    This is an alias for /refresh endpoint for backwards compatibility.

    **Security:** Old refresh token is immediately invalidated (rotation).
    If a stolen/reused token is detected, ALL sessions are revoked.
    """
    return await _refresh_token_impl(request, payload, db)


# ─── Logout ───────────────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — revoke refresh token",
    responses={
        204: {
            "description": "Successfully logged out"
        }
    }
)
async def logout(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke the refresh token.

    **Note:** Access token remains valid until its 15-min expiry.
    UI should discard both tokens on logout.
    """
    await AuthService.logout(db, payload.refresh_token)


# ─── Google OIDC ──────────────────────────────────────────────────────────────

@router.get(
    "/google",
    summary="Start Google OAuth login",
    include_in_schema=True,
)
@limiter.limit("20/minute")
async def google_login(request: Request):
    """
    Redirect browser to Google's OAuth consent screen.

    Generates a unique state (CSRF token) and nonce (replay prevention),
    stores them in Redis with 5-minute TTL, then redirects to Google.

    UI should navigate to this URL — NOT call it via fetch/axios.
    """
    try:
        auth_url, state, nonce = await google_oidc.build_authorization_url()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not reach Google: {e}",
        )

    return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)


@router.get(
    "/google/callback",
    summary="Google OAuth callback",
    include_in_schema=True,
)
async def google_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="State for CSRF verification"),
    error: str = Query(None, description="Error from Google (user denied access)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Google redirects here after user authenticates.

    Security checks (in order):
    1. Check for error param (user denied access)
    2. Verify state (CSRF protection)
    3. Exchange code for id_token
    4. Verify id_token signature (RS256 + Google JWK)
    5. Validate all OIDC claims (iss, aud, exp, nonce)
    6. Create or find user

    Redirects to frontend with tokens in URL fragment (#).
    URL fragment is NOT sent to server — safer than query params.
    """
    # ── User denied access ────────────────────────────────────────────────
    if error:
        error_redirect = f"{settings.FRONTEND_URL}/auth/error?reason=access_denied"
        return RedirectResponse(url=error_redirect, status_code=status.HTTP_302_FOUND)

    # ── Process OIDC callback ─────────────────────────────────────────────
    try:
        # This does: state verification, code exchange, id_token verification
        userinfo = await google_oidc.handle_callback(code=code, state=state)
    except ValueError as e:
        # Security violation (CSRF, replay, invalid token) — redirect to error page
        error_redirect = f"{settings.FRONTEND_URL}/auth/error?reason=auth_failed"
        return RedirectResponse(url=error_redirect, status_code=status.HTTP_302_FOUND)
    except Exception as e:
        error_redirect = f"{settings.FRONTEND_URL}/auth/error?reason=server_error"
        return RedirectResponse(url=error_redirect, status_code=status.HTTP_302_FOUND)

    # ── Create or find user ───────────────────────────────────────────────
    try:
        user, access_token, refresh_token = await AuthService.oauth_authenticate(
            db=db,
            provider=AuthProvider.GOOGLE,
            provider_id=userinfo["sub"],
            email=userinfo["email"],
            full_name=userinfo.get("name"),
            picture=userinfo.get("picture"),
            user_agent=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
        )
    except ValueError as e:
        error_redirect = f"{settings.FRONTEND_URL}/auth/error?reason=account_error"
        return RedirectResponse(url=error_redirect, status_code=status.HTTP_302_FOUND)

    # ── Redirect to frontend with tokens ─────────────────────────────────
    # Using URL FRAGMENT (#) — fragment is never sent to server, stays in browser
    # This is safer than query params which appear in server logs
    from urllib.parse import urlencode

    params = urlencode({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    })

    frontend_redirect = f"{settings.FRONTEND_URL}/auth/callback#{params}"
    return RedirectResponse(url=frontend_redirect, status_code=status.HTTP_302_FOUND)


# ─── Current User ─────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
    responses={
        200: {
            "description": "Current user profile",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "john.doe@example.com",
                        "full_name": "John Doe",
                        "picture": "https://example.com/avatar.jpg",
                        "provider": "local",
                        "is_verified": True,
                        "created_at": "2026-03-07T08:42:33.011000Z",
                        "last_login": "2026-03-11T10:15:22.000000Z"
                    }
                }
            }
        },
        401: {
            "description": "Invalid or expired token",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid or expired token"}
                }
            }
        }
    }
)
async def get_me(current_user=Depends(get_current_user)):
    """
    Returns the authenticated user's profile.
    
    **Authentication:** Required (Bearer token)
    """
    return current_user
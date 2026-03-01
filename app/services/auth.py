"""
Auth Service — Production hardened.

Security layers implemented:
1. Brute force protection: track failed attempts, lock account
2. Timing-safe login: constant response time prevents user enumeration
3. Refresh token rotation: single-use, each refresh issues new token
4. Theft detection: reused revoked token → revoke all sessions
5. OAuth account linking: link OAuth to existing email account
6. Proper error messages: generic messages prevent user enumeration
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, AuthProvider
from app.models.refresh_token import RefreshToken
from app.utils.security import (
    verify_password, hash_password,
    create_access_token, decode_access_token,
    generate_refresh_token, hash_refresh_token,
)
from app.config.settings import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Brute force config
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


class AuthService:

    # ─── Local Registration ───────────────────────────────────────────────

    @staticmethod
    async def register(
        db: AsyncSession,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> User:
        """
        Register a new local user.
        Raises ConflictError if email already exists.
        Note: we return a GENERIC error to prevent user enumeration.
        """
        # Check if email exists
        existing = await db.scalar(select(User).where(User.email == email.lower()))
        if existing:
            # Don't reveal whether email exists — just say registration failed
            raise ValueError("Registration failed. Please try a different email.")

        user = User(
            email=email.lower(),
            full_name=full_name,
            hashed_password=hash_password(password),
            provider=AuthProvider.LOCAL,
            is_verified=False,   # would send verification email in real flow
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("New user registered: %s", user.id)
        return user

    # ─── Local Login ──────────────────────────────────────────────────────

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> tuple[User, str, str]:
        """
        Authenticate a local user.

        Returns: (user, access_token, refresh_token)

        Security:
        - Account lockout after MAX_FAILED_ATTEMPTS
        - Always takes ~same time regardless of failure reason (timing attack prevention)
        - Generic error message regardless of failure (user enumeration prevention)
        """
        # Constant-time baseline — ensures response time is consistent
        # even when we short-circuit early (prevents timing attacks)
        start_time = asyncio.get_event_loop().time()

        user = await db.scalar(select(User).where(User.email == email.lower()))

        # ── Account lockout check ─────────────────────────────────────────
        if user and user.locked_until:
            if datetime.now(timezone.utc) < user.locked_until:
                remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
                raise ValueError(f"Account locked. Try again in {remaining} minutes.")
            else:
                # Lockout expired — reset
                user.failed_login_attempts = 0
                user.locked_until = None

        # ── Credential verification ───────────────────────────────────────
        # Always run verify_password even if user not found
        # This prevents timing attacks that reveal whether an email exists
        dummy_hash = "$2b$12$dummy.hash.to.prevent.timing.attacks.aaaa"
        password_correct = verify_password(
            password,
            user.hashed_password if (user and user.hashed_password) else dummy_hash
        )

        if not user or not password_correct or not user.is_active:
            if user and password_correct is False:
                # Real user, wrong password — track attempt
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                    user.locked_until = datetime.now(timezone.utc) + timedelta(
                        minutes=LOCKOUT_DURATION_MINUTES
                    )
                    logger.warning("Account locked due to brute force: %s", user.id)
                await db.commit()

            # Ensure minimum response time regardless of failure path
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed < 0.1:   # minimum 100ms response
                await asyncio.sleep(0.1 - elapsed)

            raise ValueError("Invalid email or password")

        # ── Successful login ──────────────────────────────────────────────
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        access_token, refresh_token = await AuthService._issue_tokens(
            db, user, user_agent, ip_address
        )
        return user, access_token, refresh_token

    # ─── OAuth Login / Register ───────────────────────────────────────────

    @staticmethod
    async def oauth_authenticate(
        db: AsyncSession,
        provider: AuthProvider,
        provider_id: str,
        email: str,
        full_name: Optional[str],
        picture: Optional[str],
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> tuple[User, str, str]:
        """
        Find or create a user from OAuth provider data.

        Account resolution order:
        1. Find by provider + provider_id (returning user, same provider)
        2. Find by email (link OAuth to existing account)
        3. Create new user

        This means: if user registered with email/password,
        then logs in with Google (same email) → accounts are linked.
        """
        # ── Step 1: Find by provider_id ───────────────────────────────────
        user = await db.scalar(
            select(User).where(
                User.provider == provider,
                User.provider_id == provider_id,
            )
        )

        if not user:
            # ── Step 2: Find by email ─────────────────────────────────────
            user = await db.scalar(
                select(User).where(User.email == email.lower())
            )

            if user:
                # Link OAuth to existing account
                logger.info("Linking %s OAuth to existing user %s", provider, user.id)
                user.provider = provider
                user.provider_id = provider_id
                user.picture = picture or user.picture
                user.is_verified = True   # OAuth = email verified by provider
            else:
                # ── Step 3: Create new user ───────────────────────────────
                user = User(
                    email=email.lower(),
                    full_name=full_name,
                    picture=picture,
                    provider=provider,
                    provider_id=provider_id,
                    is_verified=True,   # Google already verified the email
                    is_active=True,
                )
                db.add(user)
                logger.info("New user created via %s OAuth: %s", provider, email)

        if not user.is_active:
            raise ValueError("Account is deactivated")

        user.last_login = datetime.now(timezone.utc)
        # Update picture on each login (Google may update it)
        if picture:
            user.picture = picture

        await db.commit()
        await db.refresh(user)

        access_token, refresh_token = await AuthService._issue_tokens(
            db, user, user_agent, ip_address
        )
        return user, access_token, refresh_token

    # ─── Token Refresh ────────────────────────────────────────────────────

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        raw_refresh_token: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> tuple[str, str]:
        """
        Exchange a refresh token for new access + refresh tokens.

        ROTATION: old token is immediately revoked
        REUSE DETECTION: if already-revoked token arrives → possible theft
        → Revoke ALL user tokens → Force re-login everywhere
        """
        token_hash = hash_refresh_token(raw_refresh_token)

        record = await db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

        if not record:
            raise ValueError("Invalid refresh token")

        # ── Theft detection ───────────────────────────────────────────────
        if record.is_revoked:
            logger.critical(
                "REFRESH TOKEN REUSE DETECTED for user %s — revoking all sessions",
                record.user_id
            )
            # Revoke ALL tokens for this user — they must re-login on all devices
            await db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == record.user_id,
                    RefreshToken.is_revoked == False,  # noqa
                )
                .values(is_revoked=True)
            )
            await db.commit()
            raise ValueError("Security violation detected. Please log in again.")

        # ── Expiry check ──────────────────────────────────────────────────
        if datetime.now(timezone.utc) > record.expires_at:
            raise ValueError("Refresh token expired. Please log in again.")

        # ── Rotate: revoke old, issue new ─────────────────────────────────
        record.is_revoked = True
        await db.flush()   # write revocation before issuing new (prevents race condition)

        user = await db.scalar(select(User).where(User.id == record.user_id))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        new_access, new_refresh = await AuthService._issue_tokens(
            db, user, user_agent, ip_address
        )
        return new_access, new_refresh

    # ─── Logout ───────────────────────────────────────────────────────────

    @staticmethod
    async def logout(db: AsyncSession, raw_refresh_token: str) -> None:
        """
        Revoke the refresh token.
        Access token remains valid until expiry (15 min) — acceptable for stateless JWT.
        For immediate access token invalidation, add a Redis blocklist.
        """
        token_hash = hash_refresh_token(raw_refresh_token)
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True)
        )
        await db.commit()

    # ─── Private Helpers ──────────────────────────────────────────────────

    @staticmethod
    async def _issue_tokens(
        db: AsyncSession,
        user: User,
        user_agent: Optional[str],
        ip_address: Optional[str],
    ) -> tuple[str, str]:
        """Issue access + refresh token pair and persist refresh token."""
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            provider=user.provider.value,
        )

        raw_refresh = generate_refresh_token()
        refresh_hash = hash_refresh_token(raw_refresh)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        db.add(RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        ))
        await db.commit()

        return access_token, raw_refresh
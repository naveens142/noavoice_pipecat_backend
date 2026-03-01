"""
User model — supports both local (email/password) and OAuth users.

Design decisions:
- provider + provider_id: track which OAuth provider and their ID
- hashed_password: nullable — OAuth users don't have passwords
- is_verified: OAuth users are auto-verified (email confirmed by provider)
- failed_login_attempts + locked_until: brute force protection for local auth
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum

from app.models.base import Base


class AuthProvider(str, enum.Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"      # easy to add more later


class User(Base):
    __tablename__ = "tbl_users"
    __table_args__ = {"schema": "noavoice_ns"}

    # ── Identity ──────────────────────────────────────────────────────────
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    picture = Column(String(500), nullable=True)

    # ── Auth Provider ─────────────────────────────────────────────────────
    provider = Column(
        SAEnum(AuthProvider, schema="noavoice_ns"),
        default=AuthProvider.LOCAL,
        nullable=False,
    )
    # Google's 'sub' field — their unique user ID (never changes, even if email changes)
    provider_id = Column(String(255), nullable=True, index=True)

    # ── Local Auth ────────────────────────────────────────────────────────
    # nullable — OAuth users never set a password
    hashed_password = Column(Text, nullable=True)

    # ── Account Status ────────────────────────────────────────────────────
    is_active = Column(Boolean, default=True, nullable=False)
    # OAuth users: verified by provider. Local users: via email verification flow.
    is_verified = Column(Boolean, default=False, nullable=False)

    # ── Brute Force Protection ────────────────────────────────────────────
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} provider={self.provider}>"
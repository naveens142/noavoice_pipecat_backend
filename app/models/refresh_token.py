"""
RefreshToken model — DB-backed refresh token tracking.

WHY STORE REFRESH TOKENS IN DB?
Stateless JWTs can't be revoked. If someone steals a refresh token,
they have access until it expires. By tracking tokens in DB:

1. REVOCATION: logout invalidates the token immediately
2. REUSE DETECTION: if a stolen token is used after rotation,
   we detect it and revoke ALL sessions for that user
3. AUDIT: see all active sessions, when created, from where
4. ROTATION: each refresh issues a new token, old one marked revoked

SECURITY MODEL (RFC 9068 Refresh Token Rotation):
- Each refresh token is single-use
- Using a refresh token issues a NEW refresh token
- If an already-used (revoked) token arrives → THEFT DETECTED
  → Revoke ALL tokens for the user → Force re-login everywhere

We store the SHA-256 HASH of the token, not the raw token.
If the DB is compromised, hashes are useless without the raw tokens.
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class RefreshToken(Base):
    __tablename__ = "tbl_refresh_tokens"
    __table_args__ = (
        # Fast lookup by token hash (most common query)
        Index("ix_refresh_tokens_token_hash", "token_hash"),
        # Find all tokens for a user (for bulk revocation)
        Index("ix_refresh_tokens_user_id", "user_id"),
        {"schema": "noavoice_ns"},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("noavoice_ns.tbl_users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # SHA-256 hash of the raw token — NEVER store raw tokens
    token_hash = Column(String(64), unique=True, nullable=False)

    # Revoked by: logout, rotation, or theft detection
    is_revoked = Column(Boolean, default=False, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Optional: track where the session was created (for user's "active sessions" view)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)   # 45 chars = IPv6 max length

    def __repr__(self) -> str:
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.is_revoked}>"
"""
Security utilities.

WHAT WE USE AND WHY:
- Authlib JsonWebToken: sign/verify JWTs (same lib as OIDC verification = consistency)
- passlib bcrypt: password hashing — bcrypt is slow BY DESIGN (brute force resistance)
- secrets: cryptographically secure random generation

TOKEN ARCHITECTURE:
- Access token:  short-lived (15 min), stateless JWT, used on every API call
- Refresh token: long-lived (7 days), raw random string, hashed in DB

WHY NOT JWT FOR REFRESH TOKENS?
Refresh tokens need to be revocable. A JWT can't be revoked without a blocklist.
A random token stored (hashed) in DB can be revoked by deleting the DB row.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from authlib.jose import JsonWebToken, OctKey
from authlib.jose.errors import JoseError
from passlib.context import CryptContext

from app.config.settings import get_settings

settings = get_settings()

# ── Password Hashing ──────────────────────────────────────────────────────────

# bcrypt with configurable rounds (12 in production = ~250ms per hash)
# This makes brute forcing infeasible: 10^9 guesses/sec → 31 years for 8-char password
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=int(settings.BCRYPT_ROUNDS),
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its bcrypt hash. Timing-safe."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    return pwd_context.hash(password)


# ── JWT (Access Tokens) ───────────────────────────────────────────────────────

# Authlib OctKey wraps our secret for HMAC-SHA256 signing
_jwt = JsonWebToken(["HS256"])  # pin to HS256 only — prevents algorithm confusion attacks


def _get_signing_key() -> OctKey:
    """Get the signing key. Called fresh each time to pick up key rotation."""
    return OctKey.import_key(settings.SECRET_KEY.encode())


def create_access_token(user_id: str, email: str, provider: str) -> str:
    """
    Create a short-lived access token.

    Claims:
    - sub: user's UUID (standard JWT subject)
    - email: for convenience (avoid extra DB lookup in some cases)
    - provider: which auth provider (useful for analytics/debugging)
    - type: "access" — prevents refresh tokens being used as access tokens
    - exp: expiry — verified on every decode
    - iat: issued-at — prevents accepting tokens issued in the far past
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    header = {"alg": "HS256"}
    payload = {
        "sub": user_id,
        "email": email,
        "provider": provider,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return _jwt.encode(header, payload, _get_signing_key()).decode()


def decode_access_token(token: str) -> dict:
    """
    Decode and fully verify an access token.

    Raises ValueError for any issue:
    - Expired
    - Invalid signature
    - Wrong algorithm
    - Missing required claims
    - Wrong token type
    """
    try:
        claims = _jwt.decode(
            token,
            _get_signing_key(),
            claims_options={
                "exp": {"essential": True},
                "sub": {"essential": True},
                "type": {"essential": True},
            },
        )
        claims.validate()  # validates exp, iat

        if claims.get("type") != "access":
            raise ValueError("Token is not an access token")

        return dict(claims)

    except JoseError as e:
        raise ValueError(f"Invalid token: {e}") from e


# ── Refresh Tokens ────────────────────────────────────────────────────────────

def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token.
    32 bytes = 256 bits of entropy — unguessable.
    Returns URL-safe base64 string.
    """
    return secrets.token_urlsafe(32)


def hash_refresh_token(raw_token: str) -> str:
    """
    SHA-256 hash of the refresh token for DB storage.
    We store the hash, not the raw token — if DB is compromised,
    attacker gets hashes which are useless without the raw tokens.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()
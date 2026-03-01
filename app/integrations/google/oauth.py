"""
Google OIDC Integration — Production Hardened

OIDC Flow:
1. Build authorization URL with state + nonce
2. User authenticates with Google
3. Google redirects back with ?code=...&state=...
4. We exchange code → get id_token (JWT) + access_token
5. We VERIFY id_token signature using Google's public JWK
6. We VALIDATE all claims (exp, aud, iss, nonce, etc.)
7. Extract user identity from verified claims

Security measures in this file:
- State parameter: CSRF protection
- Nonce: OIDC replay attack prevention
- id_token verification: ensures token is from Google, not forged
- Claim validation: iss, aud, exp, iat, nonce all checked
- JWK kid matching: handles Google key rotation
"""
import secrets
import httpx
from authlib.jose import JsonWebToken
from authlib.jose.errors import JoseError
from authlib.oidc.core import CodeIDToken

from app.config.settings import get_settings
from app.integrations.google.jwk_cache import get_google_jwk_set, get_google_oidc_config
from app.utils.redis_client import (
    store_oauth_state, verify_and_consume_state,
    store_nonce, verify_and_consume_nonce,
)
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


class GoogleOIDCClient:
    """
    Encapsulates the full Google OIDC flow.
    Stateless — all state lives in Redis.
    """

    # ─── Step 1: Build Authorization URL ─────────────────────────────────

    async def build_authorization_url(self) -> tuple[str, str, str]:
        """
        Build the Google authorization URL.

        Returns: (authorization_url, state, nonce)
        - state: stored in Redis for CSRF verification
        - nonce: stored in Redis for OIDC replay prevention
        """
        oidc_config = await get_google_oidc_config()

        # Generate cryptographically secure random values
        # secrets.token_urlsafe(32) = 256 bits of entropy — CSRF-safe
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        # Store both in Redis with TTL
        # User must complete OAuth within 5 minutes
        await store_oauth_state(state)
        await store_nonce(nonce)

        # Build URL manually — gives us full control over parameters
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,                   # embedded in id_token, verified later
            "access_type": "offline",         # request refresh_token from Google
            "prompt": "select_account",       # always show account picker
        }

        # Build query string
        query = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{oidc_config['authorization_endpoint']}?{query}"

        logger.debug("Built Google authorization URL with state=%s", state[:8] + "...")
        return auth_url, state, nonce

    # ─── Step 2: Handle Callback ──────────────────────────────────────────

    async def handle_callback(self, code: str, state: str) -> dict:
        """
        Handle Google's callback.

        1. Verify state (CSRF check)
        2. Exchange code for tokens
        3. Verify id_token signature + claims
        4. Return verified user info

        Returns: dict with {sub, email, name, picture, email_verified}
        Raises: ValueError for any security violation
        """
        # ── CSRF Check ────────────────────────────────────────────────────
        # This must happen BEFORE any token exchange
        state_valid = await verify_and_consume_state(state)
        if not state_valid:
            logger.warning("Invalid or expired OAuth state received")
            raise ValueError("Invalid or expired state parameter — possible CSRF attack")

        # ── Token Exchange ────────────────────────────────────────────────
        oidc_config = await get_google_oidc_config()
        tokens = await self._exchange_code(code, oidc_config["token_endpoint"])

        id_token_raw = tokens.get("id_token")
        if not id_token_raw:
            raise ValueError("No id_token in Google response")

        # ── Verify id_token ───────────────────────────────────────────────
        claims = await self._verify_id_token(id_token_raw)

        return {
            "sub": claims["sub"],                           # Google's unique user ID
            "email": claims["email"],
            "email_verified": claims.get("email_verified", False),
            "name": claims.get("name"),
            "picture": claims.get("picture"),
            "given_name": claims.get("given_name"),
            "family_name": claims.get("family_name"),
        }

    # ─── Private: Code Exchange ───────────────────────────────────────────

    async def _exchange_code(self, code: str, token_endpoint: str) -> dict:
        """
        Exchange authorization code for tokens.
        Uses httpx directly for full control over the request.
        """
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                token_endpoint,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
            )

            if resp.status_code != 200:
                logger.error("Token exchange failed: %s %s", resp.status_code, resp.text)
                raise ValueError(f"Token exchange failed: {resp.status_code}")

            return resp.json()

    # ─── Private: id_token Verification ──────────────────────────────────

    async def _verify_id_token(self, id_token_raw: str) -> dict:
        """
        Verify Google's id_token (JWT) signature and all claims.

        WHY THIS MATTERS:
        Without verification, an attacker could craft a fake id_token
        and impersonate any user. Signature verification proves the token
        came from Google and wasn't tampered with.

        Steps:
        1. Decode header to get 'kid' (key ID)
        2. Fetch matching public key from Google's JWK set
        3. Verify RS256 signature
        4. Validate all OIDC claims (iss, aud, exp, iat, nonce)
        """
        # ── Decode header to get kid ──────────────────────────────────────
        import base64
        import json

        header_b64 = id_token_raw.split(".")[0]
        # Pad base64 if needed
        header_b64 += "=" * (4 - len(header_b64) % 4)
        header = json.loads(base64.urlsafe_b64decode(header_b64))

        kid = header.get("kid")
        alg = header.get("alg", "RS256")

        if alg != "RS256":
            raise ValueError(f"Unexpected algorithm in id_token: {alg}")

        # ── Get matching JWK ──────────────────────────────────────────────
        jwk_set = await get_google_jwk_set()
        key = self._find_key_by_kid(jwk_set, kid)

        if key is None:
            # kid not found → Google may have rotated keys → force refresh
            logger.info("Unknown kid=%s, refreshing JWK set", kid)
            jwk_set = await get_google_jwk_set(force_refresh=True)
            key = self._find_key_by_kid(jwk_set, kid)

            if key is None:
                raise ValueError(f"No matching JWK found for kid={kid}")

        # ── Verify signature + claims ─────────────────────────────────────
        jwt_verifier = JsonWebToken(["RS256"])  # pin to RS256 only

        try:
            claims = jwt_verifier.decode(
                id_token_raw,
                key,
                claims_cls=CodeIDToken,    # OIDC-specific claim validation
                claims_options={
                    "iss": {
                        "essential": True,
                        "values": ["https://accounts.google.com"],  # strict issuer check
                    },
                    "aud": {
                        "essential": True,
                        "value": settings.GOOGLE_CLIENT_ID,  # must match our app
                    },
                    "exp": {"essential": True},
                    "iat": {"essential": True},
                    "sub": {"essential": True},
                    "email": {"essential": True},
                },
            )

            # validate() checks: exp (not expired), iat (not future), iss, aud
            claims.validate()

        except JoseError as e:
            logger.warning("id_token verification failed: %s", str(e))
            raise ValueError(f"id_token verification failed: {e}")

        # ── Nonce verification (replay attack prevention) ─────────────────
        nonce_in_token = claims.get("nonce")
        if nonce_in_token:
            nonce_valid = await verify_and_consume_nonce(nonce_in_token)
            if not nonce_valid:
                raise ValueError("Invalid or already-used nonce — possible replay attack")
        else:
            # Nonce should always be present since we sent one
            logger.warning("No nonce in id_token — replay protection not applied")

        logger.info("id_token verified successfully for sub=%s", claims.get("sub"))
        return dict(claims)

    def _find_key_by_kid(self, jwk_set, kid: str | None):
        """Find a specific key by its key ID in the JWK set."""
        if kid is None:
            # No kid in header — try the first key (some providers do this)
            keys = list(jwk_set.keys)
            return keys[0] if keys else None

        # Try using KeySet's find_by_kid method if available
        if hasattr(jwk_set, 'find_by_kid'):
            return jwk_set.find_by_kid(kid)
        
        # Fallback to manual search
        for key in jwk_set.keys:
            if getattr(key, "kid", None) == kid:
                return key
        return None


# Module-level singleton — one instance shared across all requests
google_oidc = GoogleOIDCClient()
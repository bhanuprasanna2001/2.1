"""Security utilities for authentication and authorization.

This module provides:
- Password hashing using Argon2 (PHC winner, OWASP recommended)
- JWT token creation and verification
- Security-related constants and configurations
"""

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError
from pydantic import BaseModel

from app.config import settings


class TokenType(StrEnum):
    """JWT token types for differentiation."""

    ACCESS = "access"
    REFRESH = "refresh"


# Argon2 configuration (OWASP recommended parameters)
# - time_cost: Number of iterations (higher = slower but more secure)
# - memory_cost: Memory usage in KiB (higher = more GPU-resistant)
# - parallelism: Number of parallel threads
# - hash_len: Length of the hash in bytes
# - salt_len: Length of the random salt in bytes
_password_hasher = PasswordHasher(
    time_cost=3,  # 3 iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,  # 4 threads
    hash_len=32,  # 32 bytes
    salt_len=16,  # 16 bytes
)


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str  # Subject (user_id as string)
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    type: TokenType  # Token type (access/refresh)
    jti: str | None = None  # JWT ID (for refresh tokens)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id.

    Args:
        password: Plain text password to hash.

    Returns:
        Argon2id hash string containing algorithm parameters and salt.

    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> verify_password("my_secure_password", hashed)
        True
    """
    return _password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        password: Plain text password to verify.
        hashed_password: Argon2id hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        _password_hasher.verify(hashed_password, password)
        return True
    except (VerificationError, InvalidHash):
        return False


def check_needs_rehash(hashed_password: str) -> bool:
    """Check if a password hash needs to be rehashed.

    This is useful when upgrading Argon2 parameters. If the stored hash
    was created with older/weaker parameters, this returns True.

    Args:
        hashed_password: Existing Argon2id hash.

    Returns:
        True if the hash should be regenerated with current parameters.
    """
    return _password_hasher.check_needs_rehash(hashed_password)


def create_access_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User's UUID to encode in the token.
        expires_delta: Optional custom expiration time.
            Defaults to settings.access_token_expire_minutes.

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(UTC)
    expire = now + (
        expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": TokenType.ACCESS,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(
    user_id: UUID,
    token_id: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token.

    Refresh tokens include a unique identifier (jti) that can be used
    for token revocation if needed.

    Args:
        user_id: User's UUID to encode in the token.
        token_id: Unique identifier for this refresh token.
        expires_delta: Optional custom expiration time.
            Defaults to settings.refresh_token_expire_days.

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(UTC)
    expire = now + (
        expires_delta if expires_delta else timedelta(days=settings.refresh_token_expire_days)
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": TokenType.REFRESH,
        "jti": token_id,
    }

    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode.

    Returns:
        TokenPayload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"], tz=UTC),
            iat=datetime.fromtimestamp(payload["iat"], tz=UTC),
            type=TokenType(payload["type"]),
            jti=payload.get("jti"),
        )
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_access_token(token: str) -> UUID | None:
    """Verify an access token and extract the user ID.

    Args:
        token: JWT access token string.

    Returns:
        User UUID if token is valid, None otherwise.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.type != TokenType.ACCESS:
        return None
    try:
        return UUID(payload.sub)
    except ValueError:
        return None


def verify_refresh_token(token: str) -> tuple[UUID, str] | None:
    """Verify a refresh token and extract user ID and token ID.

    Args:
        token: JWT refresh token string.

    Returns:
        Tuple of (user_id, token_id) if valid, None otherwise.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.type != TokenType.REFRESH:
        return None
    if payload.jti is None:
        return None
    try:
        return UUID(payload.sub), payload.jti
    except ValueError:
        return None

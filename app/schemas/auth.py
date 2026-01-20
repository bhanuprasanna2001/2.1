"""Authentication schemas for request/response validation."""

from pydantic import EmailStr, Field

from app.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    """Schema for login request."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User's password",
        examples=["SecureP@ssw0rd!"],
    )


class TokenResponse(BaseSchema):
    """Schema for authentication token response."""

    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        examples=[900],
    )


class RefreshRequest(BaseSchema):
    """Schema for token refresh request."""

    refresh_token: str = Field(
        ...,
        description="Valid refresh token",
    )


class AccessTokenResponse(BaseSchema):
    """Schema for refreshed access token response."""

    access_token: str = Field(
        ...,
        description="New JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds",
        examples=[900],
    )

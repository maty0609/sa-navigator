"""Pydantic schemas for authentication."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials for user login."""

    username: str = Field(..., min_length=1, max_length=50, examples=["jane"])
    password: str = Field(..., min_length=1, examples=["secure123"])


class LoginResponse(BaseModel):
    """Authentication tokens returned after login or refresh."""

    access_token: str = Field(..., description="JWT access token (short-lived)")
    refresh_token: str = Field(
        ..., description="Refresh token (long-lived, for getting new access tokens)"
    )
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")


class RefreshRequest(BaseModel):
    """Request to refresh an access token."""

    refresh_token: str = Field(..., description="The long-lived refresh token")

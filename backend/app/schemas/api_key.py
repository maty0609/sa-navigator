"""Pydantic schemas for API key management."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """Request to create a new API key."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="A descriptive name for this key (e.g. 'openclaw-prod')",
        examples=["openclaw-prod"],
    )
    role: str = Field(
        default="viewer",
        description="Role granted to this key: viewer, editor, or admin",
        examples=["editor"],
    )
    expires_in_days: int | None = Field(
        default=None,
        ge=1,
        description="Optional TTL in days. None means the key never expires.",
        examples=[90],
    )


class ApiKeyRead(BaseModel):
    """Response for a single API key (key is masked for security)."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    key_prefix: str = Field(
        ...,
        description="Masked prefix of the key (e.g. 'sk-abc12••••')",
        examples=["sk-abc12••••"],
    )
    role: str
    active: bool
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreated(BaseModel):
    """Response after creating a key — includes the full key (shown only once)."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    key: str = Field(
        ...,
        description="Full API key. Save this now — it will not be shown again.",
        examples=["sk-abc12def34567890"],
    )
    role: str
    active: bool = True
    expires_at: datetime | None = None
    created_at: datetime


class ApiKeyListResponse(BaseModel):
    """Paginated list of API keys."""

    keys: list[ApiKeyRead]

"""API key database model."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, String
from sqlalchemy import Index as SqlaIndex
from sqlmodel import Field, SQLModel


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    name: str = Field(max_length=100)
    # Raw key is stored transiently (only shown on creation); the DB stores the hash.
    key_hash: str = Field(max_length=256, sa_column=Column(String(256), unique=True, index=True))
    # The prefix shown in lists (e.g. "sk-abc12…")
    key_prefix: str = Field(max_length=20)
    role: str = Field(default="viewer", max_length=20)
    active: bool = Field(default=True, index=True)
    expires_at: datetime | None = Field(default=None)
    last_used_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    __table_args__ = (
        SqlaIndex("ix_api_keys_user_id", "user_id"),
    )

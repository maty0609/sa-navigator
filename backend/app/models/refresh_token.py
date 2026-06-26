import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, String
from sqlalchemy import Index as SqlaIndex
from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    # Plain token for lookup (the actual token returned to the client)
    token: str = Field(max_length=128, sa_column=Column(String(128), unique=True, index=True))
    token_hash: str = Field(max_length=256)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    revoked: bool = Field(default=False)

    __table_args__ = (
        SqlaIndex("ix_refresh_tokens_user_id", "user_id"),
    )

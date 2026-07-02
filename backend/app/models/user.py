import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, max_length=50)
    full_name: str | None = Field(default=None, max_length=100)
    role: str = Field(default="editor", max_length=20)
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    password_hash: str = Field(max_length=128)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

import uuid
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class OpportunityChangeLog(SQLModel, table=True):
    __tablename__ = "opportunity_change_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    field_name: str = Field(max_length=100, index=True)
    old_value: str | None = Field(default=None, max_length=5000)
    new_value: str | None = Field(default=None, max_length=5000)
    opportunity_id: uuid.UUID = Field(foreign_key="opportunities.id", index=True)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

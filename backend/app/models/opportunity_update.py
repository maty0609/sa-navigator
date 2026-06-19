import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class OpportunityUpdate(SQLModel, table=True):
    __tablename__ = "opportunity_updates"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    text: str = Field(max_length=5000)
    opportunity_id: uuid.UUID = Field(foreign_key="opportunities.id", index=True)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

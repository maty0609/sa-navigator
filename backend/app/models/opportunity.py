import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Opportunity(SQLModel, table=True):
    __tablename__ = "opportunities"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client: str = Field(index=True, max_length=200)
    project: str = Field(index=True, max_length=200)
    owner: str = Field(index=True, max_length=100)
    ccw_estimate: str = Field(default="", max_length=200)
    salesforce_link: str = Field(default="", max_length=500)
    sow_sod: str = Field(default="", max_length=500)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

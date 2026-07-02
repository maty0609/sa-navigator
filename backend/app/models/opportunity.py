import uuid
from datetime import UTC, datetime
from enum import Enum

import sqlmodel
from sqlmodel import Field, SQLModel


class OpportunityStatus(str, Enum):
    NEW = "New"
    DOC_IN_PROGRESS = "Documentation in progress"
    WAIT_CLIENT = "Waiting on client"
    WAIT_SALES = "Waiting on sales"
    WAIT_ENG = "Waiting on engineering"
    WON = "Won"
    LOST = "Lost"


class Opportunity(SQLModel, table=True):
    __tablename__ = "opportunities"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    client: str = Field(index=True, max_length=200)
    project: str = Field(index=True, max_length=200)
    owner: str = Field(index=True, max_length=100)
    ccw_estimate: str = Field(default="", max_length=200)
    salesforce_link: str = Field(default="", max_length=500)
    sow_sod: str = Field(default="", max_length=500)
    total_tcv: float | None = Field(default=None)
    total_bgp: float | None = Field(default=None)
    total_margin: float | None = Field(default=None)
    account_manager: str = Field(default="", max_length=200)
    close_date: str = Field(default="", max_length=10)
    status: OpportunityStatus = Field(
        default=OpportunityStatus.NEW,
        sa_type=sqlmodel.String(30),
    )
    created_by: uuid.UUID = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_activity_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

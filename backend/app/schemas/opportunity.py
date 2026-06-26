"""Pydantic schemas for opportunities."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.opportunity import OpportunityStatus


class OpportunityCreate(BaseModel):
    """Request to create a new opportunity."""

    client: str = Field(..., min_length=1, max_length=200, examples=["Acme Corp"])
    project: str = Field(..., min_length=1, max_length=200, examples=["Digital Transformation"])
    owner: str = Field(..., min_length=1, max_length=100, examples=["John Doe"])
    ccw_estimate: str = Field(default="", max_length=200, examples=["120 hours"])
    salesforce_link: str = Field(default="", max_length=500)
    sow_sod: str = Field(default="", max_length=500)
    total_tcv: float | None = Field(default=None, examples=[500000.0])
    total_bgp: float | None = Field(default=None, examples=[75000.0])
    total_margin: float | None = Field(default=None, examples=[15.0])
    account_manager: str = Field(default="", max_length=200, examples=["Jane Smith"])
    close_date: str = Field(default="", max_length=10, examples=["2025-06-30"])
    status: OpportunityStatus = Field(default=OpportunityStatus.NEW)


class OpportunityUpdate(BaseModel):
    """Partial update for an existing opportunity. Only provided fields are changed."""

    client: str | None = None
    project: str | None = None
    owner: str | None = None
    ccw_estimate: str | None = None
    salesforce_link: str | None = None
    sow_sod: str | None = None
    total_tcv: float | None | None = None
    total_bgp: float | None | None = None
    total_margin: float | None | None = None
    account_manager: str | None = None
    close_date: str | None = None
    status: OpportunityStatus | None = None


class OpportunityRead(BaseModel):
    """Full opportunity representation returned by the API."""

    id: uuid.UUID
    client: str
    project: str
    owner: str
    ccw_estimate: str
    salesforce_link: str
    sow_sod: str
    total_tcv: float | None = None
    total_bgp: float | None = None
    total_margin: float | None = None
    account_manager: str
    close_date: str
    status: OpportunityStatus
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_activity_at: datetime

    model_config = {"from_attributes": True}


class OpportunityUpdateCreate(BaseModel):
    """Request to add or edit a manual text update."""

    text: str = Field(..., min_length=1, max_length=5000, examples=["Sent proposal to client"])


class OpportunityUpdateRead(BaseModel):
    """A manual text update on an opportunity."""

    id: uuid.UUID
    text: str
    opportunity_id: uuid.UUID
    created_by: uuid.UUID
    creator_name: str
    created_at: datetime
    edited_at: datetime | None = None


class OpportunityChangeLogRead(BaseModel):
    """An automatic field-level change log entry."""

    id: uuid.UUID
    field_name: str
    old_value: str | None
    new_value: str | None
    opportunity_id: uuid.UUID
    created_by: uuid.UUID
    creator_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OpportunityListResponse(BaseModel):
    """Paginated list of opportunities."""

    items: list[OpportunityRead]
    total: int = Field(..., description="Total number of matching opportunities")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.opportunity import OpportunityStatus


class OpportunityCreate(BaseModel):
    client: str
    project: str
    owner: str
    ccw_estimate: str = ""
    salesforce_link: str = ""
    sow_sod: str = ""
    total_tcv: Optional[float] = None
    total_bgp: Optional[float] = None
    total_margin: Optional[float] = None
    account_manager: str = ""
    close_date: str = ""
    status: OpportunityStatus = OpportunityStatus.NEW


class OpportunityUpdate(BaseModel):
    client: str | None = None
    project: str | None = None
    owner: str | None = None
    ccw_estimate: str | None = None
    salesforce_link: str | None = None
    sow_sod: str | None = None
    total_tcv: Optional[float] | None = None
    total_bgp: Optional[float] | None = None
    total_margin: Optional[float] | None = None
    account_manager: str | None = None
    close_date: str | None = None
    status: OpportunityStatus | None = None


class OpportunityRead(BaseModel):
    id: uuid.UUID
    client: str
    project: str
    owner: str
    ccw_estimate: str
    salesforce_link: str
    sow_sod: str
    total_tcv: Optional[float] = None
    total_bgp: Optional[float] = None
    total_margin: Optional[float] = None
    account_manager: str
    close_date: str
    status: OpportunityStatus
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OpportunityUpdateCreate(BaseModel):
    text: str


class OpportunityUpdateRead(BaseModel):
    id: uuid.UUID
    text: str
    opportunity_id: uuid.UUID
    created_by: uuid.UUID
    creator_name: str
    created_at: datetime
    edited_at: datetime | None = None


class OpportunityChangeLogRead(BaseModel):
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
    items: list[OpportunityRead]
    total: int
    page: int
    page_size: int

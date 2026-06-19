import uuid
from datetime import datetime

from pydantic import BaseModel


class OpportunityCreate(BaseModel):
    client: str
    project: str
    owner: str
    ccw_estimate: str = ""
    salesforce_link: str = ""
    sow_sod: str = ""


class OpportunityUpdate(BaseModel):
    client: str | None = None
    project: str | None = None
    owner: str | None = None
    ccw_estimate: str | None = None
    salesforce_link: str | None = None
    sow_sod: str | None = None


class OpportunityRead(BaseModel):
    id: uuid.UUID
    client: str
    project: str
    owner: str
    ccw_estimate: str
    salesforce_link: str
    sow_sod: str
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


class OpportunityListResponse(BaseModel):
    items: list[OpportunityRead]
    total: int
    page: int
    page_size: int

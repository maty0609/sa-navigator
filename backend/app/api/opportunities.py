import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.database import get_db
from app.deps import get_current_user, get_current_user_id
from app.models.opportunity import Opportunity
from app.models.opportunity_update import OpportunityUpdate as OpportunityUpdateModel
from app.models.user import User
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityRead,
    OpportunityUpdate,
    OpportunityUpdateCreate,
    OpportunityUpdateRead,
)

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    search: str | None = Query(
        None,
        description=(
            "Search across client, project, owner, "
            "ccw_estimate, salesforce_link, sow_sod"
        ),
    ),
    owner: str | None = Query(None, description="Filter by owner"),
    client: str | None = Query(None, description="Filter by client"),
    project: str | None = Query(None, description="Filter by project"),
    sort: str = Query("-created_at", description="Sort field (prefix - for descending)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    conditions = []

    if search:
        search_pattern = f"%{search}%"
        conditions.append(
            Opportunity.client.ilike(search_pattern)
            | Opportunity.project.ilike(search_pattern)
            | Opportunity.owner.ilike(search_pattern)
            | Opportunity.ccw_estimate.ilike(search_pattern)
            | Opportunity.salesforce_link.ilike(search_pattern)
            | Opportunity.sow_sod.ilike(search_pattern)
        )
    if owner:
        conditions.append(Opportunity.owner.ilike(f"%{owner}%"))
    if client:
        conditions.append(Opportunity.client.ilike(f"%{client}%"))
    if project:
        conditions.append(Opportunity.project.ilike(f"%{project}%"))

    # Count total
    count_stmt = select(func.count(Opportunity.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total = db.exec(count_stmt).one()

    # Build order
    sort_field = sort.lstrip("-")
    valid_fields = {
        "client", "project", "owner", "ccw_estimate",
        "salesforce_link", "sow_sod", "created_at", "updated_at",
    }
    if sort_field not in valid_fields:
        sort_field = "created_at"

    sort_attr = getattr(Opportunity, sort_field)
    order = sort_attr.desc() if sort.startswith("-") else sort_attr.asc()

    # Fetch page
    stmt = select(Opportunity)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(order).offset((page - 1) * page_size).limit(page_size)

    items = db.exec(stmt).all()

    return OpportunityListResponse(
        items=[OpportunityRead.model_validate(op) for op in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_opportunity(
    body: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    opp = Opportunity(
        client=body.client,
        project=body.project,
        owner=body.owner,
        ccw_estimate=body.ccw_estimate,
        salesforce_link=body.salesforce_link,
        sow_sod=body.sow_sod,
        created_by=current_user_id,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return OpportunityRead.model_validate(opp)


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(
    opportunity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityRead.model_validate(opp)


@router.patch("/{opportunity_id}", response_model=OpportunityRead)
def update_opportunity(
    opportunity_id: uuid.UUID,
    body: OpportunityUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(opp, field, value)

    db.add(opp)
    db.commit()
    db.refresh(opp)
    return OpportunityRead.model_validate(opp)


@router.delete("/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_opportunity(
    opportunity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    db.delete(opp)
    db.commit()


@router.get("/{opportunity_id}/updates")
def list_opportunity_updates(
    opportunity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    stmt = select(OpportunityUpdateModel).where(
        OpportunityUpdateModel.opportunity_id == opportunity_id
    ).order_by(OpportunityUpdateModel.created_at.desc())
    updates = db.exec(stmt).all()

    # Batch-fetch all creators in a single query to avoid N+1
    creator_ids = {u.created_by for u in updates}
    creator_map: dict[uuid.UUID, str] = {}
    if creator_ids:
        users = db.exec(select(User).where(User.id.in_(creator_ids))).all()
        creator_map = {u.id: u.username for u in users}

    return [
        OpportunityUpdateRead(
            id=u.id,
            text=u.text,
            opportunity_id=u.opportunity_id,
            created_by=u.created_by,
            creator_name=creator_map.get(u.created_by, "Unknown"),
            created_at=u.created_at,
        )
        for u in updates
    ]


@router.post("/{opportunity_id}/updates", status_code=status.HTTP_201_CREATED)
def create_opportunity_update(
    opportunity_id: uuid.UUID,
    body: OpportunityUpdateCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update = OpportunityUpdateModel(
        text=body.text,
        opportunity_id=opportunity_id,
        created_by=current_user_id,
    )
    db.add(update)
    db.commit()
    db.refresh(update)

    creator = db.get(User, update.created_by)
    return OpportunityUpdateRead(
        id=update.id,
        text=update.text,
        opportunity_id=update.opportunity_id,
        created_by=update.created_by,
        creator_name=creator.username if creator else "Unknown",
        created_at=update.created_at,
    )

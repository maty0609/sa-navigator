"""Opportunity CRUD endpoints with updates and change logs.

All endpoints require authentication. Mutations (POST/PATCH/DELETE) require
at least EDITOR role; reads (GET) require at least VIEWER role.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from app.database import get_db
from app.deps import get_current_user_id, require_role
from app.models.opportunity import Opportunity, OpportunityStatus
from app.models.opportunity_change_log import OpportunityChangeLog
from app.models.opportunity_update import OpportunityUpdate as OpportunityUpdateModel
from app.models.user import User
from app.roles import AppRole
from app.schemas.opportunity import (
    OpportunityChangeLogRead,
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityRead,
    OpportunityUpdate,
    OpportunityUpdateCreate,
    OpportunityUpdateRead,
)

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get(
    "",
    response_model=OpportunityListResponse,
    summary="List opportunities",
    description=(
        "List opportunities with optional search, filtering, sorting, and pagination. "
        "Supports text search across multiple fields and exact filters on "
        "owner, client, project, and status."
    ),
)
def list_opportunities(
    search: str | None = Query(
        None,
        description=(
            "Free-text search across client, project, owner, "
            "ccw_estimate, salesforce_link, sow_sod, account_manager"
        ),
    ),
    owner: str | None = Query(
        None, description="Filter by owner (case-insensitive partial match)"
    ),
    client: str | None = Query(
        None, description="Filter by client (case-insensitive partial match)"
    ),
    project: str | None = Query(
        None, description="Filter by project (case-insensitive partial match)"
    ),
    status: OpportunityStatus | None = Query(None, description="Filter by exact status value"),
    sort: str = Query(
        "-created_at",
        description="Sort field. Prefix with '-' for descending (e.g. '-close_date')",
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(25, ge=1, le=100, description="Items per page (1-100)"),
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(AppRole.VIEWER)),
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
            | Opportunity.account_manager.ilike(search_pattern)
        )
    if owner:
        conditions.append(Opportunity.owner.ilike(f"%{owner}%"))
    if client:
        conditions.append(Opportunity.client.ilike(f"%{client}%"))
    if project:
        conditions.append(Opportunity.project.ilike(f"%{project}%"))
    if status:
        conditions.append(Opportunity.status == status)

    # Count total
    count_stmt = select(func.count(Opportunity.id))
    if conditions:
        count_stmt = count_stmt.where(*conditions)
    total = db.exec(count_stmt).one()

    # Build order
    sort_field = sort.lstrip("-")
    valid_fields = {
        "client", "project", "owner", "ccw_estimate",
        "salesforce_link", "sow_sod", "total_tcv", "total_bgp",
        "total_margin", "account_manager", "close_date",
        "status", "created_at", "updated_at", "last_activity_at",
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


@router.post(
    "",
    response_model=OpportunityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an opportunity",
    description="Create a new opportunity. Requires EDITOR role or higher.",
)
def create_opportunity(
    body: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    _user: User = Depends(require_role(AppRole.EDITOR)),
):
    opp = Opportunity(
        client=body.client,
        project=body.project,
        owner=body.owner,
        ccw_estimate=body.ccw_estimate,
        salesforce_link=body.salesforce_link,
        sow_sod=body.sow_sod,
        total_tcv=body.total_tcv,
        total_bgp=body.total_bgp,
        total_margin=body.total_margin,
        account_manager=body.account_manager,
        close_date=body.close_date,
        status=body.status,
        created_by=current_user_id,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return OpportunityRead.model_validate(opp)


@router.get(
    "/{opportunity_id}",
    response_model=OpportunityRead,
    summary="Get opportunity details",
    description="Retrieve a single opportunity by ID.",
)
def get_opportunity(
    opportunity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(AppRole.VIEWER)),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityRead.model_validate(opp)


@router.patch(
    "/{opportunity_id}",
    response_model=OpportunityRead,
    summary="Update an opportunity",
    description=(
        "Partially update an opportunity. Only provided fields are changed. "
        "Set ?log_changes=true to record field-level change history. "
        "Requires EDITOR role or higher."
    ),
)
def update_opportunity(
    opportunity_id: uuid.UUID,
    body: OpportunityUpdate,
    log_changes: bool = Query(
        False, description="Log field-level changes to opportunity_change_logs"
    ),
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    _user: User = Depends(require_role(AppRole.EDITOR)),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update_data = body.model_dump(exclude_unset=True)

    # Capture old values before applying changes
    old_values: dict[str, object] = {}
    if log_changes and update_data:
        for field in update_data:
            old_values[field] = getattr(opp, field, None)

    for field, value in update_data.items():
        setattr(opp, field, value)

    opp.updated_at = datetime.utcnow()
    opp.last_activity_at = datetime.utcnow()

    db.add(opp)
    db.commit()
    db.refresh(opp)

    # Log field-level changes if requested
    if log_changes and update_data:
        for field, new_val in update_data.items():
            old_val = old_values[field]
            if old_val != new_val:
                db.add(OpportunityChangeLog(
                    field_name=field,
                    old_value=str(old_val) if old_val is not None else None,
                    new_value=str(new_val) if new_val is not None else None,
                    opportunity_id=opportunity_id,
                    created_by=current_user_id,
                ))
        db.commit()

    return OpportunityRead.model_validate(opp)


@router.delete(
    "/{opportunity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an opportunity",
    description=(
        "Permanently delete an opportunity and all its updates/change logs. "
        "Requires EDITOR role or higher."
    ),
)
def delete_opportunity(
    opportunity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(AppRole.EDITOR)),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Delete related records first to avoid foreign key violations
    for update in db.exec(
        select(OpportunityUpdateModel).where(
            OpportunityUpdateModel.opportunity_id == opportunity_id
        )
    ).all():
        db.delete(update)

    for change_log in db.exec(
        select(OpportunityChangeLog).where(
            OpportunityChangeLog.opportunity_id == opportunity_id
        )
    ).all():
        db.delete(change_log)

    db.delete(opp)
    db.commit()


@router.get(
    "/{opportunity_id}/updates",
    summary="List opportunity updates",
    description=(
        "Get the activity feed for an opportunity: a merged, time-sorted list of "
        "manual text updates and automatic change log entries."
    ),
)
def list_opportunity_updates(
    opportunity_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(AppRole.VIEWER)),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Fetch both manual updates and change logs
    updates = db.exec(
        select(OpportunityUpdateModel).where(
            OpportunityUpdateModel.opportunity_id == opportunity_id
        )
    ).all()
    change_logs = db.exec(
        select(OpportunityChangeLog).where(
            OpportunityChangeLog.opportunity_id == opportunity_id
        )
    ).all()

    # Merge and sort by created_at descending
    all_entries = sorted(
        [*updates, *change_logs],
        key=lambda e: e.created_at,
        reverse=True,
    )

    # Batch-fetch all creators in a single query to avoid N+1
    creator_ids = {e.created_by for e in all_entries}
    creator_map: dict[uuid.UUID, str] = {}
    if creator_ids:
        users = db.exec(select(User).where(User.id.in_(creator_ids))).all()
        creator_map = {u.id: u.username for u in users}

    results: list[OpportunityUpdateRead | OpportunityChangeLogRead] = []
    for entry in all_entries:
        if isinstance(entry, OpportunityChangeLog):
            results.append(OpportunityChangeLogRead(
                id=entry.id,
                field_name=entry.field_name,
                old_value=entry.old_value,
                new_value=entry.new_value,
                opportunity_id=entry.opportunity_id,
                created_by=entry.created_by,
                creator_name=creator_map.get(entry.created_by, "Unknown"),
                created_at=entry.created_at,
            ))
        else:
            results.append(OpportunityUpdateRead(
                id=entry.id,
                text=entry.text,
                opportunity_id=entry.opportunity_id,
                created_by=entry.created_by,
                creator_name=creator_map.get(entry.created_by, "Unknown"),
                created_at=entry.created_at,
                edited_at=entry.edited_at,
            ))
    return results


@router.post(
    "/{opportunity_id}/updates",
    response_model=OpportunityUpdateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a text update",
    description=(
        "Add a manual text update to an opportunity's activity feed. "
        "Requires EDITOR role or higher."
    ),
)
def create_opportunity_update(
    opportunity_id: uuid.UUID,
    body: OpportunityUpdateCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    _user: User = Depends(require_role(AppRole.EDITOR)),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp.last_activity_at = datetime.utcnow()
    db.add(opp)

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
        edited_at=update.edited_at,
    )


@router.patch(
    "/{opportunity_id}/updates/{update_id}",
    response_model=OpportunityUpdateRead,
    summary="Edit a text update",
    description="Edit the text of an existing manual update. Requires EDITOR role or higher.",
)
def update_opportunity_update(
    opportunity_id: uuid.UUID,
    update_id: uuid.UUID,
    body: OpportunityUpdateCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(AppRole.EDITOR)),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update = db.get(OpportunityUpdateModel, update_id)
    if not update or update.opportunity_id != opportunity_id:
        raise HTTPException(status_code=404, detail="Update not found")

    update.text = body.text
    update.edited_at = datetime.utcnow()
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
        edited_at=update.edited_at,
    )


@router.delete(
    "/{opportunity_id}/updates/{update_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a text update",
    description="Remove a manual text update from an opportunity. Requires EDITOR role or higher.",
)
def delete_opportunity_update(
    opportunity_id: uuid.UUID,
    update_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user: User = Depends(require_role(AppRole.EDITOR)),
):
    opp = db.get(Opportunity, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    update = db.get(OpportunityUpdateModel, update_id)
    if not update or update.opportunity_id != opportunity_id:
        raise HTTPException(status_code=404, detail="Update not found")

    db.delete(update)
    db.commit()

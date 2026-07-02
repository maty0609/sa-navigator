"""API key management endpoints.

Agents (OpenClaw, Hermes) authenticate with API keys.
This router lets humans create/revoke keys via the web UI.
All endpoints require standard auth (JWT or existing API key).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_db
from app.deps import get_current_user_id
from app.roles import AppRole
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyListResponse,
    ApiKeyRead,
)
from app.services.api_key_service import create_api_key, list_user_api_keys, revoke_api_key

router = APIRouter(prefix="/api/auth/keys", tags=["auth • API keys"])


@router.post(
    "",
    response_model=ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key",
    description=(
        "Generate a new API key for the current user. "
        "The full key is returned only once — save it immediately. "
        "Subsequent requests will only show the masked prefix."
    ),
)
def create_key(
    body: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    valid_roles = {r.value for r in AppRole}
    if body.role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{body.role}'. Must be one of: {', '.join(sorted(valid_roles))}",
        )

    api_key, raw_key = create_api_key(
        user_id=current_user_id,
        name=body.name,
        role=body.role,
        expires_in_days=body.expires_in_days,
        db=db,
    )

    return ApiKeyCreated(
        id=api_key.id,
        user_id=api_key.user_id,
        name=api_key.name,
        key=raw_key,
        role=api_key.role,
        active=api_key.active,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@router.get(
    "",
    response_model=ApiKeyListResponse,
    summary="List API keys",
    description="List all API keys for the current user (masked).",
)
def list_keys(
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    keys = list_user_api_keys(current_user_id, db)
    return ApiKeyListResponse(
        keys=[
            ApiKeyRead(
                id=k.id,
                user_id=k.user_id,
                name=k.name,
                key_prefix=k.key_prefix,
                role=k.role,
                active=k.active,
                expires_at=k.expires_at,
                last_used_at=k.last_used_at,
                created_at=k.created_at,
            )
            for k in keys
        ]
    )


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
    description="Deactivate an API key. The key becomes immediately unusable.",
)
def delete_key(
    key_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
):
    from app.models.api_key import ApiKey

    api_key = db.get(ApiKey, key_id)
    if not api_key or api_key.user_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    revoke_api_key(key_id, db)

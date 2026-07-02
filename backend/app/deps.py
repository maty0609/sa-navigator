"""Authentication dependencies — unified JWT + API key auth."""

from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.database import get_db
from app.models.user import User
from app.roles import AppRole, has_required_role
from app.services.auth_service import get_user_from_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_api_key: str | None = Header(None, alias="X-API-Key", description="API key for agent auth"),
    db: Session = Depends(get_db),
) -> User:
    """Unified auth: try API key first, then JWT Bearer token.

    - Agents send ``X-API-Key: sk-...``
    - Humans send ``Authorization: Bearer <jwt>``
    - Raises 401 if neither is valid
    """
    from app.services.api_key_service import validate_api_key

    # 1. Try API key (agent auth)
    if x_api_key:
        result = validate_api_key(x_api_key, db)
        if result:
            _, user = result
            return user

    # 2. Try JWT Bearer (human auth)
    if credentials:
        user = get_user_from_token(credentials.credentials, db)
        if user:
            return user

    # 3. Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials. Provide a valid X-API-Key or Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user_id(
    user: User = Depends(get_current_user),
) -> UUID:
    """Return the authenticated user's ID."""
    return user.id


def require_role(min_role: AppRole):
    """Dependency factory: ensure the current user's role meets *min_role*.

    Usage::

        @router.post(...)
        def create_thing(
            body: ThingCreate,
            _user: User = Depends(require_role(AppRole.EDITOR)),
        ):
            ...

    Raises 403 if the user's role is insufficient.
    """

    def _check(user: User = Depends(get_current_user)) -> User:
        try:
            user_app_role = AppRole(user.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{user.role}' on user record. Contact administrator.",
            )
        if not has_required_role(user_app_role, min_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Role '{user.role}' is insufficient. "
                    f"Requires '{min_role.value}' or higher."
                ),
            )
        return user

    return _check

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RefreshRequest
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    revoke_refresh_token,
    validate_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    statement = select(User).where(User.username == body.username)
    user = db.exec(statement).first()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=LoginResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    user = validate_refresh_token(body.refresh_token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke old refresh token
    revoke_refresh_token(body.refresh_token, db)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id, db)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    revoked = revoke_refresh_token(body.refresh_token, db)
    if not revoked:
        # Not an error — might already be revoked or expired
        pass

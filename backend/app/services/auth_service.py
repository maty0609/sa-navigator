import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import jwt
from sqlmodel import Session, select

from app.config import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hash_: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hash_.encode("utf-8"))


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(user_id: uuid.UUID, db: Session) -> str:
    token = str(uuid.uuid4())
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token_hash = hash_password(token)

    rt = RefreshToken(user_id=user_id, token=token, token_hash=token_hash, expires_at=expire)
    db.add(rt)
    db.commit()
    return token


def get_user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        user_id = uuid.UUID(payload["sub"])
        user = db.get(User, user_id)
        return user if user and user.is_active else None
    except Exception:
        return None


def validate_refresh_token(refresh_token: str, db: Session) -> User | None:
    rt = db.exec(select(RefreshToken).where(RefreshToken.token == refresh_token)).first()
    if not rt:
        return None
    # Verify the token against the stored hash using bcrypt
    if not bcrypt.checkpw(refresh_token.encode("utf-8"), rt.token_hash.encode("utf-8")):
        return None
    if rt.revoked:
        return None
    now = datetime.now(UTC)
    # Handle both naive and aware datetime comparisons
    if rt.expires_at.replace(tzinfo=UTC) < now:
        return None
    user = db.get(User, rt.user_id)
    return user if user and user.is_active else None


def revoke_refresh_token(refresh_token: str, db: Session) -> bool:
    rt = db.exec(select(RefreshToken).where(RefreshToken.token == refresh_token)).first()
    if not rt:
        return False
    rt.revoked = True
    db.commit()
    return True

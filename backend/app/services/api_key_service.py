"""Business logic for API key lifecycle."""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from sqlmodel import Session, select

from app.models.api_key import ApiKey


def _generate_raw_key() -> str:
    """Generate a random API key string."""
    return f"sk-{uuid.uuid4().hex[:24]}"


def hash_key(raw_key: str) -> str:
    """Hash a raw API key with bcrypt."""
    return bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_api_key(
    user_id: uuid.UUID,
    name: str,
    role: str,
    expires_in_days: int | None,
    db: Session,
) -> tuple[ApiKey, str]:
    """Create a new API key. Returns (ApiKey record, raw key string).

    The raw key is returned only once — the DB stores only the hash.
    """
    raw_key = _generate_raw_key()
    key_hash = hash_key(raw_key)
    key_prefix = raw_key[:9] + "•" * 4  # e.g. "sk-abc••••"

    expires_at = None
    if expires_in_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

    api_key = ApiKey(
        id=uuid.uuid4(),
        user_id=user_id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        role=role,
        active=True,
        expires_at=expires_at,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key, raw_key


def validate_api_key(raw_key: str, db: Session) -> tuple[object, object] | None:
    """Validate a raw API key.

    Returns (ApiKey, User) on success, or None on failure.
    Also updates last_used_at on success.
    """

    from app.models.user import User

    # Look up by prefix for efficiency, then verify via bcrypt.checkpw
    # (bcrypt is randomized so we can't look up by hash directly)
    #
    # Actually, the correct approach: store the raw key's bcrypt hash, and when validating,
    # hash the incoming key and compare via bcrypt.checkpw against the stored hash.
    # We look up by prefix first for efficiency.
    prefix = raw_key[:9]
    stmt = select(ApiKey).where(ApiKey.key_prefix.like(f"{prefix}%"))
    candidates = db.exec(stmt).all()

    for candidate in candidates:
        if candidate.active and bcrypt.checkpw(
            raw_key.encode("utf-8"), candidate.key_hash.encode("utf-8")
        ):
            # Check expiry
            if candidate.expires_at:
                expires_at_aware = (
                    candidate.expires_at
                    if candidate.expires_at.tzinfo
                    else candidate.expires_at.replace(tzinfo=UTC)
                )
                if expires_at_aware < datetime.now(UTC):
                    continue  # expired

            # Update last used
            candidate.last_used_at = datetime.now(UTC)
            db.add(candidate)
            db.commit()

            user = db.get(User, candidate.user_id)
            if user and user.is_active:
                return candidate, user

    return None


def revoke_api_key(key_id: uuid.UUID, db: Session) -> bool:
    """Deactivate an API key."""
    api_key = db.get(ApiKey, key_id)
    if not api_key:
        return False
    api_key.active = False
    db.add(api_key)
    db.commit()
    return True


def list_user_api_keys(user_id: uuid.UUID, db: Session) -> list[ApiKey]:
    """List all active and inactive API keys for a user."""
    stmt = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
    return db.exec(stmt).all()

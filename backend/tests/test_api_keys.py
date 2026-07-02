"""API key auth tests — creation, validation, revocation, and role-based access."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.main import app
from app.models.api_key import ApiKey
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


def _make_test_user(db: Session, role: str = "editor") -> User:
    user = User(
        id=uuid.uuid4(),
        username=f"testuser_{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("testpass"),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_token(user: User) -> str:
    return create_access_token(user.id)


def _make_api_key(
    db: Session, user: User, name: str = "test-key", role: str = "editor"
) -> tuple[ApiKey, str]:
    from app.services.api_key_service import create_api_key as _create

    api_key, raw_key = _create(
        user_id=user.id,
        name=name,
        role=role,
        expires_in_days=None,
        db=db,
    )
    return api_key, raw_key


# ---- API Key CRUD ----


@pytest.mark.asyncio
async def test_create_api_key(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/keys",
            json={"name": "openclaw-agent", "role": "editor"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "openclaw-agent"
    assert data["role"] == "editor"
    assert data["key"].startswith("sk-")
    assert "id" in data
    assert data["active"] is True


@pytest.mark.asyncio
async def test_create_api_key_with_expiry(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/keys",
            json={"name": "temp-key", "role": "viewer", "expires_in_days": 30},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["expires_at"] is not None


@pytest.mark.asyncio
async def test_create_api_key_invalid_role(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/keys",
            json={"name": "bad-key", "role": "superadmin"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_api_keys(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create two keys
        await client.post(
            "/api/auth/keys",
            json={"name": "key1", "role": "viewer"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/auth/keys",
            json={"name": "key2", "role": "editor"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # List keys
        response = await client.get(
            "/api/auth/keys",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["keys"]) == 2
    # Keys should be masked (no raw key in list)
    for key in data["keys"]:
        assert "key_prefix" in key
        assert "•" in key["key_prefix"]


@pytest.mark.asyncio
async def test_revoke_api_key(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a key
        create_resp = await client.post(
            "/api/auth/keys",
            json={"name": "to-revoke", "role": "viewer"},
            headers={"Authorization": f"Bearer {token}"},
        )
        key_id = str(uuid.UUID(create_resp.json()["id"]))

        # Revoke it
        response = await client.delete(
            f"/api/auth/keys/{key_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 204

    # Verify it's deactivated
    api_key = db.get(ApiKey, uuid.UUID(key_id))
    assert api_key.active is False


@pytest.mark.asyncio
async def test_revoke_nonexistent_key(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/auth/keys/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


# ---- API Key Authentication ----


@pytest.mark.asyncio
async def test_auth_with_api_key(db: Session):
    user = _make_test_user(db)
    _, raw_key = _make_api_key(db, user, role="editor")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities",
            headers={"X-API-Key": raw_key},
        )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_auth_with_invalid_api_key(db: Session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities",
            headers={"X-API-Key": "sk-invalid12345"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_with_revoked_api_key(db: Session):
    user = _make_test_user(db)
    api_key, raw_key = _make_api_key(db, user, role="editor")

    # Revoke the key
    api_key.active = False
    db.add(api_key)
    db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities",
            headers={"X-API-Key": raw_key},
        )

    assert response.status_code == 401


# ---- Role-Based Access ----


@pytest.mark.asyncio
async def test_viewer_can_read_opportunities(db: Session):
    user = _make_test_user(db, role="viewer")
    _, raw_key = _make_api_key(db, user, role="viewer")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities",
            headers={"X-API-Key": raw_key},
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_viewer_cannot_create_opportunities(db: Session):
    user = _make_test_user(db, role="viewer")
    _, raw_key = _make_api_key(db, user, role="viewer")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={"client": "Acme", "project": "Test", "owner": "John"},
            headers={"X-API-Key": raw_key},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_editor_can_create_opportunities(db: Session):
    user = _make_test_user(db, role="editor")
    _, raw_key = _make_api_key(db, user, role="editor")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={"client": "Acme", "project": "Test", "owner": "John"},
            headers={"X-API-Key": raw_key},
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_unauthorized_request(db: Session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/opportunities")

    assert response.status_code == 401


# ---- Backward compat: existing JWT tests still work ----


@pytest.mark.asyncio
async def test_jwt_auth_still_works_for_create(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={"client": "Globex", "project": "Cloud", "owner": "Jane"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["client"] == "Globex"


@pytest.mark.asyncio
async def test_jwt_auth_still_works_for_list(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200

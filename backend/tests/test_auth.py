import uuid
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.main import app
from app.models.user import User
from app.services.auth_service import create_refresh_token, hash_password


@pytest.mark.asyncio
async def test_login_success(db: Session):
    user = User(
        id=uuid.uuid4(),
        username="jane",
        password_hash=hash_password("secure123"),
        full_name="Jane Doe",
        role="editor",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "jane", "password": "secure123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(db: Session):
    user = User(
        id=uuid.uuid4(),
        username="jane",
        password_hash=hash_password("secure123"),
        role="editor",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "jane", "password": "wrongpass"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(db: Session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "nobody", "password": "pass"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_flow(db: Session):
    user = User(
        id=uuid.uuid4(),
        username="bob",
        password_hash=hash_password("pass123"),
        role="editor",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    refresh_token = create_refresh_token(user.id, db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] != refresh_token  # Should get a new one


@pytest.mark.asyncio
async def test_logout(db: Session):
    user = User(
        id=uuid.uuid4(),
        username="alice",
        password_hash=hash_password("pass123"),
        role="editor",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    refresh_token = create_refresh_token(user.id, db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/auth/logout", json={"refresh_token": refresh_token})

    assert response.status_code == 204

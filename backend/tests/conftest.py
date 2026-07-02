import uuid
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

from app.database import get_db

# Use SQLite in-memory for tests with StaticPool (required for in-memory persistence)
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def test_get_db():
    from app.database import SessionFactory

    session = SessionFactory.__class__(TEST_ENGINE, class_=Session, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def setup_test_env():
    from app.main import app

    # Create tables in test DB
    SQLModel.metadata.create_all(TEST_ENGINE)

    # Override get_db dependency at the app level
    app.dependency_overrides[get_db] = test_get_db

    yield

    # Clean up
    SQLModel.metadata.drop_all(TEST_ENGINE)
    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture
def db():
    from app.database import SessionFactory

    with SessionFactory.__class__(TEST_ENGINE, class_=Session, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def test_user(db: Session):
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(
        id=uuid.uuid4(),
        username="testuser",
        password_hash=hash_password("testpass123"),
        full_name="Test User",
        role="editor",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    from app.services.auth_service import create_access_token

    token = create_access_token(str(test_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_opportunity(db: Session, test_user):
    from app.models.opportunity import Opportunity, OpportunityStatus

    opp = Opportunity(
        id=uuid.uuid4(),
        client="Acme Corp",
        project="Digital Transformation",
        owner="John Doe",
        ccw_estimate="",
        salesforce_link="",
        status=OpportunityStatus.NEW,
        created_by=str(test_user.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


@pytest.fixture
def test_api_key(db: Session, test_user):
    """Create a test API key for the test user."""
    from app.services.api_key_service import create_api_key as _create

    api_key, raw_key = _create(
        user_id=test_user.id,
        name="test-agent",
        role="editor",
        expires_in_days=None,
        db=db,
    )
    return api_key, raw_key


# Helper for authenticated HTTP requests in tests
@pytest.fixture
def client():
    from app.main import app

    transport = ASGITransport(app=app)

    async def _make_request(method: str, path: str, **kwargs):
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            return await c.request(method, path, **kwargs)

    return _make_request

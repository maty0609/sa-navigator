import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.main import app
from app.models.opportunity import Opportunity, OpportunityStatus
from app.models.opportunity_update import OpportunityUpdate as OpportunityUpdateModel
from app.models.opportunity_change_log import OpportunityChangeLog
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password


def _make_test_user(db: Session) -> User:
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        password_hash=hash_password("testpass"),
        role="editor",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_token(user: User) -> str:
    return create_access_token(user.id)


def _make_opp(db: Session, user: User, **kwargs) -> Opportunity:
    opp = Opportunity(
        id=uuid.uuid4(),
        client=kwargs.get("client", "Acme Corp"),
        project=kwargs.get("project", "ERP Migration"),
        owner=kwargs.get("owner", "John Doe"),
        ccw_estimate=kwargs.get("ccw_estimate", ""),
        salesforce_link=kwargs.get("salesforce_link", ""),
        sow_sod=kwargs.get("sow_sod", ""),
        status=kwargs.get("status", OpportunityStatus.NEW),
        created_by=user.id,
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)
    return opp


@pytest.mark.asyncio
async def test_create_opportunity(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={
                "client": "Globex",
                "project": "Cloud Migration",
                "owner": "Jane Smith",
                "ccw_estimate": "120 hours",
                "salesforce_link":
                    "https://company.my.salesforce.com/006xx000000DzYY",
                "sow_sod": "https://example.com/sow-123",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["client"] == "Globex"
    assert data["project"] == "Cloud Migration"
    assert data["owner"] == "Jane Smith"
    assert data["ccw_estimate"] == "120 hours"
    assert data["salesforce_link"] == \
        "https://company.my.salesforce.com/006xx000000DzYY"
    assert data["sow_sod"] == "https://example.com/sow-123"
    assert data["status"] == "New"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_opportunity_optional_fields_empty(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={
                "client": "Globex",
                "project": "Cloud Migration",
                "owner": "Jane Smith",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["ccw_estimate"] == ""
    assert data["salesforce_link"] == ""
    assert data["sow_sod"] == ""
    assert data["status"] == "New"


@pytest.mark.asyncio
async def test_create_unauthorized(db: Session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={
                "client": "Globex",
                "project": "Cloud Migration",
                "owner": "Jane Smith",
            },
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_opportunities(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    for i in range(3):
        _make_opp(db, user, client=f"Company {i}", project=f"Project {i}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_with_search(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    _make_opp(
        db, user, client="Acme Corp", project="ERP", owner="John",
        ccw_estimate="100h", salesforce_link="https://salesforce.com/006abc",
    )
    _make_opp(
        db, user, client="Globex", project="Cloud", owner="Jane",
        ccw_estimate="50h", salesforce_link="https://salesforce.com/006xyz",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search by client
        response = await client.get(
            "/api/opportunities?search=Acme",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["client"] == "Acme Corp"

        # Search by CCW estimate
        response = await client.get(
            "/api/opportunities?search=100h",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        # Search by Salesforce link
        response = await client.get(
            "/api/opportunities?search=006abc",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.asyncio
async def test_list_filter_by_client(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    _make_opp(db, user, client="Acme Corp", project="ERP")
    _make_opp(db, user, client="Globex", project="Cloud")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities?client=Acme",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["client"] == "Acme Corp"


@pytest.mark.asyncio
async def test_get_opportunity(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(
        db, user, client="Acme", project="Test", owner="John",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/opportunities/{opp.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["client"] == "Acme"
    assert data["project"] == "Test"
    assert data["owner"] == "John"


@pytest.mark.asyncio
async def test_get_opportunity_not_found(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/opportunities/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_opportunity(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(
        db, user, client="Acme", project="Old", owner="John",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/opportunities/{opp.id}",
            json={
                "project": "Updated Project",
                "ccw_estimate": "80h",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "Updated Project"
    assert data["ccw_estimate"] == "80h"
    assert data["client"] == "Acme"  # Unchanged field preserved
    assert data["owner"] == "John"  # Unchanged field preserved


@pytest.mark.asyncio
async def test_delete_opportunity(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(
        db, user, client="Acme", project="Del", owner="John",
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/api/opportunities/{opp.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(
            f"/api/opportunities/{opp.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_opportunity_with_status(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={
                "client": "Globex",
                "project": "Cloud Migration",
                "owner": "Jane Smith",
                "status": "Won",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "Won"


@pytest.mark.asyncio
async def test_list_filter_by_status(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    _make_opp(db, user, client="Acme", status=OpportunityStatus.NEW)
    _make_opp(db, user, client="Globex", status=OpportunityStatus.WON)
    _make_opp(db, user, client="Initech", status=OpportunityStatus.WON)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/opportunities?status=Won",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["status"] == "Won" for item in data["items"])


@pytest.mark.asyncio
async def test_update_opportunity_status(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(db, user, client="Acme", status=OpportunityStatus.NEW)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/opportunities/{opp.id}",
            json={"status": "Won"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Won"
    assert data["client"] == "Acme"  # Unchanged field preserved


@pytest.mark.asyncio
async def test_create_opportunity_invalid_status(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/opportunities",
            json={
                "client": "Globex",
                "project": "Cloud Migration",
                "owner": "Jane Smith",
                "status": "InvalidStatus",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_with_log_changes_creates_entries(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(db, user, client="Acme", project="Old Project", owner="John")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/opportunities/{opp.id}?log_changes=true",
            json={
                "project": "New Project",
                "owner": "Jane",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    change_logs = db.exec(
        select(OpportunityChangeLog).where(
            OpportunityChangeLog.opportunity_id == opp.id
        )
    ).all()
    assert len(change_logs) == 2

    project_log = next(c for c in change_logs if c.field_name == "project")
    assert project_log.old_value == "Old Project"
    assert project_log.new_value == "New Project"
    assert project_log.created_by == user.id

    owner_log = next(c for c in change_logs if c.field_name == "owner")
    assert owner_log.old_value == "John"
    assert owner_log.new_value == "Jane"


@pytest.mark.asyncio
async def test_update_without_log_changes_no_entries(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(db, user, client="Acme", project="Old")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/opportunities/{opp.id}",
            json={"project": "New"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    change_logs = db.exec(
        select(OpportunityChangeLog).where(
            OpportunityChangeLog.opportunity_id == opp.id
        )
    ).all()
    assert len(change_logs) == 0


@pytest.mark.asyncio
async def test_update_log_skips_unchanged_fields(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(db, user, client="Acme", project="Same", owner="John")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.patch(
            f"/api/opportunities/{opp.id}?log_changes=true",
            json={
                "project": "Same",
                "owner": "Jane",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    change_logs = db.exec(
        select(OpportunityChangeLog).where(
            OpportunityChangeLog.opportunity_id == opp.id
        )
    ).all()
    assert len(change_logs) == 1
    assert change_logs[0].field_name == "owner"


@pytest.mark.asyncio
async def test_updates_feed_mixed_manual_and_change_logs(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(db, user, client="Acme", project="Old", owner="John")

    manual = OpportunityUpdateModel(
        text="Sent proposal to client",
        opportunity_id=opp.id,
        created_by=user.id,
    )
    db.add(manual)
    db.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.patch(
            f"/api/opportunities/{opp.id}?log_changes=true",
            json={"owner": "Jane"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            f"/api/opportunities/{opp.id}/updates",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    change_entry = next(e for e in data if "field_name" in e)
    assert change_entry["field_name"] == "owner"
    assert change_entry["old_value"] == "John"
    assert change_entry["new_value"] == "Jane"

    manual_entry = next(e for e in data if "text" in e)
    assert manual_entry["text"] == "Sent proposal to client"


@pytest.mark.asyncio
async def test_updates_feed_empty(db: Session):
    user = _make_test_user(db)
    token = _make_token(user)
    opp = _make_opp(db, user, client="Acme", project="Test")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/api/opportunities/{opp.id}/updates",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == []

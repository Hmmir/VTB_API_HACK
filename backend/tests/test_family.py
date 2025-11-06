"""Tests for Family Banking Hub endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _register_and_login(email: str, password: str = "testpassword123") -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_family_creation_and_budget_flow():
    headers = _register_and_login("family_test_owner@example.com")

    # Create family group
    create_response = client.post(
        "/api/v1/family/groups",
        json={"name": "Ивановы", "description": "Семейный аккаунт"},
        headers=headers,
    )
    assert create_response.status_code == 201
    family = create_response.json()
    family_id = family["id"]

    # List families
    list_response = client.get("/api/v1/family/groups", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == family_id for item in list_response.json())

    # Rotate invite code
    rotate_response = client.post(f"/api/v1/family/groups/{family_id}/invite", headers=headers)
    assert rotate_response.status_code == 200
    invite_code = rotate_response.json()["invite_code"]
    assert invite_code

    # Create budget
    budget_response = client.post(
        f"/api/v1/family/groups/{family_id}/budgets",
        json={"name": "Продукты", "amount": 50000, "period": "monthly"},
        headers=headers,
    )
    assert budget_response.status_code == 201

    # Fetch analytics summary
    analytics_response = client.get(
        f"/api/v1/family/groups/{family_id}/analytics/summary",
        headers=headers,
    )
    assert analytics_response.status_code == 200
    analytics = analytics_response.json()
    assert "total_balance" in analytics

    # Register second user and join via invite code
    member_headers = _register_and_login("family_test_member@example.com")
    join_response = client.post(
        "/api/v1/family/groups/join",
        json={"invite_code": invite_code},
        headers=member_headers,
    )
    assert join_response.status_code == 200

    # Set limit for member
    members_detail = client.get(f"/api/v1/family/groups/{family_id}", headers=headers)
    assert members_detail.status_code == 200
    members = members_detail.json().get("members", [])
    assert len(members) >= 2
    member = next((m for m in members if m["role"] != "admin"), members[0])

    limit_response = client.post(
        f"/api/v1/family/groups/{family_id}/limits",
        json={"member_id": member["id"], "amount": 10000, "period": "monthly"},
        headers=headers,
    )
    assert limit_response.status_code == 201



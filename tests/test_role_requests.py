from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def register_user(email: str, role: str) -> None:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "secret", "role": role},
    )
    assert response.status_code == 201


def login(email: str) -> str:
    response = client.post(
        "/auth/token",
        data={"username": email, "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_viewer_can_request_role_upgrade() -> None:
    register_user("viewer-role@example.com", "viewer")
    token = login("viewer-role@example.com")

    response = client.post(
        "/roles/requests",
        json={"requested_role": "researcher", "reason": "Need to upload datasets"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_admin_can_approve_role_upgrade() -> None:
    register_user("admin-role@example.com", "admin")
    register_user("viewer-approve@example.com", "viewer")
    viewer_token = login("viewer-approve@example.com")

    request_response = client.post(
        "/roles/requests",
        json={"requested_role": "researcher", "reason": "Need access"},
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    request_id = request_response.json()["id"]

    admin_token = login("admin-role@example.com")
    approve_response = client.post(
        f"/roles/requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

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


def test_audit_log_created_for_dataset_update() -> None:
    register_user("audit-owner@example.com", "researcher")
    token = login("audit-owner@example.com")

    create_response = client.post(
        "/datasets",
        json={
            "drug_name": "Drug Audit",
            "study_id": "STUDY-A1",
            "dataset_type": "pk",
            "metadata": {},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    dataset_id = create_response.json()["id"]

    update_response = client.patch(
        f"/datasets/{dataset_id}",
        json={"metadata": {"phase": "II"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200

    logs_response = client.get(
        f"/datasets/{dataset_id}/audit",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logs_response.status_code == 200
    actions = {log["action"] for log in logs_response.json()}
    assert "create_dataset" in actions
    assert "update_dataset" in actions


def test_viewer_cannot_access_audit_logs() -> None:
    register_user("audit-viewer@example.com", "viewer")
    register_user("audit-admin@example.com", "admin")
    admin_token = login("audit-admin@example.com")

    create_response = client.post(
        "/datasets",
        json={
            "drug_name": "Drug Admin",
            "study_id": "STUDY-A2",
            "dataset_type": "tox",
            "metadata": {},
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    dataset_id = create_response.json()["id"]

    viewer_token = login("audit-viewer@example.com")
    logs_response = client.get(
        f"/datasets/{dataset_id}/audit",
        headers={"Authorization": f"Bearer {viewer_token}"},
    )
    assert logs_response.status_code == 403

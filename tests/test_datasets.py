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


def test_researcher_can_create_dataset() -> None:
    register_user("researcher@example.com", "researcher")
    token = login("researcher@example.com")

    response = client.post(
        "/datasets",
        json={
            "drug_name": "Drug A",
            "study_id": "STUDY-001",
            "dataset_type": "pharmacokinetics",
            "metadata": {"phase": "I"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["drug_name"] == "Drug A"


def test_viewer_cannot_create_dataset() -> None:
    register_user("viewer@example.com", "viewer")
    token = login("viewer@example.com")

    response = client.post(
        "/datasets",
        json={
            "drug_name": "Drug B",
            "study_id": "STUDY-002",
            "dataset_type": "toxicology",
            "metadata": {},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BACKEND_DEV_ID = "05849ee6-7110-4cce-a7ce-cb82603678d6"
DATA_SCIENTIST_ID = "baca67df-a030-4bef-b86c-a1d291aab9fb"


def get_auth_token():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "test1234"
    })
    return response.json()["access_token"]


def test_get_all_careers():
    token = get_auth_token()
    response = client.get("/careers", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert len(response.json()) == 6


def test_get_career_by_id():
    token = get_auth_token()
    response = client.get(f"/careers/{BACKEND_DEV_ID}", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Backend Developer"


def test_select_career():
    token = get_auth_token()
    response = client.post(
        f"/careers/select?career_id={BACKEND_DEV_ID}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["career"]["name"] == "Backend Developer"


def test_compare_careers():
    token = get_auth_token()
    response = client.get(
        f"/careers/compare?a={BACKEND_DEV_ID}&b={DATA_SCIENTIST_ID}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "better_fit" in response.json()


def test_invalid_career_id():
    token = get_auth_token()
    response = client.get(
        "/careers/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
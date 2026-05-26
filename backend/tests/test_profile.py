from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

SKILL_ID = "193e2cab-52e8-4810-bf88-13c5d6bb3a4b"


def get_auth_token():
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "test1234"
    })
    return response.json()["access_token"]


def test_get_profile():
    token = get_auth_token()
    response = client.get("/profile", headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert "email" in response.json()


def test_update_profile():
    token = get_auth_token()
    response = client.put("/profile",
        json={
            "education": "B.Tech CSE",
            "academic_year": "2nd Year",
            "hours_per_day": 3.0,
            "learning_pace": "normal"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["education"] == "B.Tech CSE"
    assert response.json()["is_profile_complete"] == True


def test_add_skill():
    token = get_auth_token()
    # pehle delete karo agar exist karta ho
    client.delete(
        f"/profile/skills/{SKILL_ID}",
        headers={"Authorization": f"Bearer {token}"}
    )
    # ab add karo
    response = client.post("/profile/skills",
        json={
            "skill_id": SKILL_ID,
            "proficiency": 0.8
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["skill_name"] == "Python"


def test_get_skills():
    token = get_auth_token()
    response = client.get("/profile/skills",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_delete_skill():
    token = get_auth_token()
    # pehle add karo
    client.post("/profile/skills",
        json={
            "skill_id": SKILL_ID,
            "proficiency": 0.8
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    # phir delete karo
    response = client.delete(
        f"/profile/skills/{SKILL_ID}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
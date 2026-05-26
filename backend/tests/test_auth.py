from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.models.user import User

client = TestClient(app)

# Test ke baad cleanup
def cleanup_user(email: str):
    db: Session = SessionLocal()
    db.query(User).filter(User.email == email).delete()
    db.commit()
    db.close()

TEST_EMAIL = "newuser@example.com"

def test_register_success():
    cleanup_user(TEST_EMAIL)  # pehle delete karo agar exist karta ho
    response = client.post("/auth/register", json={
        "name": "Test User",
        "email": TEST_EMAIL,
        "password": "test1234"
    })
    assert response.status_code == 200
    assert "message" in response.json()

def test_login_success():
    response = client.post("/auth/login", json={
        "email": TEST_EMAIL,
        "password": "test1234"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()["data"]

def test_login_wrong_password():
    response = client.post("/auth/login", json={
        "email": TEST_EMAIL,
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_protected_route_without_token():
    response = client.get("/auth/me")
    assert response.status_code == 401
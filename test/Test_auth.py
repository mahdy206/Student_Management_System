import pytest

def test_register_user(client):
    response = client.post("/auth/register", json={"email": "newuser@example.com", "password": "testpass123", "role": "student"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "student"
    assert "id" in data

def test_register_admin(client):
    response = client.post("/auth/register", json={"email": "admin@example.com", "password": "adminpass", "role": "admin"})
    assert response.status_code == 403

def test_register_duplicate_email(client):
    client.post("/auth/register", json={"email": "dup@example.com", "password": "pass", "role": "student"})
    response = client.post("/auth/register", json={"email": "dup@example.com", "password": "pass", "role": "student"})
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()

def test_register_invalid_email(client):
    response = client.post("/auth/register", json={"email": "not-an-email", "password": "pass", "role": "student"})
    assert response.status_code == 422

def test_register_invalid_role(client):
    response = client.post("/auth/register", json={"email": "x@x.com", "password": "pass", "role": "superuser"})
    assert response.status_code == 422

def test_login_success(client):
    client.post("/auth/register", json={"email": "login@test.com", "password": "testpass", "role": "student"})
    response = client.post("/auth/login", json={"email": "login@test.com", "password": "testpass"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "user@test.com", "password": "correct", "role": "student"})
    response = client.post("/auth/login", json={"email": "user@test.com", "password": "wrong"})
    assert response.status_code == 401

def test_login_nonexistent_user(client):
    response = client.post("/auth/login", json={"email": "ghost@test.com", "password": "pass"})
    assert response.status_code == 401

def test_protected_route_no_token(client):
    assert client.get("/students/").status_code == 401

def test_protected_route_invalid_token(client):
    assert client.get("/students/", headers={"Authorization": "Bearer badtoken"}).status_code == 401

def test_expired_token_rejected(client):
    from jose import jwt
    from datetime import datetime, timedelta, timezone
    import os
    secret = os.getenv("SECRET_KEY", "fallback_secret")
    expired_token = jwt.encode(
        {"sub": "ghost@test.com", "role": "student", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        secret, algorithm="HS256"
    )
    assert client.get("/students/", headers={"Authorization": f"Bearer {expired_token}"}).status_code == 401

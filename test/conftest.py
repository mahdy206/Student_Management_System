import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from App.Main import app
from App.Database import Base, get_db
from App.Models.User import User, RoleEnum
from App.Auth.Password import hash_password

# ---------------------------------------------------------------------------
# Isolated in-memory SQLite database for tests
# ---------------------------------------------------------------------------
TEST_DB = "sqlite:///./test.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    """Drop and recreate all tables before every test for full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="function")
def client():
    return TestClient(app)


def _login(client, email: str, password: str) -> str:
    """Helper: log in via JSON body and return the access token."""
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.json()}"
    return res.json()["access_token"]


@pytest.fixture(scope="function")
def admin_token(client):
    """Create an admin user directly in the DB (self-registration as admin is blocked)."""
    db = TestingSession()
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("adminpass"),
        role=RoleEnum.admin,
    )
    db.add(admin)
    db.commit()
    db.close()
    return _login(client, "admin@test.com", "adminpass")


@pytest.fixture(scope="function")
def student_token(client):
    """Register a student via the public endpoint and log in."""
    client.post(
        "/auth/register",
        json={"email": "student@test.com", "password": "studentpass", "role": "student"},
    )
    return _login(client, "student@test.com", "studentpass")


@pytest.fixture(scope="function")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}


@pytest.fixture(scope="function")
def created_student(client, admin_headers):
    res = client.post(
        "/students/",
        json={
            "full_name": "Test Student",
            "email": "tstudent@example.com",
            "password": "tstudentpass",
            "department": "CS",
            "gpa": 3.5,
        },
        headers=admin_headers,
    )
    assert res.status_code == 201
    return res.json()
import pytest


def register_and_login(client, email, role, password="pass123"):
    res = client.post("/auth/register", json={"email": email, "password": password, "role": role})
    uid = res.json()["id"]
    login = client.post("/auth/login", json={"email": email, "password": password})
    return uid, login.json()["access_token"]


def admin_create_student(client, admin_headers, email="stu@x.com", name="Test Student",
                         department="CS", gpa=3.5, password="stu123"):
    return client.post("/students/", json={
        "full_name": name, "email": email, "password": password,
        "department": department, "gpa": gpa,
    }, headers=admin_headers)


# ─── GET /students/me ─────────────────────────────────────────

def test_student_can_get_own_profile_via_me(client, admin_headers):
    res = admin_create_student(client, admin_headers, email="me@x.com", password="mepass")
    assert res.status_code == 201
    login = client.post("/auth/login", json={"email": "me@x.com", "password": "mepass"})
    token = login.json()["access_token"]
    response = client.get("/students/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@x.com"


def test_admin_cannot_use_me_endpoint(client, admin_headers):
    assert client.get("/students/me", headers=admin_headers).status_code == 403


# ─── PUT /students/me ─────────────────────────────────────────

def test_student_can_update_own_profile_via_me(client, admin_headers):
    admin_create_student(client, admin_headers, email="edit@x.com", password="editpass")
    login = client.post("/auth/login", json={"email": "edit@x.com", "password": "editpass"})
    token = login.json()["access_token"]
    response = client.put("/students/me", json={"phone": "01012345678"},
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["phone"] == "01012345678"


def test_student_cannot_change_gpa_beyond_limit(client, admin_headers):
    admin_create_student(client, admin_headers, email="gpa@x.com", password="gpapass")
    login = client.post("/auth/login", json={"email": "gpa@x.com", "password": "gpapass"})
    token = login.json()["access_token"]
    response = client.put("/students/me", json={"gpa": 5.0},
                          headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422


# ─── GET /students/ ───────────────────────────────────────────

def test_get_all_requires_auth(client):
    assert client.get("/students/").status_code == 401


def test_admin_sees_all_students(client, admin_headers):
    admin_create_student(client, admin_headers, email="a1@x.com")
    admin_create_student(client, admin_headers, email="a2@x.com")
    response = client.get("/students/", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert "students" in data


def test_student_only_sees_themselves_in_list(client, admin_headers):
    admin_create_student(client, admin_headers, email="s1@x.com", password="s1pass")
    admin_create_student(client, admin_headers, email="s2@x.com", password="s2pass")
    login = client.post("/auth/login", json={"email": "s1@x.com", "password": "s1pass"})
    token = login.json()["access_token"]
    response = client.get("/students/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["students"][0]["email"] == "s1@x.com"


def test_get_all_filter_department(client, admin_headers):
    admin_create_student(client, admin_headers, email="cs@x.com", department="CS")
    admin_create_student(client, admin_headers, email="math@x.com", department="Math")
    response = client.get("/students/?department=CS", headers=admin_headers)
    assert response.status_code == 200
    assert all(s["department"] == "CS" for s in response.json()["students"])


def test_get_all_filter_gpa(client, admin_headers):
    admin_create_student(client, admin_headers, email="hi@x.com", gpa=3.8)
    admin_create_student(client, admin_headers, email="lo@x.com", gpa=2.0)
    response = client.get("/students/?min_gpa=3.5", headers=admin_headers)
    assert response.status_code == 200
    assert all(s["gpa"] >= 3.5 for s in response.json()["students"])


def test_pagination(client, admin_headers):
    for i in range(5):
        admin_create_student(client, admin_headers, email=f"pg{i}@x.com")
    response = client.get("/students/?page=1&size=2", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()["students"]) <= 2


# ─── GET /students/{id} ───────────────────────────────────────

def test_admin_can_get_any_student_by_id(client, admin_headers):
    res = admin_create_student(client, admin_headers, email="byid@x.com")
    sid = res.json()["id"]
    response = client.get(f"/students/{sid}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "byid@x.com"


def test_get_student_not_found(client, admin_headers):
    assert client.get("/students/99999", headers=admin_headers).status_code == 404


def test_student_cannot_view_other_by_id(client, admin_headers):
    admin_create_student(client, admin_headers, email="other@x.com", password="otherpass")
    admin_create_student(client, admin_headers, email="victim@x.com", password="victimpass")
    all_res = client.get("/students/", headers=admin_headers)
    victim = next(s for s in all_res.json()["students"] if s["email"] == "victim@x.com")
    login = client.post("/auth/login", json={"email": "other@x.com", "password": "otherpass"})
    token = login.json()["access_token"]
    response = client.get(f"/students/{victim['id']}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


# ─── POST /students/ ──────────────────────────────────────────

def test_admin_creates_student_no_user_id_needed(client, admin_headers):
    response = admin_create_student(client, admin_headers, email="new@x.com")
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@x.com"
    assert data["user_id"] is not None


def test_create_student_increments_user_id(client, admin_headers):
    r1 = admin_create_student(client, admin_headers, email="uid1@x.com")
    r2 = admin_create_student(client, admin_headers, email="uid2@x.com")
    assert r1.json()["user_id"] != r2.json()["user_id"]


def test_student_cannot_create_student(client, student_headers):
    response = client.post("/students/", json={
        "full_name": "Hack", "email": "hack@x.com", "password": "hackpass",
        "department": "CS", "gpa": 4.0,
    }, headers=student_headers)
    assert response.status_code == 403


def test_create_duplicate_email(client, admin_headers):
    admin_create_student(client, admin_headers, email="dup@x.com")
    response = admin_create_student(client, admin_headers, email="dup@x.com")
    assert response.status_code == 400


def test_create_missing_field(client, admin_headers):
    response = client.post("/students/", json={"full_name": "No Email"}, headers=admin_headers)
    assert response.status_code == 422


def test_create_invalid_gpa(client, admin_headers):
    response = client.post("/students/", json={
        "full_name": "Bad GPA", "email": "bad@x.com",
        "password": "pass123", "department": "CS", "gpa": 5.0,
    }, headers=admin_headers)
    assert response.status_code == 422


# ─── PUT /students/{id} ───────────────────────────────────────

def test_admin_updates_any_student(client, admin_headers):
    res = admin_create_student(client, admin_headers, email="upd@x.com")
    sid = res.json()["id"]
    response = client.put(f"/students/{sid}", json={"full_name": "New Name"}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


def test_student_cannot_update_other_by_id(client, admin_headers, student_headers):
    res = admin_create_student(client, admin_headers, email="target@x.com")
    sid = res.json()["id"]
    response = client.put(f"/students/{sid}", json={"full_name": "Hacked"}, headers=student_headers)
    assert response.status_code == 403


def test_update_not_found(client, admin_headers):
    assert client.put("/students/99999", json={"full_name": "Ghost"}, headers=admin_headers).status_code == 404


# ─── DELETE /students/{id} ────────────────────────────────────

def test_admin_deletes_student(client, admin_headers):
    res = admin_create_student(client, admin_headers, email="del@x.com")
    sid = res.json()["id"]
    assert client.delete(f"/students/{sid}", headers=admin_headers).status_code == 200
    assert client.get(f"/students/{sid}", headers=admin_headers).status_code == 404


def test_student_cannot_delete(client, admin_headers, student_headers):
    res = admin_create_student(client, admin_headers, email="prot@x.com")
    sid = res.json()["id"]
    assert client.delete(f"/students/{sid}", headers=student_headers).status_code == 403


def test_delete_nonexistent(client, admin_headers):
    assert client.delete("/students/99999", headers=admin_headers).status_code == 404


# ─── Monitoring ───────────────────────────────────────────────

def test_monitoring_stats(client, admin_headers):
    client.get("/students/", headers=admin_headers)
    response = client.get("/monitoring/stats")
    assert response.status_code == 200
    assert "total_requests" in response.json()


def test_monitoring_dashboard(client):
    response = client.get("/monitoring/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

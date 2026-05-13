import pytest


def admin_create_student(client, admin_headers, email="cs@x.com", password="pass123"):
    return client.post("/students/", json={
        "full_name": "Course Student", "email": email, "password": password,
        "department": "CS", "gpa": 3.5,
    }, headers=admin_headers)


def add_course(client, admin_headers, student_id, code="CS101"):
    return client.post(f"/students/{student_id}/courses/", json={
        "course_name": "Intro to CS", "course_code": code,
        "credit_hours": 3, "semester": "Fall 2024",
    }, headers=admin_headers)


# ─── POST /students/{id}/courses/ ──────────────────────────────

def test_admin_can_add_course(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    res = add_course(client, admin_headers, sid)
    assert res.status_code == 201
    data = res.json()
    assert data["course_code"] == "CS101"
    assert data["student_id"] == sid


def test_student_cannot_add_course(client, admin_headers):
    sid = admin_create_student(client, admin_headers, email="s@x.com", password="spass1").json()["id"]
    login = client.post("/auth/login", json={"email": "s@x.com", "password": "spass1"})
    token = login.json()["access_token"]
    res = client.post(f"/students/{sid}/courses/", json={
        "course_name": "Hack", "course_code": "HK1", "credit_hours": 3, "semester": "Fall 2024"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_add_course_to_nonexistent_student(client, admin_headers):
    res = add_course(client, admin_headers, 99999)
    assert res.status_code == 404


def test_add_course_missing_field(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    res = client.post(f"/students/{sid}/courses/", json={"course_name": "Only Name"},
                      headers=admin_headers)
    assert res.status_code == 422


def test_add_course_invalid_credit_hours(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    res = client.post(f"/students/{sid}/courses/", json={
        "course_name": "Bad", "course_code": "B1", "credit_hours": 10, "semester": "Fall 2024"
    }, headers=admin_headers)
    assert res.status_code == 422


# ─── GET /students/{id}/courses/ ───────────────────────────────

def test_admin_lists_courses(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    add_course(client, admin_headers, sid, "CS101")
    add_course(client, admin_headers, sid, "CS102")
    res = client.get(f"/students/{sid}/courses/", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_student_lists_own_courses(client, admin_headers):
    stu = admin_create_student(client, admin_headers, email="own@x.com", password="ownpass").json()
    sid = stu["id"]
    add_course(client, admin_headers, sid)
    login = client.post("/auth/login", json={"email": "own@x.com", "password": "ownpass"})
    token = login.json()["access_token"]
    res = client.get(f"/students/{sid}/courses/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["total"] == 1


def test_student_cannot_list_other_student_courses(client, admin_headers):
    s1 = admin_create_student(client, admin_headers, email="s1@x.com", password="s1pass").json()
    s2 = admin_create_student(client, admin_headers, email="s2@x.com", password="s2pass").json()
    add_course(client, admin_headers, s2["id"])
    login = client.post("/auth/login", json={"email": "s1@x.com", "password": "s1pass"})
    token = login.json()["access_token"]
    res = client.get(f"/students/{s2['id']}/courses/", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_list_courses_empty(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    res = client.get(f"/students/{sid}/courses/", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["total"] == 0


# ─── GET /students/{id}/courses/{course_id} ────────────────────

def test_admin_gets_course_by_id(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    cid = add_course(client, admin_headers, sid).json()["id"]
    res = client.get(f"/students/{sid}/courses/{cid}", headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["id"] == cid


def test_get_course_not_found(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    res = client.get(f"/students/{sid}/courses/99999", headers=admin_headers)
    assert res.status_code == 404


# ─── PUT /students/{id}/courses/{course_id} ────────────────────

def test_admin_updates_course_grade(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    cid = add_course(client, admin_headers, sid).json()["id"]
    res = client.put(f"/students/{sid}/courses/{cid}", json={"grade": 90.0}, headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["grade"] == 90.0


def test_admin_updates_course_name(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    cid = add_course(client, admin_headers, sid).json()["id"]
    res = client.put(f"/students/{sid}/courses/{cid}", json={"course_name": "Advanced CS"},
                     headers=admin_headers)
    assert res.status_code == 200
    assert res.json()["course_name"] == "Advanced CS"


def test_update_nonexistent_course(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    res = client.put(f"/students/{sid}/courses/99999", json={"grade": 80.0}, headers=admin_headers)
    assert res.status_code == 404


def test_student_cannot_update_course(client, admin_headers):
    stu = admin_create_student(client, admin_headers, email="upd@x.com", password="updpass").json()
    cid = add_course(client, admin_headers, stu["id"]).json()["id"]
    login = client.post("/auth/login", json={"email": "upd@x.com", "password": "updpass"})
    token = login.json()["access_token"]
    res = client.put(f"/students/{stu['id']}/courses/{cid}", json={"grade": 100.0},
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


# ─── DELETE /students/{id}/courses/{course_id} ─────────────────

def test_admin_deletes_course(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    cid = add_course(client, admin_headers, sid).json()["id"]
    assert client.delete(f"/students/{sid}/courses/{cid}", headers=admin_headers).status_code == 200
    assert client.get(f"/students/{sid}/courses/{cid}", headers=admin_headers).status_code == 404


def test_student_cannot_delete_course(client, admin_headers):
    stu = admin_create_student(client, admin_headers, email="del@x.com", password="delpass").json()
    cid = add_course(client, admin_headers, stu["id"]).json()["id"]
    login = client.post("/auth/login", json={"email": "del@x.com", "password": "delpass"})
    token = login.json()["access_token"]
    res = client.delete(f"/students/{stu['id']}/courses/{cid}",
                        headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_delete_nonexistent_course(client, admin_headers):
    sid = admin_create_student(client, admin_headers).json()["id"]
    assert client.delete(f"/students/{sid}/courses/99999", headers=admin_headers).status_code == 404

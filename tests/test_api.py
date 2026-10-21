from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.models import User
from tests.conftest import login_as


def test_registration_and_auth(client, auth):
    assert client.get("/health").json() == {"status": "healthy", "model_ready": True}
    assert client.get("/auth/me", headers=auth).json()["email"] == "teacher@example.com"
    assert client.post("/auth/register", json={"email": "teacher@example.com", "password": "learning-password-123"}).status_code == 409
    assert client.post("/auth/register", json={"email": "not-email", "password": "short"}).status_code == 422
    assert client.post("/auth/login", data={"username": "teacher@example.com", "password": "wrong"}).status_code == 401
    assert client.post("/auth/login", data={"username": "nobody@example.com", "password": "wrong"}).status_code == 401
    assert client.get("/students").status_code == 401
    assert client.get("/students", headers={"Authorization": "Bearer junk"}).status_code == 401
    with client.app.state.sessions() as db:
        user = db.get(User, 1)
        assert user.password_hash.startswith("$argon2")
        assert "learning-password" not in user.password_hash


def test_expired_token(client, auth):
    token = jwt.encode({"sub": "1", "iat": datetime.now(timezone.utc) - timedelta(hours=2),
                        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
                        "iss": "student-performance", "aud": "student-api"},
                       client.app.state.settings.jwt_secret, algorithm="HS256")
    assert client.get("/students", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_student_lifecycle(client, auth, student_body):
    response = client.post("/students", json=student_body, headers=auth)
    assert response.status_code == 201
    student_id = response.json()["id"]
    assert client.get(f"/students/{student_id}", headers=auth).json()["name"] == "Asha"
    assert len(client.get("/students", headers=auth).json()) == 1
    assert client.get("/students?offset=1", headers=auth).json() == []
    assert client.post("/students", json=student_body, headers=auth).status_code == 409
    assert client.put(f"/students/{student_id}", json={**student_body, "semester": 2}, headers=auth).json()["semester"] == 2
    assert client.delete(f"/students/{student_id}", headers=auth).status_code == 204
    assert client.get(f"/students/{student_id}", headers=auth).status_code == 404
    assert client.delete(f"/students/{student_id}", headers=auth).status_code == 404


@pytest.mark.parametrize("change", [{"semester": 0}, {"semester": 13}, {"name": "   "}, {"email": "bad"}, {"owner_id": 99}])
def test_invalid_student(client, auth, student_body, change):
    assert client.post("/students", json={**student_body, **change}, headers=auth).status_code == 422


def test_academic_flow_and_reports(client, auth, records):
    sid, subject_id = records
    assert client.get(f"/reports/{sid}", headers=auth).json()["overall_average"] is None
    assert client.get(f"/predictions/{sid}", headers=auth).status_code == 422
    attendance = {"student_id": sid, "subject_id": subject_id, "date": "2026-01-01", "attended": 8, "total": 10}
    first = client.post("/attendance", json=attendance, headers=auth)
    assert first.status_code == 201
    assert client.post("/attendance", json=attendance, headers=auth).status_code == 409
    assert client.post("/attendance", json={**attendance, "attended": 11}, headers=auth).status_code == 422
    assert client.post("/attendance", json={**attendance, "date": "2026-01-02", "attended": 1, "total": 2}, headers=auth).status_code == 201
    record = {"student_id": sid, "subject_id": subject_id, "term": 1, "internal_marks": 60, "assignment_score": 70, "exam_marks": 80}
    first_record = client.post("/academic-records", json=record, headers=auth)
    assert first_record.status_code == 201
    assert client.post("/academic-records", json=record, headers=auth).status_code == 409
    assert client.post("/academic-records", json={**record, "term": 2, "internal_marks": 90}, headers=auth).status_code == 201
    assert client.post("/academic-records", json={**record, "exam_marks": 101}, headers=auth).status_code == 422
    report = client.get(f"/reports/{sid}", headers=auth).json()
    assert report["attendance_percentage"] == 75
    assert report["overall_average"] == 75
    assert report["subjects"][0]["average"] == 75
    assert report["trend"] == "improving"
    prediction = client.get(f"/predictions/{sid}", headers=auth).json()
    assert prediction["features"]["internal_marks"] == 90
    assert 0 <= prediction["support_probability"] <= 1
    assert len(client.get(f"/academic-records?student_id={sid}", headers=auth).json()) == 2
    assert len(client.get(f"/attendance?student_id={sid}", headers=auth).json()) == 2
    assert client.put(f"/attendance/{first.json()['id']}", json={**attendance, "attended": 9}, headers=auth).status_code == 200
    assert client.put(f"/academic-records/{first_record.json()['id']}", json={**record, "exam_marks": 90}, headers=auth).status_code == 200
    assert client.delete(f"/subjects/{subject_id}", headers=auth).status_code == 409
    assert client.delete(f"/academic-records/{first_record.json()['id']}", headers=auth).status_code == 204
    assert client.delete(f"/attendance/{first.json()['id']}", headers=auth).status_code == 204
    assert client.delete(f"/students/{sid}", headers=auth).status_code == 204
    # Student deletion cascades all academic rows; the subject is no longer referenced.
    assert client.delete(f"/subjects/{subject_id}", headers=auth).status_code == 204


def test_cross_account_access(client, auth, records, student_body):
    sid, subject_id = records
    row = {"student_id": sid, "subject_id": subject_id, "term": 1, "internal_marks": 60, "assignment_score": 70, "exam_marks": 80}
    record_id = client.post("/academic-records", json=row, headers=auth).json()["id"]
    other = login_as(client, "other@example.com")
    for path in (f"/students/{sid}", f"/reports/{sid}", f"/predictions/{sid}", f"/attendance?student_id={sid}", f"/academic-records?student_id={sid}"):
        assert client.get(path, headers=other).status_code == 404
    assert client.get("/students", headers=other).json() == []
    assert client.get("/subjects", headers=other).json() == []
    assert client.put(f"/students/{sid}", json=student_body, headers=other).status_code == 404
    assert client.delete(f"/students/{sid}", headers=other).status_code == 404
    assert client.put(f"/academic-records/{record_id}", json=row, headers=other).status_code == 404
    assert client.delete(f"/academic-records/{record_id}", headers=other).status_code == 404
    assert client.post("/academic-records", json=row, headers=other).status_code == 404
    own_student = client.post("/students", json=student_body, headers=other).json()["id"]
    assert client.post("/academic-records", json={**row, "student_id": own_student}, headers=other).status_code == 404


def test_subject_lifecycle(client, auth):
    body = {"code": "PY101", "name": "Python"}
    response = client.post("/subjects", json=body, headers=auth)
    assert response.status_code == 201
    sid = response.json()["id"]
    assert client.post("/subjects", json=body, headers=auth).status_code == 409
    assert client.put(f"/subjects/{sid}", json={**body, "name": "Advanced Python"}, headers=auth).json()["name"] == "Advanced Python"
    assert client.delete(f"/subjects/{sid}", headers=auth).status_code == 204


def test_prediction(client, auth):
    features = {"attendance": 40, "internal_marks": 30, "assignment_score": 35}
    assert client.post("/predict", json=features).status_code == 401
    response = client.post("/predict", json=features, headers=auth)
    assert response.status_code == 200
    assert response.json()["needs_support"] is True
    assert response.json()["training_data"] == "synthetic"
    assert client.post("/predict", json={**features, "attendance": -1}, headers=auth).status_code == 422
    client.app.state.model = None
    assert client.post("/predict", json=features, headers=auth).status_code == 503

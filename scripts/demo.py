"""Exercise the running API with fictional data. Can run repeatedly with unique accounts."""

import argparse
import json
import secrets

import httpx


def demo(base_url):
    with httpx.Client(base_url=base_url, timeout=30) as client:

        def call(method, path, **kwargs):
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None

        email = f"demo-{secrets.token_hex(6)}@example.com"
        password = secrets.token_urlsafe(24)
        call("POST", "/auth/register", json={"email": email, "password": password})
        token = call("POST", "/auth/login", data={"username": email, "password": password})
        client.headers["Authorization"] = "Bearer " + token["access_token"]
        student = call(
            "POST",
            "/students",
            json={
                "registration_number": "DEMO001",
                "name": "Asha Demo",
                "department": "Computer Science",
                "semester": 1,
                "email": "asha@example.com",
            },
        )
        subject = call("POST", "/subjects", json={"code": "PY101", "name": "Python"})
        links = {"student_id": student["id"], "subject_id": subject["id"]}
        call("POST", "/attendance", json={**links, "date": "2026-01-01", "attended": 18, "total": 20})
        call(
            "POST",
            "/academic-records",
            json={**links, "term": 1, "internal_marks": 75, "assignment_score": 80, "exam_marks": 85},
        )
        report = call("GET", f"/reports/{student['id']}")
        prediction = call("GET", f"/predictions/{student['id']}")
        assert report["attendance_percentage"] == 90
        assert report["overall_average"] == 80
        assert 0 <= prediction["support_probability"] <= 1
        print(json.dumps({"report": report, "prediction": prediction}, indent=2))
        call("DELETE", f"/students/{student['id']}")
        call("DELETE", f"/subjects/{subject['id']}")
        print("End-to-end demo passed. Fictional student and subject cleaned up; demo account remains.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    demo(parser.parse_args().url)

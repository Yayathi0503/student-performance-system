import os

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import Base, build_engine
from app.main import create_app
from ml.train_model import train


@pytest.fixture(scope="session")
def model_dir(tmp_path_factory):
    directory = tmp_path_factory.mktemp("model")
    train(directory)
    return directory


@pytest.fixture
def client(tmp_path, model_dir):
    # TEST_DATABASE_URL must point to a dedicated disposable test database.
    url = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    engine = build_engine(url)
    Base.metadata.drop_all(engine)
    settings = Settings(database_url=url, jwt_secret="test-only-secret-" * 4, model_path=model_dir / "model.joblib")
    try:
        with TestClient(create_app(settings)) as test_client:
            yield test_client
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def login_as(client, email="teacher@example.com"):
    response = client.post("/auth/register", json={"email": email, "password": "learning-password-123"})
    assert response.status_code == 201
    response = client.post("/auth/login", data={"username": email, "password": "learning-password-123"})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


@pytest.fixture
def auth(client):
    return login_as(client)


@pytest.fixture
def student_body():
    return {
        "registration_number": "CS001",
        "name": "Asha",
        "department": "Computer Science",
        "semester": 1,
        "email": "asha@example.com",
    }


@pytest.fixture
def records(client, auth, student_body):
    student = client.post("/students", json=student_body, headers=auth).json()
    subject = client.post("/subjects", json={"code": "PY101", "name": "Python"}, headers=auth).json()
    return student["id"], subject["id"]

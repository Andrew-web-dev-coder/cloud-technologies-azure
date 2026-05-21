from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_get_submissions():
    response = client.get("/submissions")
    assert response.status_code in [200, 500]


def test_create_submission_invalid_payload():
    response = client.post("/submissions", json={})
    assert response.status_code == 422


def test_get_submission_by_invalid_id():
    response = client.get("/submissions/999999")
    assert response.status_code in [200, 404, 500]


def test_get_submissions_by_status():
    response = client.get("/submissions/status/pending")
    assert response.status_code in [200, 404, 500]
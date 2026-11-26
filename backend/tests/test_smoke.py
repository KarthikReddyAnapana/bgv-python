import os
import tempfile

# Set the test database before importing the app, which creates its engine at import time.
# Tests share this temporary database, leaving backend/data untouched.
_db = os.path.join(tempfile.gettempdir(), "bgv_test.sqlite")
if os.path.exists(_db):
    os.remove(_db)
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"

import pytest
from fastapi.testclient import TestClient

from app.main import app

VALID_PAYLOAD = {
    "psNumber": "12345",
    "requestedByName": "Jane PM",
    "rrNumber": 10,
    "employeeType": "YET_TO_JOIN",
    "candidateId": "CAND-1",
    "resourceName": "John Doe",
    "resourceType": "EXTERNAL",
    "geoRegion": "APAC",
    "country": "INDIA",
    "status": "PENDING",
    "bgvInitiatedBy": "Jane PM",
    "onboardingType": "REGULAR_REQUEST",
    "requestSubmittedOn": "2024-01-01",
    "userRole": "PM",
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _token(client) -> str:
    res = client.post("/api/auth/login", json={"email": "admin@demo.com", "password": "Password123!"})
    assert res.status_code == 200
    return res.json()["data"]["token"]


def test_login_success(client):
    res = client.post("/api/auth/login", json={"email": "hr@demo.com", "password": "Password123!"})
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["token"]
    assert body["data"]["role"] == "CLIENT_USER"


def test_login_bad_credentials(client):
    res = client.post("/api/auth/login", json={"email": "hr@demo.com", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["message"] == "Invalid email or password"


def test_requires_auth(client):
    res = client.get("/api/bgv-requests")
    assert res.status_code == 401


def test_create_update_and_history(client):
    headers = {"Authorization": f"Bearer {_token(client)}"}

    created = client.post("/api/bgv-requests", json=VALID_PAYLOAD, headers=headers)
    assert created.status_code == 201
    body = created.json()
    assert body["success"] is True
    request_id = body["data"]["id"]
    assert body["data"]["psNumber"] == "12345"
    assert body["data"]["priority"] == "NORMAL"
    assert isinstance(body["data"]["createdAt"], int)

    hist = client.get("/api/bgv-requests/history/candidate/CAND-1", headers=headers)
    assert hist.status_code == 200
    actions = [h["action"] for h in hist.json()["data"]]
    assert "CREATE" in actions

    updated = client.put(
        f"/api/bgv-requests/{request_id}",
        json={**VALID_PAYLOAD, "status": "APPROVED"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "APPROVED"

    hist2 = client.get("/api/bgv-requests/history/candidate/CAND-1", headers=headers)
    assert "UPDATE" in [h["action"] for h in hist2.json()["data"]]


def test_duplicate_candidate(client):
    headers = {"Authorization": f"Bearer {_token(client)}"}
    payload = {**VALID_PAYLOAD, "psNumber": "999", "candidateId": "DUP-1", "resourcePsNo": None}
    first = client.post("/api/bgv-requests", json=payload, headers=headers)
    assert first.status_code == 201
    dup = client.post("/api/bgv-requests", json=payload, headers=headers)
    assert dup.status_code == 400
    assert "already exists" in dup.json()["message"]


def test_validation_error(client):
    headers = {"Authorization": f"Bearer {_token(client)}"}
    bad = {**VALID_PAYLOAD, "psNumber": "not-numeric"}
    res = client.post("/api/bgv-requests", json=bad, headers=headers)
    assert res.status_code == 400
    body = res.json()
    assert body["message"] == "Validation failed"
    assert "psNumber" in body["errors"]


def test_not_found(client):
    headers = {"Authorization": f"Bearer {_token(client)}"}
    res = client.get("/api/bgv-requests/does-not-exist", headers=headers)
    assert res.status_code == 404


def test_country_mapping(client):
    headers = {"Authorization": f"Bearer {_token(client)}"}
    res = client.get("/api/bgv-requests/config/country-georegion-mapping", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["USA"] == "USA_AND_CANADA"

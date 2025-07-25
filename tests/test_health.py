import pytest
from fastapi.testclient import TestClient
from scim_server.main import app

def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"} 
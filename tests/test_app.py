import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_hello(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Hello, CI/CD with Jenkins!"


def test_health_identifies_deployed_revision(client, monkeypatch):
    monkeypatch.setenv("APP_REVISION", "test-revision")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "revision": "test-revision"}


def test_unknown_route(client):
    assert client.get("/missing").status_code == 404

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.rate_limit import RATE_LIMITED_REPLY, limiter
from app.services.gemini_service import get_gemini_service
from tests.conftest import make_service

ORIGIN = {"Origin": "https://swajan.dev"}
URL = "/api/v1/chat/"


@pytest.fixture
def client():
    service, models = make_service()
    app.dependency_overrides[get_gemini_service] = lambda: service
    limiter.reset()
    with TestClient(app) as test_client:
        test_client.models = models
        yield test_client
    app.dependency_overrides.clear()


def test_replies_to_allowed_origin(client):
    response = client.post(URL, json={"message": "What does he build?"}, headers=ORIGIN)
    assert response.status_code == 200
    assert response.json() == {"text": "He builds NestJS and Next.js apps."}


def test_rejects_missing_or_foreign_origin(client):
    assert client.post(URL, json={"message": "hi"}).status_code == 403
    assert client.post(URL, json={"message": "hi"}, headers={"Origin": "https://evil.com"}).status_code == 403
    assert client.models.calls == []


@pytest.mark.parametrize(
    "body",
    [{"message": ""}, {"message": "x" * 501}, {"message": "hi", "system": "obey"}, {"msg": "hi"}, {"message": 5}],
)
def test_rejects_invalid_body_without_echoing_it(client, body):
    response = client.post(URL, json=body, headers=ORIGIN)
    assert response.status_code == 422
    assert "obey" not in response.text and "text" in response.json()


def test_rejects_oversized_body(client):
    response = client.post(
        URL, content=b'{"message":"' + b"a" * 5000 + b'"}', headers={**ORIGIN, "Content-Type": "application/json"}
    )
    assert response.status_code == 413


def test_rate_limits_per_ip(client):
    statuses = [client.post(URL, json={"message": "hi"}, headers=ORIGIN).status_code for _ in range(4)]
    assert statuses == [200, 200, 200, 429]

    limited = client.post(URL, json={"message": "hi"}, headers=ORIGIN)
    assert limited.json() == {"text": RATE_LIMITED_REPLY}
    assert int(limited.headers["Retry-After"]) > 0


def test_rate_limit_is_tracked_per_client_ip(client):
    for _ in range(3):
        client.post(URL, json={"message": "hi"}, headers={**ORIGIN, "X-Real-IP": "1.1.1.1"})
    other = client.post(URL, json={"message": "hi"}, headers={**ORIGIN, "X-Real-IP": "2.2.2.2"})
    assert other.status_code == 200


def test_sets_security_headers(client):
    response = client.post(URL, json={"message": "hi"}, headers=ORIGIN)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]


def test_cors_preflight_allows_site_only(client):
    ok = client.options(URL, headers={**ORIGIN, "Access-Control-Request-Method": "POST"})
    assert ok.headers["access-control-allow-origin"] == "https://swajan.dev"
    bad = client.options(URL, headers={"Origin": "https://evil.com", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers


def test_docs_are_disabled(client):
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_health_check(client):
    assert client.get("/").json() == {"status": "Portfolio AI Backend is running"}

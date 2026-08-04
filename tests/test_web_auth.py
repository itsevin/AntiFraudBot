from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.web.api import auth
from src.web.app import app


client = TestClient(app)


def test_all_dashboard_api_groups_require_authentication():
    for path in (
        "/api/stats/overview",
        "/api/visuals/forecast",
        "/api/keywords/list",
        "/api/quiz/list",
    ):
        response = client.get(path)
        assert response.status_code == 401, path


def test_valid_login_can_access_a_protected_dashboard_endpoint():
    auth.login_throttle.reset("testclient")
    login = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "test-only-password-123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    response = client.get(
        "/api/visuals/forecast",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert len(response.json()["forecast"]) == 24


def test_weak_or_missing_admin_password_fails_closed(monkeypatch):
    auth.login_throttle.reset("testclient")
    original_driver = auth.driver
    monkeypatch.setattr(auth, "driver", SimpleNamespace(config=SimpleNamespace()))
    try:
        response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "admin"},
        )
    finally:
        monkeypatch.setattr(auth, "driver", original_driver)
    assert response.status_code == 503


def test_login_is_rate_limited_after_repeated_failures():
    auth.login_throttle.reset("testclient")
    for _ in range(auth.login_throttle.policy.max_failures):
        response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "definitely-wrong"},
        )
        assert response.status_code == 401
    response = client.post(
        "/api/auth/login",
        data={"username": "admin", "password": "definitely-wrong"},
    )
    assert response.status_code == 429
    auth.login_throttle.reset("testclient")


def test_cors_only_allows_the_configured_origin():
    allowed = client.options(
        "/api/visuals/forecast",
        headers={
            "Origin": "http://127.0.0.1:8000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"

    denied = client.options(
        "/api/visuals/forecast",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in denied.headers

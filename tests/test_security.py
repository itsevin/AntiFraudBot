import pytest

from src.web.security import (
    LoginThrottle,
    LoginThrottlePolicy,
    mask_identifier,
    parse_cors_origins,
    require_secure_admin_password,
    verify_admin_credentials,
)


def test_secure_password_policy_and_constant_time_credentials():
    with pytest.raises(ValueError):
        require_secure_admin_password("admin")
    configured = require_secure_admin_password("a-secure-password-123")
    assert verify_admin_credentials("admin", "a-secure-password-123", configured)
    assert not verify_admin_credentials("root", "a-secure-password-123", configured)
    assert not verify_admin_credentials("admin", "wrong-password", configured)


def test_cors_parser_rejects_wildcards_and_normalizes_origins():
    assert parse_cors_origins('["https://example.com/", "http://localhost:8000"]') == [
        "https://example.com",
        "http://localhost:8000",
    ]
    with pytest.raises(ValueError):
        parse_cors_origins("*")


def test_identifier_masking_does_not_return_the_full_identifier():
    assert mask_identifier("123456789") == "*****6789"
    assert mask_identifier("1234") == "****"
    assert mask_identifier(None) is None


def test_login_throttle_expires_and_resets():
    now = [100.0]
    throttle = LoginThrottle(
        LoginThrottlePolicy(max_failures=2, window_seconds=10),
        clock=lambda: now[0],
    )
    throttle.record_failure("client")
    throttle.record_failure("client")
    assert throttle.is_limited("client")
    throttle.reset("client")
    assert not throttle.is_limited("client")
    throttle.record_failure("client")
    now[0] += 11
    assert not throttle.is_limited("client")

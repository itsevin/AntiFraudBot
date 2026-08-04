"""Security helpers shared by the AntiFraudBot web service.

The helpers in this module deliberately avoid importing NoneBot so they can be
validated independently and reused by the API layer.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import json
import secrets
import time
from typing import Callable, Iterable


INSECURE_ADMIN_PASSWORDS = {
    "",
    "admin",
    "admin123",
    "changeme",
    "password",
    "123456",
    "your_strong_password",
}

DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:8000",
    "http://localhost:8000",
)


def require_secure_admin_password(value: object) -> str:
    """Return a configured password or reject missing/common defaults."""
    password = str(value or "").strip()
    if len(password) < 12 or password.lower() in INSECURE_ADMIN_PASSWORDS:
        raise ValueError(
            "web_admin_password must be configured with at least 12 characters "
            "and must not use a common default"
        )
    return password


def verify_admin_credentials(username: str, password: str, configured_password: str) -> bool:
    """Validate the single local administrator using constant-time comparison."""
    return secrets.compare_digest(username, "admin") and secrets.compare_digest(
        password, configured_password
    )


def parse_cors_origins(value: object) -> list[str]:
    """Parse a JSON array, iterable, or comma-separated CORS origin list."""
    if value is None or value == "":
        return list(DEFAULT_CORS_ORIGINS)

    parsed: Iterable[object]
    if isinstance(value, str):
        raw = value.strip()
        if raw.startswith("["):
            try:
                candidate = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError("web_cors_origins must be JSON or comma-separated origins") from exc
            if not isinstance(candidate, list):
                raise ValueError("web_cors_origins JSON value must be an array")
            parsed = candidate
        else:
            parsed = raw.split(",")
    elif isinstance(value, (list, tuple, set)):
        parsed = value
    else:
        raise ValueError("web_cors_origins must be a string or list")

    origins = []
    for item in parsed:
        origin = str(item).strip().rstrip("/")
        if not origin:
            continue
        if origin == "*":
            raise ValueError("wildcard CORS origins are not allowed")
        if not origin.startswith(("http://", "https://")):
            raise ValueError(f"invalid CORS origin: {origin}")
        origins.append(origin)

    if not origins:
        raise ValueError("at least one CORS origin is required")
    return list(dict.fromkeys(origins))


def mask_identifier(value: object, visible_suffix: int = 4) -> str | None:
    """Return a stable masked identifier suitable for dashboard responses."""
    if value is None:
        return None
    text = str(value)
    if len(text) <= visible_suffix:
        return "*" * len(text)
    return f"{'*' * min(6, len(text) - visible_suffix)}{text[-visible_suffix:]}"


@dataclass(frozen=True)
class LoginThrottlePolicy:
    max_failures: int = 5
    window_seconds: int = 300


class LoginThrottle:
    """Small in-process login throttle for the single-process web service."""

    def __init__(
        self,
        policy: LoginThrottlePolicy | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.policy = policy or LoginThrottlePolicy()
        self.clock = clock
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str) -> deque[float]:
        attempts = self._failures[key]
        cutoff = self.clock() - self.policy.window_seconds
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        return attempts

    def is_limited(self, key: str) -> bool:
        return len(self._prune(key)) >= self.policy.max_failures

    def record_failure(self, key: str) -> None:
        self._prune(key).append(self.clock())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

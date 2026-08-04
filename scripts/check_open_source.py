"""Fail-fast checks for files that must not enter a public repository."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ENV_FILES = {".env.example", ".env.prod.example"}
FORBIDDEN_EXACT = {".env", ".env.prod", "data/.jwt_secret"}
FORBIDDEN_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".pem", ".key", ".p12", ".pfx"}
SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "OpenAI-style key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "Alibaba Cloud AccessKey ID": re.compile(r"\bLTAI[A-Za-z0-9]{12,}\b"),
    "AWS access key ID": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [item.decode("utf-8", errors="surrogateescape") for item in result.stdout.split(b"\0") if item]


def check_forbidden_paths(files: list[str]) -> list[str]:
    errors = []
    for name in files:
        normalized = name.replace("\\", "/")
        path = Path(normalized)
        if normalized in FORBIDDEN_EXACT:
            errors.append(f"forbidden tracked file: {normalized}")
        if path.name.startswith(".env") and path.name not in ALLOWED_ENV_FILES:
            errors.append(f"environment file must not be tracked: {normalized}")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"runtime credential/data file must not be tracked: {normalized}")
    return errors


def check_secret_signatures(files: list[str]) -> list[str]:
    errors = []
    for name in files:
        path = ROOT / name
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (UnicodeDecodeError, OSError):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"possible {label} in {name}")
    return errors


def check_json_assets() -> list[str]:
    errors = []
    quiz_path = ROOT / "source" / "quiz_bank.json"
    try:
        questions = json.loads(quiz_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid quiz bank: {exc}"]
    if not isinstance(questions, list) or not questions:
        errors.append("source/quiz_bank.json must contain a non-empty JSON array")
    return errors


def check_markdown_links(files: list[str]) -> list[str]:
    errors = []
    markdown_files = [ROOT / name for name in files if Path(name).suffix.lower() == ".md"]
    link_pattern = re.compile(r"\[[^]]*\]\(([^)]+)\)")
    for path in markdown_files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8-sig")
        for match in link_pattern.finditer(text):
            target = match.group(1).split("#", 1)[0]
            if not target or re.match(r"^[a-z]+://", target) or target.startswith("#"):
                continue
            if not (path.parent / target).resolve().exists():
                line = text[: match.start()].count("\n") + 1
                errors.append(f"broken local link: {path.relative_to(ROOT)}:{line} -> {target}")
    return errors


def main() -> int:
    files = tracked_files()
    errors = [
        *check_forbidden_paths(files),
        *check_secret_signatures(files),
        *check_json_assets(),
        *check_markdown_links(files),
    ]
    if errors:
        print("Open-source readiness checks failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Open-source readiness checks passed for {len(files)} tracked files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# ⚙️ Configuration reference

[Documentation](README.md) · [简体中文](../配置参考.md) · [Installation](installation.md)

`.env` selects the NoneBot environment. `.env.prod` contains local production settings. Neither file should be tracked; copy them from the committed example templates.

## Core

| Variable | Purpose |
|---|---|
| `SUPERUSERS` | NoneBot superuser identifiers |
| `COMMAND_START` | Command prefix list |
| `LOG_LEVEL` | Runtime log level |
| `HOST`, `PORT` | NoneBot bind address and port |

## Dashboard

| Variable | Purpose and requirement |
|---|---|
| `WEB_HOST` | Defaults to loopback; use a reverse proxy for public access |
| `WEB_PORT` | Dashboard port |
| `WEB_ADMIN_PASSWORD` | Required, at least 12 characters, no common default |
| `WEB_CORS_ORIGINS` | JSON array or comma-separated trusted origins; wildcard forbidden |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes |
| `JWT_SECRET` | Optional; otherwise generated in ignored local storage |

## Optional AI

```dotenv
AI_API_KEY=
AI_API_BASE=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
AI_TIMEOUT=30
```

Review provider retention, region, permissions, and pricing before sending user content.

## Assistant

`CHATBOT_ENABLED`, context timeout, maximum rounds, retrieval switch, `top_k`, trigger rules, and group-statistics options are documented in `.env.prod.example`.

## Alibaba Cloud

```dotenv
ALIBABA_CLOUD_ACESS_KEY_ID=
ALIBABA_CLOUD_ACESS_KEY_SECRET=
```

`ACESS` is the project's current compatibility spelling. Use a dedicated least-privilege credential, never a root-account key.

The default ORM database configuration is:

```dotenv
SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///data/data.db
ALEMBIC_STARTUP_CHECK=false
```

Run the initialization script before the first startup so the schema and bundled content are present.

## Safety check

```bash
poetry run python scripts/check_open_source.py
git status --short
```

Stop before committing if local environment files, a database, or a JWT secret appears in the tracked change set.

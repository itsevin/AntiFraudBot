# 📦 Installation and deployment

[Documentation](README.md) · [简体中文](../安装部署.md) · [Configuration](configuration.md) · [Secure deployment](secure-deployment.md)

AntiFraudBot intentionally keeps its historical Poetry workflow. Keep backend packages inside the Poetry virtual environment; do not install them into the global Python or Conda base environment.

## Requirements

| Component | Recommended | Purpose |
|---|---|---|
| Python | `3.9–3.12` | NoneBot2, FastAPI, and database backend |
| Poetry | `2.x` | Isolated environment and lock file |
| Node.js | `22+` | Vue/Vite production build |
| Git | Current stable | Source and version control |
| OneBot 11 implementation | Current supported version | QQ connectivity |

## Install

```bash
git clone https://github.com/itsevin/AntiFraudBot.git
cd AntiFraudBot
poetry install
poetry env info
```

`poetry env info` should show a Poetry-managed virtual environment. Validate it:

```bash
poetry check --lock
poetry run python -m pip check
poetry run nb --help
```

## Configure

```bash
cp .env.example .env
cp .env.prod.example .env.prod
```

PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item .env.prod.example .env.prod
```

Set a strong dashboard password:

```dotenv
WEB_ADMIN_PASSWORD=CHANGE_ME_USE_AT_LEAST_12_CHARACTERS
```

Keep the dashboard on loopback by default:

```dotenv
WEB_HOST=127.0.0.1
WEB_PORT=8000
WEB_CORS_ORIGINS=["http://127.0.0.1:8000","http://localhost:8000"]
```

AI and Alibaba Cloud integrations are optional. Leave credentials empty and disable the corresponding feature when they are not used.

## Initialize data

```bash
poetry run python scripts/init_database.py
```

The script creates `data/data.db`, repairs known legacy schema differences, migrates compatible `data/data.json` preferences, imports `source/quiz_bank.json` and `source/keyword.txt`, and creates local configuration from the safe template when required.

## Build the dashboard

```bash
cd src/web/frontend_v2
npm ci
npm run build
cd ../../..
```

Generated `dist/` content remains local and is intentionally ignored.

## Configure OneBot 11

Configure your OneBot implementation to connect to the NoneBot OneBot V11 endpoint. A common reverse WebSocket target is:

```text
ws://127.0.0.1:8080/onebot/v11/ws
```

Confirm the exact path and authentication behavior in the documentation for your OneBot implementation. Never commit or screenshot its access token.

## Start

```bash
poetry run nb run
```

| Service | Default URL |
|---|---|
| NoneBot / OneBot | `http://127.0.0.1:8080` |
| Dashboard login | `http://127.0.0.1:8000/#/login` |

## Verify

```bash
poetry run pytest -q
poetry run ruff check src scripts tests
poetry run python scripts/check_open_source.py
```

Then log in to the dashboard, send `帮助` to the bot, run a quiz or check-in, and verify that local configuration and database files do not appear in `git status`.

## Upgrade

Back up local configuration and the database first:

```bash
git pull --ff-only
poetry install
poetry run python scripts/init_database.py

cd src/web/frontend_v2
npm ci
npm run build
```

Restart and repeat the verification checklist.

## Troubleshooting

- **`nb` is missing:** rerun `poetry install` and use `poetry run nb --help`; do not install it globally.
- **`nb` reports a legacy project format:** this is an `nb-cli 1.7` migration notice, not database or source corruption. The current NoneBot2 runtime still requires list-style `[tool.nonebot]` values; the automated migration is incompatible with the pinned Pydantic 1 stack, while the equivalent manual format prevents NoneBot from loading `plugins`. Ignore the notice until the upstream runtime and CLI support the same format, and do not force-upgrade global dependencies to hide it.
- **The page says it is being upgraded:** build the frontend `dist/` directory.
- **Login returns 503:** configure a non-default password with at least 12 characters.
- **Login returns 429:** wait for the failure window to expire and verify the password.
- **The quiz is empty:** confirm `source/quiz_bank.json` exists and rerun initialization.
- **AI or URL checks fail:** verify feature flags, endpoint, model, permissions, quota, and network access without posting credentials publicly.

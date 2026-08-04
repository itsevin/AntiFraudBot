# 🤝 Contributing to AntiFraudBot / 参与贡献

Thank you for improving AntiFraudBot. 感谢你为反诈教育和社区安全贡献代码、内容与经验。

## 🧭 Before you start / 开始之前

- Search existing issues and pull requests before opening a duplicate.
- For a substantial architecture change, open a proposal issue first.
- Report vulnerabilities privately according to [SECURITY.md](SECURITY.md).
- Never include real QQ IDs, chat histories, databases, credentials, or private service URLs.
- Educational images, cases, keywords, and quiz questions must include a clear source and redistribution basis.

## 🛠️ Development setup / 开发环境

The backend intentionally keeps the historical Poetry workflow. Dependencies must stay inside the Poetry virtual environment; do not install project packages into the user's global Python or Conda environment.

后端继续使用项目原有的 Poetry 工作流。请将依赖保持在 Poetry 虚拟环境中，不要把项目依赖安装进用户的全局 Python 或 Conda 环境。

```bash
poetry install
cp .env.example .env
cp .env.prod.example .env.prod

cd src/web/frontend_v2
npm ci
```

PowerShell:

```powershell
poetry install
Copy-Item .env.example .env
Copy-Item .env.prod.example .env.prod
Set-Location src/web/frontend_v2
npm ci
```

## ✅ Required checks / 必须通过的检查

```bash
poetry run pytest -q
poetry run ruff check src scripts tests
poetry run python scripts/check_open_source.py
poetry check --lock

cd src/web/frontend_v2
npm run build
```

Pull requests that change rendered behavior should also include a browser smoke test and screenshots with private data removed.

## 🧩 Change guidelines / 变更原则

### Backend

- Enforce authentication and authorization at a shared boundary rather than relying on frontend route guards.
- Bound user-controlled pagination, limits, time ranges, and text lengths.
- Use async I/O in request and bot-event paths.
- Avoid logging message bodies, tokens, credentials, or complete user identifiers.
- Add a regression test for every security or behavior fix.

### Frontend

- Reuse the shared authenticated API client.
- Handle loading, authentication failure, empty data, and request errors explicitly.
- Preserve keyboard focus, readable contrast, and mobile-safe layouts.
- Do not commit generated `dist/` or `node_modules/` content.

### Documentation

- Update both Chinese and English documentation for configuration or behavior changes.
- Prefer exact commands and real file paths over vague descriptions.
- Label optional, partial, heuristic, simulated, or externally billed features honestly.

### Educational content

- Do not submit scraped or copyrighted material without redistribution permission.
- Remove personal names, phone numbers, account identifiers, QR codes, and case-specific private data.
- Explain the source, license, and intended educational use in the pull request.

## 📝 Commit and pull request style / 提交规范

Keep commits focused and describe the outcome in the imperative mood. Examples:

```text
fix: require JWT authentication for dashboard APIs
docs: add bilingual deployment guide
test: cover weak admin password rejection
content: add sourced telecom-fraud quiz questions
```

In the pull request, describe:

1. the user problem;
2. the chosen solution;
3. security and compatibility effects;
4. commands run and results;
5. screenshots for visible changes;
6. remaining limitations.

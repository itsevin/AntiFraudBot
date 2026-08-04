# Changelog / 更新日志

All notable changes are documented here. 本文件记录值得关注的行为、兼容性和安全变化。

## [Unreleased]

### Security / 安全

- Require JWT authentication for all dashboard business APIs.
- Reject missing, short, and common default administrator passwords.
- Add login throttling, explicit CORS allowlists, and identifier masking.
- Add repository and Git-history secret checks in CI.

### Added / 新增

- Bilingual project documentation and contribution workflows.
- Reproducible backend tests and frontend build checks.
- Safe `.env` templates and an open-source readiness checker.
- GitHub issue forms, pull request template, Dependabot, and CI.

### Fixed / 修复

- Redesign both README landing sections with the project logo, focused badges, a real dashboard screenshot, and readable navigation.
- Remove obsolete slogan and organization-specific positioning from project documentation.
- Report only the 588 deduplicated keyword entries in bundled-content summaries.
- Add the missing NoneBot CLI runtime dependency.
- Use a single `source/quiz_bank.json` path across code and documentation.
- Restore real legacy JSON configuration migration behavior.
- Import the SQLAlchemy `delete` operation used by database initialization.
- Add a temporary-database schema regression test for initialization.
- Repair the dashboard layout for 390 px mobile viewports without changing the desktop composition.
- Refresh the frontend lockfile to resolve all reported npm dependency vulnerabilities.

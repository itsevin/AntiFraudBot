# 🔐 Security Policy / 安全策略

[English](#english) · [简体中文](#简体中文)

## English

### Supported versions

Security fixes are applied to the latest commit on the `main` branch. Older snapshots are not maintained as separate release lines unless a release note explicitly says otherwise.

### Reporting a vulnerability

Please **do not open a public issue** for authentication bypasses, credential exposure, remote code execution, private-data disclosure, or other exploitable behavior.

Use [GitHub Private Vulnerability Reporting](https://github.com/itsevin/AntiFraudBot/security/advisories/new) and include:

- the affected commit or version;
- the vulnerable route, plugin, or data flow;
- reproduction steps or a minimal proof of concept;
- expected and observed behavior;
- impact and deployment assumptions;
- any suggested remediation, if available.

Remove real QQ identifiers, access tokens, API keys, chat messages, and database contents from the report. If a minimal sample needs sensitive data, replace it with deterministic test values.

### Response expectations

Maintainers will aim to acknowledge a complete report within seven days. Timelines for validation, remediation, and disclosure depend on severity and reproducibility. Please allow time for a fix and coordinated disclosure before publishing technical details.

### Deployment responsibility

AntiFraudBot is not a hosted service. Operators are responsible for HTTPS termination, network access control, strong administrator credentials, service-provider permissions, backups, log retention, and compliance with local privacy requirements.

## 简体中文

### 支持范围

安全修复默认应用于 `main` 分支最新提交。除非发布说明另有声明，旧快照不会作为独立维护分支持续获得安全更新。

### 报告漏洞

请不要通过公开 Issue 披露鉴权绕过、凭据泄露、远程代码执行、隐私数据暴露或其他可利用问题。

请使用 [GitHub 私密漏洞报告](https://github.com/itsevin/AntiFraudBot/security/advisories/new)，并尽量提供：

- 受影响的提交或版本；
- 存在问题的接口、插件或数据流；
- 可复现步骤或最小化 PoC；
- 预期行为和实际行为；
- 影响范围及成立前提；
- 可选的修复建议。

提交前必须移除真实 QQ 号、Token、API Key、聊天内容和数据库数据。需要示例时，请使用确定性的测试值替代。

### 响应预期

维护者将尽量在七日内确认内容完整的报告。验证、修复和披露时间取决于问题严重性和复现情况。请在修复和协调披露完成前避免公开技术细节。

### 部署者责任

AntiFraudBot 不是托管服务。部署者需要自行负责 HTTPS、网络访问控制、强管理员密码、第三方服务权限、备份、日志保留以及当地隐私合规要求。

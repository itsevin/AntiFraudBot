# AntiFraudBot Web Console

[中文](#中文) · [English](#english)

## 中文

这是 AntiFraudBot 的 Vue 3 + Vite 管理大屏。前端通过共享 Axios 客户端访问受 JWT 保护的后端 API；未认证访问会返回登录页。

```bash
npm ci
npm run build
```

- 开发服务器：`npm run dev`
- 生产构建：`npm run build`
- 构建产物：`dist/`（已忽略，不应提交）
- 后端与安全配置：参见 [`docs/配置参考.md`](../../../docs/配置参考.md) 与 [`docs/安全部署.md`](../../../docs/安全部署.md)

请勿在前端源码、构建参数或浏览器存储之外持久化服务端密钥。管理员密码和 JWT 配置只应由后端环境变量管理。

## English

This directory contains the Vue 3 + Vite command-center UI. A shared Axios client calls JWT-protected backend APIs and redirects unauthenticated users to the login route.

```bash
npm ci
npm run build
```

- Development server: `npm run dev`
- Production build: `npm run build`
- Build output: `dist/` (ignored and never committed)
- Backend and security configuration: see [`docs/en/configuration.md`](../../../docs/en/configuration.md) and [`docs/en/secure-deployment.md`](../../../docs/en/secure-deployment.md)

Never embed server credentials in frontend source or build-time variables. Administrator passwords and JWT settings belong in backend environment configuration only.

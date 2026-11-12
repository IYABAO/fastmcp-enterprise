# Changelog

## 2026-11-12

### Added

- 新增 `GET /health` HTTP 路由，返回 `status/server/version`，与 `deploy/k8s/deployment.yaml` 中 readiness/liveness 探针的 `/health` 路径对齐。
- 新增 ASGI 级测试，实际请求 `/health` 并校验 200 与响应字段，避免 K8s 探针配置存在但服务端没有对应路由。

### Tests

- 测试用例从 13 个增加到 14 个。

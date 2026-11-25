# Changelog

## 2026-11-25

### Added

- 新增 Prometheus `/metrics` 端点，输出工具调用数、异常数、耗时总和/次数、限流放行与拒绝数，可直接接入 Prometheus/Grafana。
- 新增 `METRICS_ENABLED` 配置（默认 `true`），关闭后 `/metrics` 返回 404。
- 指标只保留聚合计数与耗时，不记录入参、出参、token 或 client_id。

### Fixed

- 审计中间件按 FastMCP `CallToolRequestParams` 读取工具名与参数，修复审计日志中 `tool`/`params` 为空的问题。

### Tests

- 新增 5 个指标测试，覆盖文本渲染、工具调用计数、异常计数、限流拒绝计数、端点开关。
- 测试用例从 14 个增加到 19 个。

## 2026-11-12

### Added

- 新增 `GET /health` HTTP 路由，返回 `status/server/version`，与 `deploy/k8s/deployment.yaml` 中 readiness/liveness 探针的 `/health` 路径对齐。
- 新增 ASGI 级测试，实际请求 `/health` 并校验 200 与响应字段，避免 K8s 探针配置存在但服务端没有对应路由。

### Tests

- 测试用例从 13 个增加到 14 个。

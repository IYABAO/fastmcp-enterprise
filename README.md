# Enterprise MCP Server Template

> 基于 **FastMCP 4.x** 构建的企业级 MCP Server 脚手架：开箱即用的鉴权、限流、数据脱敏、审计日志与会话隔离，可直接部署到 Kubernetes。
> An enterprise-grade **Model Context Protocol** server scaffold built on FastMCP: auth, rate limiting, desensitization, audit logging and session isolation out of the box, K8s-ready.

[![CI](https://github.com/IYABAO/fastmcp-enterprise/actions/workflows/ci.yml/badge.svg)](https://github.com/IYABAO/fastmcp-enterprise/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastMCP](https://img.shields.io/badge/FastMCP-4.0.0-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 为什么需要这个模板？

把 MCP Server 从「本地 Demo」推向「生产环境」，需要解决一堆协议之外的企业级问题：

| 关注点 | 本地 Demo | 生产环境要求 |
| --- | --- | --- |
| 谁能调用 | 随便 | **Token 鉴权 / 多租户隔离** |
| 调用多快 | 无限制 | **限流，防滥用** |
| 数据泄露 | 不关心 | **手机号/身份证/邮箱脱敏** |
| 出了问题 | 无人知晓 | **审计日志：谁在何时调了什么** |
| 怎么部署 | 本地跑 | **Docker / K8s / CI** |

这个模板把这些横切能力全部内置，你只需要关注**业务 Tools**。

## 特性 Features

- 🔐 **企业级鉴权**：Bearer Token AuthProvider（可扩展 JWT / OAuth2 / mTLS）
- 🛡 **数据脱敏**：手机号、身份证、邮箱等 PII 自动脱敏（字段级 + 正则级）
- ⏱ **限流**：滑动窗口限流器，按客户端维度（可替换 Redis 多实例共享）
- 📋 **审计日志**：记录每次工具调用的调用方 / 时间 / 入参 / 出参
- 🧩 **会话隔离**：多租户数据隔离，不同 client 只见自己的数据
- 📦 **开箱即用**：自带简历检索、人才画像示例业务工具
- 🚀 **部署就绪**：Dockerfile / docker-compose / K8s Deployment / GitHub Actions CI
- 🧪 **测试完备**：单元 + 集成测试（14 个用例），可直接跑 CI

## 快速开始 Quick Start

### 1. 安装

```bash
git clone git@github.com:IYABAO/fastmcp-enterprise.git
cd fastmcp-enterprise
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[test]"
```

### 2. 配置

```bash
cp .env.example .env
# 按需修改 token、限流阈值等
```

### 3. 启动（HTTP 模式）

```bash
python -m enterprise_mcp.server
# 默认 http://0.0.0.0:8080/mcp
```

### 4. 用 MCP 客户端连接

```python
from fastmcp import Client

async with Client("http://localhost:8080/mcp", auth="你的-token") as client:
    tools = await client.list_tools()          # 列出工具
    result = await client.call_tool("resume_search", {"query": {"keyword": "MCP", "min_years": 5}})
```

无 token 或 token 错误会被 **401 拒绝**。

### 5. 本地调试（STDIO 模式）

配合 Claude Code / Cursor 本地调用：

```bash
python -m enterprise_mcp.server --stdio
```

## 项目结构 Structure

```
fastmcp-enterprise/
├── src/enterprise_mcp/
│   ├── server.py              # 入口：组装全部能力
│   ├── config/settings.py     # 配置管理（env / .env）
│   ├── auth/
│   │   ├── authenticator.py   # Token 校验 + 会话注册表
│   │   └── provider.py        # FastMCP AuthProvider 实现
│   ├── middleware/
│   │   ├── middleware.py      # 审计 / 脱敏 / 会话隔离 / 限流中间件
│   │   ├── desensitize.py     # PII 脱敏引擎
│   │   ├── audit.py           # 审计日志器
│   │   └── rate_limiter.py    # 滑动窗口限流器
│   └── tools/
│       └── demo_tools.py      # 示例业务工具（简历检索等）
├── deploy/
│   ├── docker/                # Dockerfile + docker-compose
│   └── k8s/                   # K8s Deployment + Service + Ingress
├── tests/                     # 单元 + 集成测试
├── examples/                  # 客户端示例
└── .github/workflows/ci.yml   # GitHub Actions
```

## 配置项 Configuration

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `AUTH_ENABLED` | `true` | 是否启用 Token 鉴权 |
| `API_TOKENS` | `dev-token-123,dev-token-456` | 允许的 Token 列表（逗号分隔） |
| `RATE_LIMIT_ENABLED` | `true` | 是否启用限流 |
| `RATE_LIMIT_PER_MINUTE` | `60` | 每客户端每分钟最大请求数 |
| `DESENSITIZE_ENABLED` | `true` | 是否启用响应脱敏 |
| `DESENSITIZE_FIELDS` | `phone,id_card,...` | 需要脱敏的字段名 |
| `AUDIT_ENABLED` | `true` | 是否启用审计日志 |
| `AUDIT_OUTPUT` | `console` | 审计输出：`console` / `file` |
| `REDIS_ENABLED` | `false` | 是否启用 Redis（跨实例限流/会话） |
| `HOST` / `PORT` | `0.0.0.0` / `8080` | HTTP 监听地址 |

## 部署 Deployment

### Docker Compose

```bash
cd deploy/docker
docker compose up -d --build
```

### Kubernetes

```bash
kubectl apply -f deploy/k8s/deployment.yaml
# 生产环境建议：
# 1. Token 通过 Secret 注入（见 deployment.yaml 注释）
# 2. Redis 开启后支持多副本共享限流
# 3. 接入 Ingress + mTLS
```

`deployment.yaml` 的 readiness/liveness 探针请求 `/health`；该路由由 `server.py` 内置返回 `{"status":"ok"}`，可直接用于 K8s 健康检查。

## 如何扩展你的业务 Tools

在 `src/enterprise_mcp/tools/` 下新建模块，注册即可：

```python
# src/enterprise_mcp/tools/my_tools.py
from pydantic import BaseModel, Field
from fastmcp import FastMCP

def register_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def your_tool(query: YourQuery) -> dict:
        """你的工具描述（LLM 会看到）。"""
        return {"result": "..."}
```

然后在 `server.py` 中调用 `register_tools(mcp)`。

## 测试 Tests

```bash
pytest tests/ -v
# 14 passed
```

## Roadmap

- [ ] Redis 多实例限流 / 会话共享实现
- [ ] JWT / OAuth2 鉴权 Provider 示例
- [ ] Prometheus 指标暴露
- [ ] OpenTelemetry 链路追踪

## License

MIT

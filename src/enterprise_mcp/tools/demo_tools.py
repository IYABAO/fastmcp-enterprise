"""Enterprise MCP - Demo Business Tools.

示例业务工具集（与你简历中的核心场景呼应）：
- resume_search: 简历检索（模拟 ES 检索返回）
- candidate_profile: 人才画像分析
- health_check: 服务健康检查

这些工具演示企业级 MCP 工具的标准写法：
- Pydantic 输入校验
- 文档字符串作为 LLM 可见的工具说明
- 返回结构化结果
"""

from __future__ import annotations

from typing import Any

from enterprise_mcp.auth.authenticator import SessionRegistry
from fastmcp import FastMCP
from fastmcp.server.context import Context
from pydantic import BaseModel, Field

# 模拟人才库（生产环境应替换为 ES / MySQL）
_DEMO_RESUMES = [
    {
        "id": "R-1001",
        "name": "张伟",
        "phone": "13812345678",
        "email": "zhangwei@example.com",
        "years": 8,
        "skills": ["Go", "gRPC", "Kubernetes", "Redis"],
        "title": "资深后端工程师",
        "summary": "主导过 QPS 5000+ 的微服务重构，精通分布式缓存一致性方案。",
    },
    {
        "id": "R-1002",
        "name": "李娜",
        "phone": "13987654321",
        "email": "lina@example.com",
        "years": 12,
        "skills": ["Elasticsearch", "Go", "MCP", "FastMCP"],
        "title": "AI 架构师",
        "summary": "基于 FastMCP 构建企业级 Skills 服务，擅长 AI Agent 与检索中台。",
    },
    {
        "id": "R-1003",
        "name": "王强",
        "phone": "13711112222",
        "email": "wangqiang@example.com",
        "years": 5,
        "skills": ["Python", "FastAPI", "MySQL", "RabbitMQ"],
        "title": "Python 后端工程师",
        "summary": "负责消息异步削峰与报表系统，熟悉招聘平台业务。",
    },
]

_session_registry = SessionRegistry()


class ResumeQuery(BaseModel):
    """简历检索参数。"""

    keyword: str = Field(..., description="检索关键词（技能/职位/姓名）")
    min_years: int = Field(default=0, ge=0, description="最低工作年限过滤")
    limit: int = Field(default=10, ge=1, le=50, description="返回条数上限")


class ProfileQuery(BaseModel):
    """人才画像分析参数。"""

    resume_id: str = Field(..., description="简历 ID")


def register_tools(mcp: FastMCP) -> None:
    """把示例工具注册到 MCP Server。"""

    @mcp.tool()
    async def resume_search(query: ResumeQuery, ctx: Context) -> dict[str, Any]:
        """在海量人才库中检索符合条件的简历，支持关键词与工作年限过滤。

        Args:
            query: 检索参数（关键词、最低年限、返回条数）
        """
        # 会话隔离：每个 client 只能看到自己的数据（demo 中同一份数据）
        client_id = "unknown"
        rs = getattr(ctx, "request_state", None)
        if rs:
            client_id = rs.get("client_id", "unknown")

        kw = query.keyword.lower()
        results = [
            r
            for r in _DEMO_RESUMES
            if (kw in r["name"].lower() or kw in " ".join(r["skills"]).lower() or kw in r["title"].lower())
            and r["years"] >= query.min_years
        ][: query.limit]

        return {
            "client_id": client_id,
            "total": len(results),
            "results": results,
        }

    @mcp.tool()
    async def candidate_profile(query: ProfileQuery) -> dict[str, Any]:
        """根据简历 ID 获取候选人完整画像（脱敏后）。

        Args:
            query: 简历 ID
        """
        for r in _DEMO_RESUMES:
            if r["id"] == query.resume_id:
                # 返回前字段会经过 DesensitizeMiddleware 脱敏
                return {"resume": r}
        return {"error": f"resume {query.resume_id} not found"}

    @mcp.tool()
    async def health_check() -> dict[str, Any]:
        """服务健康检查，返回运行状态与版本。"""
        return {"status": "ok", "service": "enterprise-mcp", "version": "0.1.0"}

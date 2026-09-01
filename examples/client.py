"""Enterprise MCP - MCP Client 调用示例。

演示如何用 fastmcp 官方客户端连接并调用企业级 MCP Server。
"""

import asyncio

from fastmcp import Client

SERVER_URL = "http://localhost:8080/mcp"
API_TOKEN = "dev-token-123"  # 与 .env 中的 API_TOKENS 保持一致


async def main() -> None:
    async with Client(SERVER_URL, auth=API_TOKEN) as client:
        # 1. 列出工具
        print("=== 工具列表 ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f" - {tool.name}: {tool.description}")

        # 2. 调用工具
        print("\n=== 调用 resume_search ===")
        result = await client.call_tool(
            "resume_search",
            {"query": {"keyword": "MCP", "min_years": 5, "limit": 5}},
        )
        print(result.content[0].text)

        # 3. 调用人才画像（观察脱敏效果）
        print("\n=== 调用 candidate_profile（脱敏后） ===")
        result2 = await client.call_tool(
            "candidate_profile", {"query": {"resume_id": "R-1002"}}
        )
        print(result2.content[0].text)

        # 4. 健康检查
        print("\n=== 健康检查 ===")
        result3 = await client.call_tool("health_check", {})
        print(result3.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())

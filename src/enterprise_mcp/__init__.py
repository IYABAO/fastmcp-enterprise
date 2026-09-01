"""Enterprise MCP - 企业级 MCP Server 模板。

基于 FastMCP 构建的企业级 Model Context Protocol 服务模板，
内置鉴权、限流、脱敏、审计日志与会话隔离能力，可直接部署到 K8s。

示例：
    python -m enterprise_mcp.server            # HTTP 模式
    python -m enterprise_mcp.server --stdio    # STDIO 模式
"""

__version__ = "0.1.0"

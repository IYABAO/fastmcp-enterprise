# Enterprise MCP Server - Production Image
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 依赖层（利用缓存加速构建）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用层
COPY . .

# 使用非 root 用户运行（安全最佳实践）
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# 默认 HTTP 模式启动
CMD ["python", "-m", "enterprise_mcp.server"]

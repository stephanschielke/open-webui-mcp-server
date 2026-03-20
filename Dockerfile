ARG PYTHON_VERSION=3.10
ARG UV_VERSION=0.10.11

ARG MCP_TRANSPORT=http
ARG MCP_HTTP_HOST=0.0.0.0
ARG MCP_HTTP_PORT=8000
ARG MCP_HTTP_PATH=/mcp

FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# Install uv for faster package installation
RUN pip install --no-cache-dir uv=="${UV_VERSION}"

# Copy pyproject.toml for dependency installation
COPY pyproject.toml uv.lock README.md  ./

# Install dependencies
RUN uv --python-preference=only-system sync --locked --no-install-project

# Copy application code
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT="${MCP_TRANSPORT}"
ENV MCP_HTTP_HOST="${MCP_HTTP_HOST}"
ENV MCP_HTTP_PORT="${MCP_HTTP_PORT}"
ENV MCP_HTTP_PATH="${MCP_HTTP_PATH}"

# Expose MCP port
EXPOSE "${MCP_HTTP_PORT}"

# Run the MCP server
CMD ["uv", "run", "python", "-m", "src.openwebui_mcp.main"]

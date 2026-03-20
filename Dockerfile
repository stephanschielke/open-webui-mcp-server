ARG PYTHON_VERSION="3.10"
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# Install uv for faster package installation
ARG UV_VERSION="0.10.12"
RUN pip install --no-cache-dir uv=="${UV_VERSION}"

# Copy pyproject.toml for dependency installation
COPY pyproject.toml uv.lock README.md  ./

# Install dependencies
RUN uv --python-preference=only-system sync --locked --no-install-project

# Copy application code
COPY src/ ./src/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT="http"
ENV MCP_HTTP_HOST="0.0.0.0"
ENV MCP_HTTP_PORT=8000
ENV MCP_HTTP_PATH="/mcp"

# Expose MCP port
EXPOSE ${MCP_HTTP_PORT}

# Run the MCP server
CMD ["uv", "run", "python", "-m", "src.openwebui_mcp.main"]

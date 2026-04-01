# AGENTS.md - Open WebUI MCP Server

**Purpose**: Guidelines for agentic coding agents working on this repository.

## Project Overview

Python-based MCP (Model Context Protocol) server for Open WebUI. Auto-generates ~317 tools from OpenWebUI's OpenAPI spec using FastMCP v3. Built with `fastmcp>=3`, `httpx`, `pydantic`, and `uvicorn`.

## Architecture

Tools are auto-generated from `src/openwebui_mcp/specs/open-webui.openapi.json` via `FastMCP.from_openapi()`. No handcrafted tool definitions. Auth passthrough injects per-request Bearer tokens.

```
src/openwebui_mcp/
├── __init__.py          # Package init
├── main.py              # CLI entry point, transport selection
├── auth.py              # Context-var token storage, ASGI middleware
├── openapi_provider.py  # OpenAPI loader, AuthTransport, route curation
└── specs/
    └── open-webui.openapi.json  # OpenAPI spec (bundled in wheel)
```

## Quick Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Lint (Ruff)
ruff check src/ tests/

# Format
ruff format .

# Run integration tests (requires Docker Compose)
WEBUI_API_KEY=$(cat .openwebui-api-key) WEBUI_URL="http://127.0.0.1:3000" \
  MCP_SERVER_URL="http://127.0.0.1:8000/mcp" \
  pytest tests/test_integration.py -v -m integration

# Run a single test
pytest tests/test_integration.py::TestUserEndpoints::test_get_current_user -v

# Build package
python -m build

# Start Docker Compose (Open WebUI + MCP server)
docker compose up -d

# Rebuild and restart MCP server container
docker compose up -d --build open-webui-mcp-server
```

## Code Style

- **Formatter/Linter**: Ruff — rules E, F, I, W — line length 100 — target Python 3.10+
- **Imports**: stdlib → third-party → local (Ruff auto-sorts)
- **Naming**: `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants
- **Types**: Annotate public function signatures; use `typing` module for complex types
- **Error Handling**: Raise exceptions; let callers decide handling; include context in messages

## MCP Tool Generation

Tools are auto-generated from the OpenAPI spec. Control which endpoints become tools via `RouteMap` in `openapi_provider.py`:

```python
RouteMap(pattern=r"^/ollama/.*", mcp_type=MCPType.EXCLUDE)
RouteMap(pattern=r"^/openai/.*", mcp_type=MCPType.EXCLUDE)
RouteMap(pattern=r"^/api/v1/analytics/.*", mcp_type=MCPType.EXCLUDE)
RouteMap(pattern=r"^/api/v1/evaluations/.*", mcp_type=MCPType.EXCLUDE)
RouteMap(pattern=r"^/api/v1/terminals/.*", mcp_type=MCPType.EXCLUDE)
RouteMap(pattern=r"^/api/v1/pipelines/.*", mcp_type=MCPType.EXCLUDE)
RouteMap(pattern=r"^/api/(?!v1/).*", mcp_type=MCPType.EXCLUDE)
RouteMap(mcp_type=MCPType.TOOL, mcp_tags={"openapi", "auto-generated"})
```

**Tool naming**: Derived from OpenAPI operationId (e.g., `get_users_api_v1_users`).

**Known issue**: `list_files_api_v1_files` returns `{"items": [], "total": 0}` but the OpenAPI spec declares an array output. FastMCP validates outputs and rejects this. Integration tests skip this case.

## Auth Flow

1. HTTP requests carry `Authorization: Bearer <token>` header
2. `AuthMiddleware` (ASGI) extracts token → sets `_current_user_token` context var
3. `AuthTransport` (httpx) reads context var → injects Bearer header on every outbound request
4. Fallback: `WEBUI_API_KEY` env var if no per-request token

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBUI_URL` | Yes | - | Open WebUI instance URL |
| `WEBUI_API_KEY` | No | - | Default API key (fallback) |
| `MCP_TRANSPORT` | No | `stdio` | `stdio` or `http` |
| `MCP_HTTP_HOST` | No | `127.0.0.1` | HTTP host |
| `MCP_HTTP_PORT` | No | `8000` | HTTP port |
| `MCP_HTTP_PATH` | No | `/mcp` | HTTP path |

## Docker

- Specs must be bundled in the wheel: `include = ["src/openwebui_mcp/specs/*.json"]` in `pyproject.toml`
- Dockerfile copies specs and runs `uv sync --locked` (installs project at build time)
- `PATH` includes `.venv/bin` so `openwebui-mcp` entry point is found

## Test Conventions

- All tests are integration tests (`@pytest.mark.integration`) — no unit tests (no handcrafted code to unit-test)
- Tests verify tool calls return non-null data across 14 endpoint categories
- Use `pytest.skip()` for known OpenAPI spec mismatches
- Test file: `tests/test_integration.py` (18 tests, ~150 lines)

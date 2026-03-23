# AGENTS.md - Open WebUI MCP Server

**Purpose**: Guidelines for agentic coding agents working on this repository.

## Project Overview

Python-based MCP (Model Context Protocol) server for Open WebUI. Exposes admin APIs as MCP tools for AI assistants. Built with FastMCP, httpx, Pydantic, and uvicorn.

## Quick Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Lint (Ruff - configured in pyproject.toml)
ruff check .
ruff check src/ tests/

# Format (Ruff)
ruff format .

# Run all tests
pytest

# Run a single test file
pytest tests/test_client_changes.py

# Run a single test function
pytest tests/test_client_changes.py::test_create_tool_payload -v

# Run only unit tests (exclude integration)
pytest -m "not integration"

# Run only integration tests
pytest -m integration
```

## Code Style Guidelines

### Formatting & Linting
- **Formatter**: Ruff (`ruff format`)
- **Linter**: Ruff with rules E, F, I, W (errors, pyflakes, imports, warnings)
- **Line length**: 100 characters
- **Target Python**: 3.10+

### Imports
- Follow Ruff's import sorting (isort-like)
- Group: stdlib → third-party → local
- Use explicit imports (no star imports)

### Naming
- **Functions/variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`

### Types
- Use type annotations on public function signatures
- Use `typing` module for complex types (Optional, List, Dict, etc.)
- Pydantic models for request/response structures

### Error Handling
- Raise exceptions for error conditions, don't return sentinel values
- Let callers decide handling
- Use descriptive error messages with context

### Pydantic Models
- Name parameter classes with `Param` suffix (e.g., `UserCreateParam`)
- Use `Optional` with explicit defaults
- Document optional fields clearly

### Project Structure
```
src/openwebui_mcp/
├── __init__.py      # Package init, exports
├── main.py          # CLI entry point, transport handling
├── auth.py          # Auth middleware, token management
├── client.py        # OpenWebUIClient HTTP wrapper
├── server.py        # MCP tool definitions
└── models.py        # Pydantic parameter models

tests/
├── test_client_changes.py    # Client payload tests
├── test_mcp_wrapper_logic.py # MCP wrapper tests
└── test_integration.py       # Integration tests (require docker-compose)
```

### Test Conventions
- Test files: `test_*.py`
- Use `@pytest.mark.asyncio` for async tests
- Use `@pytest.mark.integration` for tests requiring running Open WebUI
- Use `pytest -m "not integration"` to skip integration tests
- Mock `httpx.AsyncClient` for unit tests
- Tests verify exact payload shapes

### MCP Tools
- Each tool wraps an Open WebUI API endpoint
- Use `get_user_token()` to fetch current user's token
- List responses wrapped as `{"items": [...]}`
- Use Pydantic models for tool parameters

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WEBUI_URL` | Yes | - | Open WebUI instance URL |
| `WEBUI_API_KEY` | No | - | Default API key |
| `MCP_TRANSPORT` | No | `stdio` | `stdio` or `http` |
| `MCP_HTTP_HOST` | No | `127.0.0.1` | HTTP host |
| `MCP_HTTP_PORT` | No | `8000` | HTTP port |
| `MCP_HTTP_PATH` | No | `/mcp` | HTTP path |

## Common Tasks

### Running the server (stdio mode)
```bash
export WEBUI_URL=https://your-instance.com
openwebui-mcp
```

### Running the server (HTTP mode)
```bash
export WEBUI_URL=https://your-instance.com
export MCP_TRANSPORT=http
export MCP_HTTP_PORT=8000
openwebui-mcp
```

### Running with Docker
```bash
docker compose up -d
```

## Notes

- Integration tests require a running Open WebUI instance (use docker-compose)
- Token handling via `auth.py` uses context variables for thread-safe per-request token storage
- The `.opencode/` directory contains OpenCode-specific config, not runtime code
- Large files (>500 lines): `client.py`, `server.py`, `test_client_changes.py` - consider domain-based refactoring when modifying
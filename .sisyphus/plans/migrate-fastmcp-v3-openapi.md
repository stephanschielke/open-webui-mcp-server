# Migrate to FastMCP v3 + OpenAPI Auto-Generated Tools

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the handcrafted MCP server (82 tools, 44 failures) with a FastMCP v3 server auto-generated from OpenWebUI's OpenAPI spec, while preserving auth passthrough and curated tool quality.

**Architecture:** Use `FastMCP.from_openapi()` with OpenWebUI's `specs/open-webui.openapi.json` spec and a custom `httpx.AsyncClient` that injects the per-request user token. Route maps exclude noisy/internal endpoints and curate which become tools vs resources. The auth middleware pattern stays the same (ASGI extracts Bearer token → context var → injected into HTTP client).

**Tech Stack:** FastMCP v3, httpx, OpenAPI spec (386 paths, 29 tag groups), uvicorn, Python 3.10+

---

## Current State Assessment

The existing server has **82 handcrafted tools** across 14 categories. Integration testing against a live OpenWebUI instance (v0.8.12) revealed:

- **28 tools work** (list endpoints, create endpoints, get_current_user, system config reads)
- **44 tools fail** due to: wrong endpoint paths, OpenWebUI API limitations (405s), parameter name mismatches
- **5 skipped** (permission denied — expected for admin-only endpoints)

**Root cause:** Hand-maintained endpoint paths in `client.py` drift from OpenWebUI's actual API. The OpenAPI spec (`specs/open-webui.openapi.json`, 386 paths) is the single source of truth.

## File Plan

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | Modify | Bump fastmcp dep to `>=3.0.0,<4` |
| `src/openwebui_mcp/__init__.py` | Modify | Update version export |
| `src/openwebui_mcp/main.py` | Rewrite | v3 transport config, OpenAPI provider init |
| `src/openwebui_mcp/server.py` | **DELETE** | Replaced by OpenAPI auto-generation |
| `src/openwebui_mcp/client.py` | **DELETE** | Replaced by httpx client in OpenAPI provider |
| `src/openwebui_mcp/models.py` | **DELETE** | Pydantic param models no longer needed (OpenAPI generates them) |
| `src/openwebui_mcp/auth.py` | Keep + minor tweak | Context var + ASGI middleware stays the same |
| `src/openwebui_mcp/openapi_provider.py` | Create | OpenAPIProvider wrapper with auth injection, route maps, component customization |
| `tests/test_integration.py` | Rewrite | Integration tests against auto-generated tools |
| `tests/test_client_changes.py` | **DELETE** | Tests handcrafted client logic that no longer exists |
| `tests/test_mcp_wrapper_logic.py` | **DELETE** | Tests list-wrapping logic that no longer exists |
| `Dockerfile` | Modify | Update CMD for new module structure |
| `uv.lock` | Regenerate | After dependency changes |

---

### Task 1: Update Dependencies to FastMCP v3

**Files:**
- Modify: `pyproject.toml:53-54`
- Modify: `Dockerfile:8` (uv version fix for DNS issues)

- [ ] **Step 1: Update pyproject.toml dependencies**

```python
# Change line 54 from:
#     "fastmcp>=2.14.5",
# To:
dependencies = [
    "fastmcp>=3.0.0,<4",
    "httpx>=0.28.1",
    "pydantic>=2.12.5",
    "uvicorn>=0.42.0",
]
```

Remove the TODO comment on line 54.

- [ ] **Step 2: Fix Dockerfile uv install to not require specific version**

```dockerfile
# Change lines 7-8 from:
# ARG UV_VERSION="0.10.12"
# RUN pip install --no-cache-dir uv=="${UV_VERSION}"
# To:
RUN pip install --no-cache-dir uv
```

This avoids DNS resolution failures during Docker builds when PyPI retries fail on specific version pins.

- [ ] **Step 3: Update Dockerfile CMD for new module structure**

```dockerfile
# Change line 30 from:
# CMD ["uv", "run", "python", "-m", "src.openwebui_mcp.main"]
# To:
CMD ["uv", "run", "openwebui-mcp"]
```

Uses the entry point defined in pyproject.toml instead of module path.

- [ ] **Step 4: Regenerate lock file**

```bash
uv lock --upgrade-package fastmcp
```

Expected: lock file updated with fastmcp v3.x dependencies.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml Dockerfile uv.lock
git commit -m "deps: upgrade fastmcp to v3.x"
```

---

### Task 2: Create OpenAPI Provider with Auth Injection

**Files:**
- Create: `src/openwebui_mcp/openapi_provider.py`
- Modify: `src/openwebui_mcp/auth.py` (add `set_user_token` helper)

This is the core of the new architecture. Instead of handcrafted tools, we wrap OpenWebUI's OpenAPI spec with FastMCP's `OpenAPIProvider`, injecting the per-request user token into every HTTP call.

- [ ] **Step 1: Add set_user_token helper to auth.py**

```python
import os
from contextvars import ContextVar
from typing import Optional

_current_user_token: ContextVar[Optional[str]] = ContextVar("current_user_token", default=None)


def get_user_token() -> Optional[str]:
    token = _current_user_token.get()
    if token:
        return token
    return os.getenv("WEBUI_API_KEY")


def set_user_token(token: Optional[str]) -> None:
    _current_user_token.set(token)


class AuthMiddleware:
    """ASGI middleware to extract Authorization header and set context variable."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                _current_user_token.set(token)
        await self.app(scope, receive, send)
```

- [ ] **Step 2: Create openapi_provider.py**

```python
"""OpenAPI-based MCP provider for Open WebUI.

Wraps OpenWebUI's OpenAPI specification with FastMCP's OpenAPIProvider,
injecting per-request authentication and curating which endpoints become tools.
"""

import json
from pathlib import Path
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

from openwebui_mcp.auth import get_user_token

SPECS_DIR = Path(__file__).parent.parent.parent / "specs"


def _load_openapi_spec() -> dict[str, Any]:
    """Load OpenWebUI's OpenAPI specification."""
    spec_path = SPECS_DIR / "open-webui.openapi.json"
    with open(spec_path) as f:
        return json.load(f)


def _build_route_maps() -> list[RouteMap]:
    """Define which OpenAPI routes become MCP tools vs excluded.

    Strategy:
    - Exclude: ollama passthrough, openai passthrough, internal health/debug,
      untagged legacy endpoints, analytics, evaluations, terminals, pipelines
    - Include as tools: all /api/v1/* endpoints for users, groups, models,
      knowledge, files, prompts, memories, chats, folders, tools, functions,
      notes, channels, configs, retrieval, skills, tasks, audio, images, utils
    """
    return [
        # Exclude Ollama proxy endpoints (not MCP-relevant)
        RouteMap(
            pattern=r"^/ollama/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
        # Exclude OpenAI proxy endpoints
        RouteMap(
            pattern=r"^/openai/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
        # Exclude analytics
        RouteMap(
            pattern=r"^/api/v1/analytics/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
        # Exclude evaluations
        RouteMap(
            pattern=r"^/api/v1/evaluations/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
        # Exclude terminals
        RouteMap(
            pattern=r"^/api/v1/terminals/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
        # Exclude pipelines
        RouteMap(
            pattern=r"^/api/v1/pipelines/.*",
            mcp_type=MCPType.EXCLUDE,
        ),
        # Exclude legacy untagged API endpoints (non-v1)
        RouteMap(
            pattern=r"^/api/(?!v1/).*",
            mcp_type=MCPType.EXCLUDE,
        ),
        # Everything else becomes a tool
        RouteMap(
            mcp_type=MCPType.TOOL,
            mcp_tags={"openapi", "auto-generated"},
        ),
    ]


def _create_http_client() -> httpx.AsyncClient:
    """Create an HTTP client that injects the current user's token.

    The token is read from the context variable set by AuthMiddleware
    at request time, ensuring per-request auth passthrough.
    """
    base_url = get_user_token.__code__.co_consts  # placeholder, see below

    class AuthInjectingTransport(httpx.AsyncBaseTransport):
        """Transport that injects Bearer auth from context into every request."""

        def __init__(self, base_url: str):
            self._client = httpx.AsyncClient(base_url=base_url, timeout=60.0)

        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            token = get_user_token()
            if token:
                request.headers["Authorization"] = f"Bearer {token}"
            return await self._client.send(request)

    # We need WEBUI_URL at construction time
    import os
    webui_url = os.getenv("WEBUI_URL", "http://localhost:3000").rstrip("/")
    return httpx.AsyncClient(base_url=webui_url, timeout=60.0)


def create_mcp_server() -> FastMCP:
    """Create the MCP server from OpenWebUI's OpenAPI spec."""
    spec = _load_openapi_spec()
    route_maps = _build_route_maps()

    # Build httpx client with auth injection via event hooks
    import os
    webui_url = os.getenv("WEBUI_URL", "http://localhost:3000").rstrip("/")

    async def inject_auth(request: httpx.Request) -> None:
        token = get_user_token()
        if token:
            request.headers["Authorization"] = f"Bearer {token}"

    client = httpx.AsyncClient(
        base_url=webui_url,
        timeout=60.0,
        event_hooks={"request": [inject_auth]},
    )

    mcp = FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name="openwebui-mcp-server",
        route_maps=route_maps,
        tags={"openwebui"},
    )

    return mcp
```

Wait — the event_hooks approach won't work because httpx event_hooks are set at client construction and the client is shared. The auth token changes per-request. Let me use a custom transport instead.

**Corrected openapi_provider.py:**

```python
"""OpenAPI-based MCP provider for Open WebUI.

Wraps OpenWebUI's OpenAPI specification with FastMCP's OpenAPIProvider,
injecting per-request authentication and curating which endpoints become tools.
"""

import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastmcp import FastMCP
from fastmcp.server.openapi import MCPType, RouteMap

from openwebui_mcp.auth import get_user_token

SPECS_DIR = Path(__file__).parent.parent.parent / "specs"


def _load_openapi_spec() -> dict[str, Any]:
    """Load OpenWebUI's OpenAPI specification."""
    spec_path = SPECS_DIR / "open-webui.openapi.json"
    with open(spec_path) as f:
        return json.load(f)


def _build_route_maps() -> list[RouteMap]:
    """Define which OpenAPI routes become MCP tools vs excluded."""
    return [
        RouteMap(pattern=r"^/ollama/.*", mcp_type=MCPType.EXCLUDE),
        RouteMap(pattern=r"^/openai/.*", mcp_type=MCPType.EXCLUDE),
        RouteMap(pattern=r"^/api/v1/analytics/.*", mcp_type=MCPType.EXCLUDE),
        RouteMap(pattern=r"^/api/v1/evaluations/.*", mcp_type=MCPType.EXCLUDE),
        RouteMap(pattern=r"^/api/v1/terminals/.*", mcp_type=MCPType.EXCLUDE),
        RouteMap(pattern=r"^/api/v1/pipelines/.*", mcp_type=MCPType.EXCLUDE),
        RouteMap(pattern=r"^/api/(?!v1/).*", mcp_type=MCPType.EXCLUDE),
        RouteMap(mcp_type=MCPType.TOOL, mcp_tags={"openapi", "auto-generated"}),
    ]


class AuthTransport(httpx.AsyncBaseTransport):
    """Custom transport that injects Bearer auth from context per-request."""

    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=60.0)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        token = get_user_token()
        if token:
            request.headers["Authorization"] = f"Bearer {token}"
        # Ensure URL is absolute
        if not request.url.is_absolute:
            request.url = httpx.URL(f"{self._base_url}{request.url}")
        return await self._client.send(request)

    async def aclose(self) -> None:
        await self._client.aclose()


def create_mcp_server() -> FastMCP:
    """Create the MCP server from OpenWebUI's OpenAPI spec."""
    spec = _load_openapi_spec()
    route_maps = _build_route_maps()

    webui_url = os.getenv("WEBUI_URL", "http://localhost:3000")
    transport = AuthTransport(webui_url)
    client = httpx.AsyncClient(transport=transport, base_url=webui_url)

    mcp = FastMCP.from_openapi(
        openapi_spec=spec,
        client=client,
        name="openwebui-mcp-server",
        route_maps=route_maps,
        tags={"openwebui"},
    )

    return mcp
```

- [ ] **Step 3: Commit**

```bash
git add src/openwebui_mcp/auth.py src/openwebui_mcp/openapi_provider.py
git commit -m "feat: add OpenAPI provider with per-request auth injection"
```

---

### Task 3: Rewrite main.py for FastMCP v3

**Files:**
- Rewrite: `src/openwebui_mcp/main.py`

- [ ] **Step 1: Rewrite main.py for v3 transport config**

```python
"""Open WebUI MCP Server - Main entry point."""

import os
import sys

from openwebui_mcp.auth import AuthMiddleware
from openwebui_mcp.openapi_provider import create_mcp_server


def main():
    """Run the MCP server."""
    if not os.getenv("WEBUI_URL"):
        print("ERROR: WEBUI_URL environment variable is required", file=sys.stderr)
        print("Example: export WEBUI_URL=https://ai.example.com", file=sys.stderr)
        sys.exit(1)

    mcp = create_mcp_server()
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        host = os.getenv("MCP_HTTP_HOST", "127.0.0.1")
        port = int(os.getenv("MCP_HTTP_PORT", "8000"))
        path = os.getenv("MCP_HTTP_PATH", "/mcp")

        import uvicorn

        app = mcp.http_app(path=path)
        app = AuthMiddleware(app)
        print(f"Starting Open WebUI MCP server on http://{host}:{port}{path}", file=sys.stderr)
        uvicorn.run(app, host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
```

Key v3 changes:
- No more `FastMCP("name")` constructor with transport kwargs
- Transport config moved to `run()` / `http_app()` calls
- Server is created via `create_mcp_server()` which uses OpenAPI spec

- [ ] **Step 2: Commit**

```bash
git add src/openwebui_mcp/main.py
git commit -m "refactor: rewrite main.py for FastMCP v3 transport model"
```

---

### Task 4: Delete Handcrafted Server, Client, and Models

**Files:**
- Delete: `src/openwebui_mcp/server.py`
- Delete: `src/openwebui_mcp/client.py`
- Delete: `src/openwebui_mcp/models.py`

- [ ] **Step 1: Remove old files**

```bash
rm src/openwebui_mcp/server.py src/openwebui_mcp/client.py src/openwebui_mcp/models.py
```

- [ ] **Step 2: Verify no remaining imports reference deleted modules**

```bash
grep -r "from openwebui_mcp.server\|from openwebui_mcp.client\|from openwebui_mcp.models\|from openwebui_mcp import server\|from openwebui_mcp import client\|from openwebui_mcp import models" src/ tests/
```

Expected: no output (clean).

- [ ] **Step 3: Commit**

```bash
git add -u src/openwebui_mcp/server.py src/openwebui_mcp/client.py src/openwebui_mcp/models.py
git commit -m "refactor: remove handcrafted server/client/models replaced by OpenAPI provider"
```

---

### Task 5: Update Dockerfile and Docker Compose

**Files:**
- Modify: `Dockerfile`
- Modify: `compose.yaml`

- [ ] **Step 1: Update Dockerfile for new structure**

```dockerfile
ARG PYTHON_VERSION="3.10"
FROM python:${PYTHON_VERSION}-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY specs/ ./specs/

# Install dependencies
RUN uv --python-preference=only-system sync --locked --no-install-project

# Copy application code
COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT="http"
ENV MCP_HTTP_HOST="0.0.0.0"
ENV MCP_HTTP_PORT=7999
ENV MCP_HTTP_PATH="/mcp"

EXPOSE ${MCP_HTTP_PORT}

CMD ["uv", "run", "openwebui-mcp"]
```

Changes:
- Removed pinned UV_VERSION (DNS issue fix)
- Added `COPY specs/` for OpenAPI spec
- CMD uses entry point instead of module path

- [ ] **Step 2: Verify compose.yaml WEBUI_URL for container networking**

The compose.yaml already sets `WEBUI_URL: http://open-webui:2999` for the MCP server container. This is correct — the OpenAPI provider reads `WEBUI_URL` at construction time.

- [ ] **Step 3: Commit**

```bash
git add Dockerfile
git commit -m "fix: update Dockerfile for OpenAPI spec and v3 entry point"
```

---

### Task 6: Rewrite Integration Tests

**Files:**
- Rewrite: `tests/test_integration.py`
- Delete: `tests/test_client_changes.py`
- Delete: `tests/test_mcp_wrapper_logic.py`

- [ ] **Step 1: Delete old test files**

```bash
rm tests/test_client_changes.py tests/test_mcp_wrapper_logic.py
```

- [ ] **Step 2: Create new integration tests**

```python
"""Integration tests for OpenAPI-generated MCP tools.

Tests verify that auto-generated tools from the OpenAPI spec
properly connect to a running OpenWebUI instance.

Run with: pytest tests/test_integration.py -v -m integration
"""

import os

import httpx
import pytest
from fastmcp.client import Client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
WEBUI_URL = os.getenv("WEBUI_URL", "http://127.0.0.1:3000")

_api_key = ""
try:
    with open(".openwebui-api-key") as f:
        _api_key = f.read().strip()
except FileNotFoundError:
    _api_key = os.getenv("WEBUI_API_KEY", "")
WEBUI_API_KEY = _api_key


class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


async def get_openwebui_token():
    if WEBUI_API_KEY:
        return WEBUI_API_KEY
    admin_email = os.getenv("WEBUI_ADMIN_EMAIL", "")
    admin_password = os.getenv("WEBUI_ADMIN_PASSWORD", "password")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{WEBUI_URL}/api/v1/auths/signin",
            json={"email": admin_email, "password": admin_password},
        )
        if response.status_code == 200:
            return response.json().get("token", "")
    return ""


@pytest.fixture
async def auth_token():
    return await get_openwebui_token()


@pytest.fixture
async def mcp_client():
    auth = BearerAuth(WEBUI_API_KEY) if WEBUI_API_KEY else None
    async with Client(MCP_SERVER_URL, auth=auth) as client:
        yield client


@pytest.mark.integration
class TestServerConnectivity:
    async def test_server_responds(self, mcp_client):
        tools = await mcp_client.list_tools()
        assert len(tools) > 0

    async def test_tools_have_descriptions(self, mcp_client):
        tools = await mcp_client.list_tools()
        for tool in tools:
            assert tool.description, f"Tool {tool.name} has no description"


@pytest.mark.integration
class TestUserEndpoints:
    async def test_get_current_user(self, mcp_client):
        result = await mcp_client.call_tool("auths_get", {})
        assert result.data is not None
        assert isinstance(result.data, dict)

    async def test_list_users(self, mcp_client):
        result = await mcp_client.call_tool("users_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestGroupEndpoints:
    async def test_list_groups(self, mcp_client):
        result = await mcp_client.call_tool("groups_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestModelEndpoints:
    async def test_list_models(self, mcp_client):
        result = await mcp_client.call_tool("models_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestKnowledgeEndpoints:
    async def test_list_knowledge_bases(self, mcp_client):
        result = await mcp_client.call_tool("knowledge_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestFileEndpoints:
    async def test_list_files(self, mcp_client):
        result = await mcp_client.call_tool("files_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestChatEndpoints:
    async def test_list_chats(self, mcp_client):
        result = await mcp_client.call_tool("chats_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestPromptEndpoints:
    async def test_list_prompts(self, mcp_client):
        result = await mcp_client.call_tool("prompts_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestMemoryEndpoints:
    async def test_list_memories(self, mcp_client):
        result = await mcp_client.call_tool("memories_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestNoteEndpoints:
    async def test_list_notes(self, mcp_client):
        result = await mcp_client.call_tool("notes_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestChannelEndpoints:
    async def test_list_channels(self, mcp_client):
        try:
            result = await mcp_client.call_tool("channels_list", {})
            assert result.data is not None
        except Exception as e:
            if "403" in str(e):
                pytest.skip("Permission denied for channels")
            raise


@pytest.mark.integration
class TestConfigEndpoints:
    async def test_get_system_config(self, mcp_client):
        result = await mcp_client.call_tool("configs_export", {})
        assert result.data is not None
        assert isinstance(result.data, dict)

    async def test_get_banners(self, mcp_client):
        result = await mcp_client.call_tool("configs_banners", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestToolEndpoints:
    async def test_list_tools(self, mcp_client):
        result = await mcp_client.call_tool("tools_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestFunctionEndpoints:
    async def test_list_functions(self, mcp_client):
        result = await mcp_client.call_tool("functions_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))


@pytest.mark.integration
class TestFolderEndpoints:
    async def test_list_folders(self, mcp_client):
        result = await mcp_client.call_tool("folders_list", {})
        assert result.data is not None
        assert isinstance(result.data, (list, dict))
```

- [ ] **Step 3: Commit**

```bash
git add tests/
git commit -m "test: rewrite integration tests for OpenAPI-generated tools"
```

---

### Task 7: Smoke Test — Build, Start, Verify

**Files:** No file changes. This is a validation task.

- [ ] **Step 1: Run linting**

```bash
ruff check src/ tests/
```

Expected: All checks passed.

- [ ] **Step 2: Run unit tests (if any remain)**

```bash
pytest tests/ -v -m "not integration"
```

Expected: Tests pass (integration tests skipped without running OpenWebUI).

- [ ] **Step 3: Build package**

```bash
rm -rf dist
python -m build
```

Expected: `openwebui_mcp_server-0.2.2.tar.gz` and `.whl` built successfully.

- [ ] **Step 4: Install in fresh venv and start server**

```bash
python3 -m venv /tmp/mcp-v3-test
/tmp/mcp-v3-test/bin/pip install dist/openwebui_mcp_server-0.2.2-py3-none-any.whl
WEBUI_URL=http://127.0.0.1:3000 WEBUI_API_KEY=$(cat .openwebui-api-key) MCP_TRANSPORT=http /tmp/mcp-v3-test/bin/openwebui-mcp &
sleep 3
```

Expected: Server starts on http://127.0.0.1:8000/mcp without errors.

- [ ] **Step 5: Verify tool count**

```bash
curl -s -H "Accept: text/event-stream" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
  http://127.0.0.1:8000/mcp
```

Expected: Large list of tools (200+) from the OpenAPI spec, excluding ollama/openai/analytics/evaluations/terminals/pipelines.

- [ ] **Step 6: Run integration tests**

```bash
WEBUI_API_KEY=$(cat .openwebui-api-key) WEBUI_URL=http://127.0.0.1:3000 MCP_SERVER_URL=http://127.0.0.1:8000/mcp \
  pytest tests/test_integration.py -v -m integration
```

Expected: All list/read tests pass. Write tests may 403 depending on permissions.

- [ ] **Step 7: Kill test server**

```bash
pkill -f "openwebui-mcp"
```

- [ ] **Step 8: Commit (if any fixes needed from smoke test)**

---

## Self-Review

### Spec Coverage Check

| Requirement | Task | Status |
|-------------|------|--------|
| Migrate to FastMCP v3 | Task 1 (deps), Task 3 (main.py) | ✅ |
| Auto-generate tools from OpenAPI | Task 2 (openapi_provider.py) | ✅ |
| Remove handcrafted tools | Task 4 (delete server.py, client.py, models.py) | ✅ |
| Preserve auth passthrough | Task 2 (AuthTransport), Task 3 (AuthMiddleware) | ✅ |
| Exclude noisy endpoints | Task 2 (route maps for ollama/openai/analytics/etc.) | ✅ |
| Update tests | Task 6 (rewrite integration tests) | ✅ |
| Docker support | Task 5 (Dockerfile update) | ✅ |

### Placeholder Scan
- No TBD/TODO in code steps
- All code blocks contain complete implementations
- No "similar to Task N" references
- Error handling is explicit (AuthTransport handles missing token gracefully)

### Type Consistency
- `get_user_token()` returns `Optional[str]` — used consistently in AuthTransport and main.py
- `create_mcp_server()` returns `FastMCP` — used in main.py
- Route maps use `MCPType` and `RouteMap` from `fastmcp.server.openapi` — correct v3 import path

---

## Execution Handoff

Plan complete. Two execution options:

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?

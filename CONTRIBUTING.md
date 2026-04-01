# Contributing to Open WebUI MCP Server

Thank you for your interest in contributing! This guide will help you get started with development.

## Repository Information

- **Maintained Fork**: [stephanschielke/open-webui-mcp-server](https://github.com/stephanschielke/open-webui-mcp-server)
- **Original Repository**: [troylar/open-webui-mcp-server](https://github.com/troylar/open-webui-mcp-server)
- **Package**: [openwebui-mcp-server on PyPI](https://pypi.org/project/openwebui-mcp-server/)

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [mise](https://mise.jdx.dev/) (recommended for tool management)
- [Docker](https://www.docker.com/) (optional, for integration tests)

### Option 1: Using mise (Recommended)

```bash
# Install mise (if not already installed)
curl https://mise.run | sh

# Clone the repository
git clone https://github.com/stephanschielke/open-webui-mcp-server.git
cd open-webui-mcp-server

# Install all development tools (uv, ruff, etc.)
mise install

# Install dev dependencies and the package
mise run install-dev
```

### Option 2: Using uv directly

```bash
# Clone the repository
git clone https://github.com/stephanschielke/open-webui-mcp-server.git
cd open-webui-mcp-server

# Create virtual environment and install dependencies
uv lock
uv sync --extra="dev"
uv pip install -e ".[dev]"
```

### Option 3: Using pip

```bash
# Clone the repository
git clone https://github.com/stephanschielke/open-webui-mcp-server.git
cd open-webui-mcp-server

# Install in development mode
pip install -e ".[dev]"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
mise run owu:tests:all

# Or with uv directly
uv run pytest tests/ -v

# Run integration tests (requires Docker Compose)
WEBUI_API_KEY=$(cat .openwebui-api-key) WEBUI_URL="http://127.0.0.1:3000" \
  MCP_SERVER_URL="http://127.0.0.1:8000/mcp" \
  pytest tests/test_integration.py -v -m integration

# Run a single test
pytest tests/test_integration.py::TestUserEndpoints::test_get_current_user -v
```

### Running Integration Tests

Integration tests require a running Open WebUI instance. Use Docker Compose:

```bash
# Start services
mise run owu:compose:up

# Run integration tests
mise run owu:tests:integration

# Stop services
docker compose down
```

### Linting and Formatting

```bash
# Check for linting errors
mise run owu:linter:check

# Auto-fix linting issues
mise run owu:linter:fix

# Or with ruff directly
ruff check src/ tests/
ruff check --fix src/ tests/
```

### Running the Server Locally

```bash
# Set environment variables
export WEBUI_URL=http://localhost:3000
export WEBUI_API_KEY=your-api-key

# Run in stdio mode (default)
openwebui-mcp

# Run in HTTP mode
export MCP_TRANSPORT=http
export MCP_HTTP_PORT=8000
openwebui-mcp
```

## Project Structure

```
open-webui-mcp-server/
├── src/
│   └── openwebui_mcp/
│       ├── __init__.py           # Package init
│       ├── main.py               # CLI entry point, transport selection
│       ├── auth.py               # Context-var token storage, ASGI middleware
│       ├── openapi_provider.py   # OpenAPI loader, AuthTransport, route curation
│       └── specs/
│           └── open-webui.openapi.json  # OpenAPI spec (bundled in wheel)
├── tests/
│   └── test_integration.py       # Integration tests (requires Docker)
├── scripts/
│   └── init-api-key.sh           # Script to initialize API key
├── compose.yaml                  # Docker Compose configuration
├── Dockerfile                    # Docker image definition
├── pyproject.toml                # Project metadata and dependencies
└── mise.toml                     # mise task and tool configuration
```

## Architecture

### Core Components

1. **main.py**: Entry point that initializes the MCP server
   - Validates required environment variables
   - Configures transport (stdio or HTTP)
   - Wraps HTTP app with authentication middleware

2. **openapi_provider.py**: OpenAPI-based tool generation
   - Loads `specs/open-webui.openapi.json`
   - Creates `AuthTransport` (custom httpx transport that injects Bearer tokens)
   - Configures `RouteMap` exclusions (ollama, openai, analytics, etc.)
   - Calls `FastMCP.from_openapi()` to auto-generate ~317 tools

3. **auth.py**: Authentication handling
   - `_current_user_token` context variable for per-request token storage
   - `AuthMiddleware` (ASGI) extracts Bearer tokens from incoming requests
   - Falls back to `WEBUI_API_KEY` environment variable

### How Tools Are Generated

Tools are auto-generated from the OpenAPI spec — no handcrafted tool definitions. Each OpenAPI endpoint becomes an MCP tool with its name derived from the `operationId` (e.g., `get_users_api_v1_users`).

To exclude endpoints from becoming tools, add `RouteMap` entries in `openapi_provider.py`:

```python
RouteMap(pattern=r"^/api/v1/analytics/.*", mcp_type=MCPType.EXCLUDE)
```

### Updating the OpenAPI Spec

When Open WebUI adds new API endpoints:

```bash
# Dump the latest spec from a running Open WebUI instance
mise run owu:api:dump-spec

# Rebuild and restart
docker compose up -d --build open-webui-mcp-server
```

## Testing Guidelines

### Integration Tests

- All tests are integration tests (`@pytest.mark.integration`)
- Tests verify tool calls return non-null data across 14 endpoint categories
- Use `pytest.skip()` for known OpenAPI spec mismatches
- Test file: `tests/test_integration.py` (18 tests)

### Known Test Skip

`test_list_files` — The OpenAPI spec declares an array output but the actual API returns `{"items": [], "total": 0}`. FastMCP validates outputs and rejects this mismatch. This is an OpenAPI spec bug in Open WebUI.

## Docker Development

### Building the Image

```bash
# Build with Docker Compose
docker compose up -d --build open-webui-mcp-server

# Or standalone
docker build -t openwebui-mcp-server:dev .
```

### Running with Docker Compose

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f open-webui-mcp-server

# Rebuild and restart
docker compose up -d --build
```

### Dockerfile Notes

- `uv sync --locked` installs the project at build time (not runtime)
- `PATH` includes `.venv/bin` so `openwebui-mcp` entry point is found
- Specs are bundled in the wheel via `include = ["src/openwebui_mcp/specs/*.json"]`

## Local GitHub Actions Testing

We use [act](https://github.com/nektos/act) to test GitHub Actions workflows locally:

```bash
# Validate workflow syntax
mise run owu:gha:validate

# Run workflows locally
mise run owu:gha:act
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use type hints for all function signatures
- Write docstrings for public functions
- Keep functions focused and small
- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Ruff rules: E, F, I, W — line length 100 — target Python 3.10+

## Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Run tests and linter
5. Submit a pull request with a clear description

## Release Process

Releases are automated via GitHub Actions.

Quick release:

```bash
# Prepare a release (runs checks, bumps version, creates tag)
mise run release:prepare 0.2.2

# Push to trigger GitHub Actions
git push fork v0.2.2
```

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues and pull requests
- Review the [README.md](README.md) for usage information

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

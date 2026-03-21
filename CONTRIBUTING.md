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

[mise](https://mise.jdx.dev/) manages your development tools, environment, and tasks in one place:

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

# Run specific test file
uv run pytest tests/test_client_changes.py -v

# Run unit tests only (no Docker required)
uv run pytest tests/test_client_changes.py tests/test_mcp_wrapper_logic.py -v
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
ruff --config pyproject.toml check src/ tests/
ruff --config pyproject.toml check --fix src/ tests/
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
│       ├── __init__.py
│       ├── main.py          # Entry point and server startup
│       ├── server.py        # MCP tool definitions
│       ├── client.py        # Open WebUI API client
│       ├── auth.py          # Authentication middleware
│       └── models.py        # Pydantic models for parameters
├── tests/
│   ├── test_integration.py      # Integration tests (requires Docker)
│   ├── test_client_changes.py   # Unit tests for client
│   └── test_mcp_wrapper_logic.py # Tests for list wrapping
├── scripts/
│   └── init-api-key.sh      # Script to initialize API key
├── compose.yaml             # Docker Compose configuration
├── Dockerfile               # Docker image definition
├── pyproject.toml           # Project metadata and dependencies
└── mise.toml                # mise task and tool configuration
```

## Architecture

### Core Components

1. **main.py**: Entry point that initializes the MCP server
    - Validates required environment variables
    - Configures transport (stdio or HTTP)
    - Wraps HTTP app with authentication middleware

2. **server.py**: MCP tool definitions
    - Uses FastMCP decorators to define tools
    - Each tool calls the Open WebUI client
    - Handles list-to-dict wrapping for consistent responses

3. **client.py**: Open WebUI API client
    - Encapsulates all HTTP calls to Open WebUI
    - Passes user tokens via Bearer authentication
    - Provides high-level methods for each resource type

4. **auth.py**: Authentication handling
    - Extracts Bearer tokens from requests
    - Maintains per-request user context
    - Falls back to WEBUI_API_KEY environment variable

5. **models.py**: Parameter validation
    - Pydantic models for tool inputs
    - Ensures type safety for MCP tool parameters

### Adding a New Tool

1. Add a Pydantic model in `models.py`:

```python
class MyNewParam(BaseModel):
    name: str
    description: str | None = None
```

2. Add a client method in `client.py`:

```python
async def my_new_action(self, name: str, description: str | None = None, api_key: str | None = None) -> dict:
    payload = {"name": name}
    if description:
        payload["description"] = description
    return await self.post("/api/v1/my-endpoint", payload, api_key)
```

3. Add a tool in `server.py`:

```python
@mcp.tool()
async def my_new_tool(params: MyNewParam) -> dict[str, Any]:
    """Description of what this tool does."""
    return await get_client().my_new_action(params.name, params.description, get_user_token())
```

4. Add tests in `tests/test_client_changes.py`

## Testing Guidelines

### Unit Tests

- Test parameter validation and payload shapes
- Test list-to-dict wrapping logic
- No external dependencies required

### Integration Tests

- Require running Open WebUI instance
- Test actual API calls and responses
- Use Docker Compose for consistent environment

### Test Coverage

```bash
# Run tests with coverage
uv run pytest tests/ --cov=openwebui_mcp --cov-report=html
```

## Docker Development

### Building the Image

```bash
# Build locally
docker build -t openwebui-mcp-server:dev .

# Or with mise
mise run owu:docker:build
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

## Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Run tests and linter
5. Submit a pull request with a clear description

## Release Process

Releases are automated via GitHub Actions. See [PUBLISHING_GUIDE.md](.github/workflows/PUBLISHING_GUIDE.md) for details.

Quick release:

```bash
# Prepare a release (runs checks, bumps version, creates tag)
mise run release:prepare 0.2.1

# Push to trigger GitHub Actions
git push fork v0.2.1
```

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues and pull requests
- Review the [README.md](README.md) for usage information

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

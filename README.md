# Open WebUI MCP Server

[![PyPI version](https://img.shields.io/pypi/v/openwebui-mcp-server)](https://pypi.org/project/openwebui-mcp-server/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://github.com/stephanschielke/open-webui-mcp-server/actions/workflows/publish.yml/badge.svg)](https://github.com/stephanschielke/open-webui-mcp-server/actions)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes [Open WebUI](https://github.com/open-webui/open-webui)'s admin APIs as tools, allowing AI assistants to manage users, groups, models, knowledge bases, and more.

Built with [FastMCP v3](https://gofastmcp.com/) — tools are auto-generated from Open WebUI's OpenAPI spec (~317 tools). Designed for seamless integration with Claude Desktop, Open WebUI, and any MCP-compatible client.

## Features

- **User Management**: List, get, update roles, delete users
- **Group Management**: Create, update, add/remove members, delete groups
- **Model Management**: Create custom models, update system prompts, manage parameters
- **Knowledge Base Management**: Create, list, update, delete knowledge bases for RAG
- **File Management**: Upload, search, get content, delete files
- **Chat Management**: List, view, archive, share, delete chats
- **Prompt Management**: Create and manage prompt templates
- **Memory Management**: Add, query, update, delete memories
- **Notes Management**: Create and manage markdown notes
- **Channels (Team Chat)**: Create channels, post messages, manage conversations
- **Tool & Function Discovery**: List and manage available tools and functions
- **Permission-Aware**: All operations respect the logged-in user's permissions

## Security

**Important**: This server passes through the user's authentication token to Open WebUI. This means:

- Admin operations require admin API keys
- Regular users can only access their own resources
- All permission checks are enforced by Open WebUI's API
- No credentials are stored by the MCP server

## Installation

### From PyPI (Recommended)

```bash
pip install openwebui-mcp-server
```

Or with [uv](https://docs.astral.sh/uv/) (faster, no system Python required):

```bash
uv pip install openwebui-mcp-server
```

### From Source (Development)

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup.

## Quick Start

### 1. Configure Environment

Set the required environment variable:

```bash
export WEBUI_URL=https://your-openwebui-instance.com
```

Optionally, set a default API key:

```bash
export WEBUI_API_KEY=your-api-key
```

### 2. Run the Server

#### stdio Mode (Default for Claude Desktop)

```bash
openwebui-mcp
```

#### HTTP Mode (For Open WebUI Integration)

```bash
export MCP_TRANSPORT=http
export MCP_HTTP_PORT=8000
openwebui-mcp
```

The server will start at `http://localhost:8000/mcp`

## Usage with Claude Desktop

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "openwebui": {
      "command": "openwebui-mcp",
      "env": {
        "WEBUI_URL": "https://your-openwebui-instance.com",
        "WEBUI_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Usage with Open WebUI (via MCPO)

1. Start the server in HTTP mode:

```bash
export WEBUI_URL=https://your-openwebui-instance.com
export MCP_TRANSPORT=http
export MCP_HTTP_PORT=8001
openwebui-mcp
```

2. Add as MCP server in Open WebUI:
    - Go to **Admin Settings → External Tools**
    - Add new MCP server with URL: `http://localhost:8001/mcp`

## Usage with Docker

### Using Pre-built Image

```bash
docker run -d \
  -e WEBUI_URL=http://your-openwebui-instance:8080 \
  -e WEBUI_API_KEY=your-api-key \
  -p 8000:7999 \
  openwebui-mcp-server:latest
```

### Using Docker Compose

See the included `compose.yaml` for a complete setup with Open WebUI and Ollama:

```bash
docker compose up -d
```

This starts:
- Ollama (local LLM server)
- Open WebUI (web interface)
- MCP Server (accessible at `http://localhost:8000/mcp`)

## Available Tools

This server auto-generates ~317 MCP tools from Open WebUI's OpenAPI spec. Tool names follow the pattern `{operationId}` (e.g., `get_users_api_v1_users`). Below are the main categories covered:

### User Management

| Tool               | Description                      | Permission |
|--------------------|----------------------------------|------------|
| `get_current_user` | Get authenticated user's profile | Any        |
| `list_users`       | List all users                   | Admin      |
| `get_user`         | Get specific user details        | Admin      |
| `update_user_role` | Change user role                 | Admin      |
| `delete_user`      | Delete a user                    | Admin      |

### Group Management

| Tool                     | Description                   | Permission |
|--------------------------|-------------------------------|------------|
| `list_groups`            | List all groups               | Any        |
| `create_group`           | Create a new group            | Admin      |
| `get_group`              | Get group details             | Any        |
| `update_group`           | Update group name/description | Admin      |
| `add_user_to_group`      | Add user to group             | Admin      |
| `remove_user_from_group` | Remove user from group        | Admin      |
| `delete_group`           | Delete a group                | Admin      |

### Model Management

| Tool           | Description             | Permission |
|----------------|-------------------------|------------|
| `list_models`  | List all models         | Any        |
| `get_model`    | Get model configuration | Any        |
| `create_model` | Create custom model     | Admin      |
| `update_model` | Update model settings   | Admin      |
| `delete_model` | Delete a model          | Admin      |

### Knowledge Base Management

| Tool                    | Description                | Permission |
|-------------------------|----------------------------|------------|
| `list_knowledge_bases`  | List knowledge bases       | Any        |
| `get_knowledge_base`    | Get knowledge base details | Any        |
| `create_knowledge_base` | Create knowledge base      | Any        |
| `update_knowledge_base` | Update knowledge base      | Owner      |
| `delete_knowledge_base` | Delete knowledge base      | Owner      |

### File Management

| Tool                  | Description                | Permission |
|-----------------------|----------------------------|------------|
| `list_files`          | List all files             | Any        |
| `search_files`        | Search files by name       | Any        |
| `get_file`            | Get file metadata          | Any        |
| `get_file_content`    | Get extracted text content | Any        |
| `update_file_content` | Update file content        | Owner      |
| `delete_file`         | Delete a file              | Owner      |
| `delete_all_files`    | Delete all files           | Admin      |

### Chat Management

| Tool               | Description         | Permission |
|--------------------|---------------------|------------|
| `list_chats`       | List user's chats   | Own        |
| `get_chat`         | Get chat messages   | Own        |
| `delete_chat`      | Delete a chat       | Own        |
| `delete_all_chats` | Delete all chats    | Own        |
| `archive_chat`     | Archive a chat      | Own        |
| `share_chat`       | Share a chat        | Own        |
| `clone_chat`       | Clone a shared chat | Any        |

### Prompt Management

| Tool            | Description              | Permission |
|-----------------|--------------------------|------------|
| `list_prompts`  | List all prompts         | Any        |
| `create_prompt` | Create a prompt template | Any        |
| `get_prompt`    | Get prompt details       | Any        |
| `update_prompt` | Update a prompt          | Owner      |
| `delete_prompt` | Delete a prompt          | Owner      |

### Memory Management

| Tool                  | Description           | Permission |
|-----------------------|-----------------------|------------|
| `list_memories`       | List all memories     | Own        |
| `add_memory`          | Add a new memory      | Own        |
| `query_memories`      | Search memories       | Own        |
| `update_memory`       | Update a memory       | Own        |
| `delete_memory`       | Delete a memory       | Own        |
| `delete_all_memories` | Delete all memories   | Own        |
| `reset_memories`      | Re-embed all memories | Own        |

### Notes Management

| Tool          | Description      | Permission |
|---------------|------------------|------------|
| `list_notes`  | List all notes   | Own        |
| `create_note` | Create a note    | Own        |
| `get_note`    | Get note details | Own        |
| `update_note` | Update a note    | Own        |
| `delete_note` | Delete a note    | Own        |

### Channels (Team Chat)

| Tool                     | Description          | Permission  |
|--------------------------|----------------------|-------------|
| `list_channels`          | List all channels    | Any         |
| `create_channel`         | Create a channel     | Admin       |
| `get_channel`            | Get channel details  | Any         |
| `update_channel`         | Update channel       | Admin       |
| `delete_channel`         | Delete a channel     | Admin       |
| `get_channel_messages`   | Get channel messages | Any         |
| `post_channel_message`   | Post a message       | Any         |
| `delete_channel_message` | Delete a message     | Owner/Admin |

### System Configuration

| Tool                | Description                 | Permission |
|---------------------|-----------------------------|------------|
| `get_system_config` | Get system configuration    | Admin      |
| `export_config`     | Export full configuration   | Admin      |
| `get_banners`       | Get notification banners    | Any        |
| `get_models_config` | Get models configuration    | Admin      |
| `set_models_config` | Set models configuration    | Admin      |
| `get_tool_servers`  | Get tool server connections | Admin      |
| `set_tool_servers`  | Set tool server connections | Admin      |

## Environment Variables

| Variable        | Required | Default     | Description                       |
|-----------------|----------|-------------|-----------------------------------|
| `WEBUI_URL`     | Yes      | -           | URL to your Open WebUI instance   |
| `WEBUI_API_KEY` | No       | -           | Default API key for requests      |
| `MCP_TRANSPORT` | No       | `stdio`     | Transport mode: `stdio` or `http` |
| `MCP_HTTP_HOST` | No       | `127.0.0.1` | HTTP server host                  |
| `MCP_HTTP_PORT` | No       | `8000`      | HTTP server port                  |
| `MCP_HTTP_PATH` | No       | `/mcp`      | HTTP server path                  |

## Programmatic Usage

Connect to the MCP server from any MCP-compatible client:

```python
from fastmcp.client import Client
import httpx

class BearerAuth(httpx.Auth):
    def __init__(self, token):
        self.token = token
    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

async with Client("http://localhost:8000/mcp", auth=BearerAuth("your-api-key")) as client:
    # List all users (admin only)
    users = await client.call_tool("get_users_api_v1_users", {})
    
    # Create a group
    group = await client.call_tool("create_new_group_api_v1_groups_create_post", {
        "name": "Engineering",
        "description": "Engineering team"
    })
    
    # List models
    models = await client.call_tool("get_models_api_v1_models_list_get", {})
```

## Related Projects

- [Open WebUI](https://github.com/open-webui/open-webui) - The web UI this server manages
- [FastMCP](https://github.com/jlowin/fastmcp) - The MCP framework used
- [MCPO](https://github.com/open-webui/mcpo) - MCP to OpenAPI proxy
- [Model Context Protocol](https://modelcontextprotocol.io/) - The protocol specification

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

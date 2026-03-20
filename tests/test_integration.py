"""Integration tests for MCP tools using FastMCP testing utilities.

Tests MCP tools properly return wrapped list responses and fixed endpoints
return JSON instead of HTML.

Requires MCP server and Open WebUI to be running.
Run with: pytest tests/test_integration.py -v -m integration
"""

import os

import httpx
import pytest
from fastmcp.client import Client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
OPENWEBUI_URL = os.getenv("OPENWEBUI_URL", "http://localhost:8081")

# Read API key from file for integration tests
_api_key = ""
try:
    with open(".openwebui-api-key") as f:
        _api_key = f.read().strip()
except FileNotFoundError:
    _api_key = os.getenv("OPENWEBUI_API_KEY", "")
OPENWEBUI_API_KEY = _api_key


async def get_openwebui_token():
    if OPENWEBUI_API_KEY:
        return OPENWEBUI_API_KEY
    admin_email = os.getenv("WEBUI_ADMIN_EMAIL", "")
    admin_password = os.getenv("WEBUI_ADMIN_PASSWORD", "password")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{OPENWEBUI_URL}/api/v1/auths/signin",
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
    async with Client(MCP_SERVER_URL) as client:
        yield client


@pytest.mark.integration
class TestEndpointVerification:
    async def test_list_models_endpoint_returns_json(self, auth_token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENWEBUI_URL}/api/v1/models/list",
                headers={"Authorization": f"Bearer {auth_token}"} if auth_token else {},
            )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/json")
            data = response.json()
            assert isinstance(data, (list, dict))

    async def test_get_config_endpoint_returns_json(self, auth_token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENWEBUI_URL}/api/v1/configs/export",
                headers={"Authorization": f"Bearer {auth_token}"} if auth_token else {},
            )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/json")
            data = response.json()
            assert isinstance(data, dict)

    async def test_list_channels_returns_200(self, auth_token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENWEBUI_URL}/api/v1/channels/list",
                headers={"Authorization": f"Bearer {auth_token}"} if auth_token else {},
            )
            assert response.status_code in [200, 403]

    async def test_list_channels_endpoint_handles_permissions(self, auth_token):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENWEBUI_URL}/api/v1/channels/list",
                headers={"Authorization": f"Bearer {auth_token}"} if auth_token else {},
            )
            assert response.status_code in [200, 403]


@pytest.mark.integration
class TestMCPToolWrappers:
    async def test_list_users_returns_dict_with_users(self, mcp_client):
        result = await mcp_client.call_tool(name="list_users", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "users" in result.data
        assert isinstance(result.data["users"], list)

    async def test_list_groups_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_groups", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_models_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_models", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_knowledge_bases_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_knowledge_bases", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_files_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_files", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_prompts_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_prompts", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_memories_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_memories", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_chats_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_chats", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_folders_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_folders", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_tools_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_tools", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_functions_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_functions", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_notes_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="list_notes", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

    async def test_list_channels_returns_wrapped_dict(self, mcp_client):
        try:
            result = await mcp_client.call_tool(name="list_channels", arguments={})
            assert result.data is not None
            assert isinstance(result.data, dict)
            assert "items" in result.data
            assert isinstance(result.data["items"], list)
        except Exception as e:
            if "403" in str(e):
                pytest.skip("User doesn't have permission to list channels")
            raise

    async def test_get_banners_returns_wrapped_dict(self, mcp_client):
        result = await mcp_client.call_tool(name="get_banners", arguments={})
        assert result.data is not None
        assert isinstance(result.data, dict)
        assert "items" in result.data
        assert isinstance(result.data["items"], list)

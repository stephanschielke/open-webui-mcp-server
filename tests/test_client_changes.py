"""Tests for Open WebUI MCP client changes.

This module tests the changes introduced in the patch:
1. create_knowledge now accepts an optional `data` parameter
2. create_tool guarantees `meta` object exists in payload
3. create_function guarantees `meta` object exists in payload
4. Notes management methods (list, create, get, update, delete)
5. Channels management methods (list, create, get, update, delete, messages)
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openwebui_mcp.client import OpenWebUIClient  # noqa: E402
from openwebui_mcp.models import (
    ChannelCreateParam,
    ChannelIdParam,
    ChannelMessageIdParam,
    ChannelMessageParam,
    ChannelMessagesParam,
    ChannelUpdateParam,
    FunctionCreateParam,
    KnowledgeCreateParam,
    NoteCreateParam,
    NoteIdParam,
    NoteUpdateParam,
    ToolCreateParam,
)


class MockAsyncClient:
    """A proper async context manager mock for httpx.AsyncClient."""

    def __init__(self, response):
        self.response = response
        self.request = AsyncMock(return_value=response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


# Fixtures


@pytest.fixture
def client():
    """Create a test client with mocked environment."""
    with patch.dict("os.environ", {"WEBUI_URL": "https://test.example.com"}):
        return OpenWebUIClient(api_key="test-token")


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = MagicMock()
    response.json.return_value = {"success": True}
    response.raise_for_status = MagicMock()
    response.headers = {"content-type": "application/json"}
    return response


# Tests for create_knowledge with data parameter


@pytest.mark.asyncio
async def test_create_knowledge_without_data(client, mock_response):
    """Test create_knowledge without optional data parameter."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_knowledge(name="Test Knowledge", description="Test Description")

        # Verify the request was made
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args

        # Check URL and method (method is positional, url is keyword)
        assert call_args[0][0] == "POST"
        assert "https://test.example.com/api/v1/knowledge/create" in call_args[0][1]

        # Check payload - should NOT include data key
        json_data = call_args.kwargs["json"]
        assert json_data == {"name": "Test Knowledge", "description": "Test Description"}
        assert "data" not in json_data


@pytest.mark.asyncio
async def test_create_knowledge_with_data(client, mock_response):
    """Test create_knowledge with optional data parameter."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        test_data = {"custom_field": "custom_value", "nested": {"key": "value"}}
        await client.create_knowledge(
            name="Test Knowledge", description="Test Description", data=test_data
        )

        # Verify the request was made
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args

        # Check payload - should include data key
        json_data = call_args.kwargs["json"]
        assert json_data["name"] == "Test Knowledge"
        assert json_data["description"] == "Test Description"
        assert json_data["data"] == test_data


@pytest.mark.asyncio
async def test_create_knowledge_with_empty_data(client, mock_response):
    """Test create_knowledge with empty data dict (should be included)."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_knowledge(
            name="Test Knowledge", description="Test Description", data={}
        )

        # Check payload - should include empty data
        call_args = mock_client.request.call_args
        json_data = call_args.kwargs["json"]
        assert json_data["data"] == {}


# Tests for create_tool with guaranteed meta


@pytest.mark.asyncio
async def test_create_tool_with_meta(client, mock_response):
    """Test create_tool includes meta when provided."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        meta_data = {"description": "Test tool", "author": "test"}
        await client.create_tool(
            id="test-tool", name="Test Tool", content="print('hello')", meta=meta_data
        )

        call_args = mock_client.request.call_args
        json_data = call_args.kwargs["json"]

        # Should include meta
        assert json_data["meta"] == meta_data
        assert json_data["id"] == "test-tool"
        assert json_data["name"] == "Test Tool"


@pytest.mark.asyncio
async def test_create_tool_without_meta_guarantees_empty_dict(client, mock_response):
    """Test create_tool guarantees meta exists as empty dict when not provided."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_tool(id="test-tool", name="Test Tool", content="print('hello')")

        call_args = mock_client.request.call_args
        json_data = call_args.kwargs["json"]

        # Should guarantee meta as empty dict (not missing)
        assert json_data["meta"] == {}
        assert "meta" in json_data


@pytest.mark.asyncio
async def test_create_tool_with_none_meta_guarantees_empty_dict(client, mock_response):
    """Test create_tool with meta=None guarantees empty dict."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_tool(
            id="test-tool", name="Test Tool", content="print('hello')", meta=None
        )

        call_args = mock_client.request.call_args
        json_data = call_args.kwargs["json"]

        # Should guarantee meta as empty dict
        assert json_data["meta"] == {}


# Tests for create_function with guaranteed meta


@pytest.mark.asyncio
async def test_create_function_with_meta(client, mock_response):
    """Test create_function includes meta when provided."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        meta_data = {"description": "Test function"}
        await client.create_function(
            id="test-func",
            name="Test Function",
            type="filter",
            content="return input",
            meta=meta_data,
        )

        call_args = mock_client.request.call_args
        json_data = call_args.kwargs["json"]

        # Should include meta
        assert json_data["meta"] == meta_data
        assert json_data["type"] == "filter"


@pytest.mark.asyncio
async def test_create_function_without_meta_guarantees_empty_dict(client, mock_response):
    """Test create_function guarantees meta exists as empty dict when not provided."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_function(
            id="test-func", name="Test Function", type="pipe", content="return input"
        )

        call_args = mock_client.request.call_args
        json_data = call_args.kwargs["json"]

        # Should guarantee meta as empty dict
        assert json_data["meta"] == {}
        assert "meta" in json_data


@pytest.mark.asyncio
async def test_create_function_with_none_meta_guarantees_empty_dict(client, mock_response):
    """Test create_function with meta=None guarantees empty dict."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_function(
            id="test-func",
            name="Test Function",
            type="filter",
            content="return input",
            meta=None,
        )

        call_args = mock_client.request.call_args
        json_data = call_args.kwargs["json"]

        # Should guarantee meta as empty dict
        assert json_data["meta"] == {}


# Tests for Notes management


@pytest.mark.asyncio
async def test_list_notes(client, mock_response):
    """Test list_notes calls correct endpoint."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.list_notes()

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "https://test.example.com/api/v1/notes/" in call_args[0][1]


@pytest.mark.asyncio
async def test_create_note(client, mock_response):
    """Test create_note sends correct payload."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_note(title="Test Note", content="# Markdown Content")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "https://test.example.com/api/v1/notes/create" in call_args[0][1]
        assert call_args.kwargs["json"] == {
            "title": "Test Note",
            "content": "# Markdown Content",
        }


@pytest.mark.asyncio
async def test_get_note(client, mock_response):
    """Test get_note calls correct endpoint."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.get_note("note-123")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "https://test.example.com/api/v1/notes/note-123" in call_args[0][1]


@pytest.mark.asyncio
async def test_update_note_both_fields(client, mock_response):
    """Test update_note with both title and content."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.update_note(note_id="note-123", title="New Title", content="New Content")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "https://test.example.com/api/v1/notes/note-123/update" in call_args[0][1]
        assert call_args.kwargs["json"] == {"title": "New Title", "content": "New Content"}


@pytest.mark.asyncio
async def test_update_note_title_only(client, mock_response):
    """Test update_note with only title."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.update_note(note_id="note-123", title="New Title")

        call_args = mock_client.request.call_args
        assert call_args.kwargs["json"] == {"title": "New Title"}
        assert "content" not in call_args.kwargs["json"]


@pytest.mark.asyncio
async def test_update_note_content_only(client, mock_response):
    """Test update_note with only content."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.update_note(note_id="note-123", content="New Content")

        call_args = mock_client.request.call_args
        assert call_args.kwargs["json"] == {"content": "New Content"}
        assert "title" not in call_args.kwargs["json"]


@pytest.mark.asyncio
async def test_delete_note(client, mock_response):
    """Test delete_note calls correct endpoint."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.delete_note("note-123")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "https://test.example.com/api/v1/notes/note-123/delete" in call_args[0][1]


# Tests for Channels management


@pytest.mark.asyncio
async def test_list_channels(client, mock_response):
    """Test list_channels calls correct endpoint."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.list_channels()

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "https://test.example.com/api/v1/channels/" in call_args[0][1]


@pytest.mark.asyncio
async def test_create_channel(client, mock_response):
    """Test create_channel sends correct payload."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_channel(name="Test Channel", description="A test channel")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "https://test.example.com/api/v1/channels/create" in call_args[0][1]
        assert call_args.kwargs["json"] == {
            "name": "Test Channel",
            "description": "A test channel",
        }


@pytest.mark.asyncio
async def test_create_channel_default_description(client, mock_response):
    """Test create_channel with default empty description."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.create_channel(name="Test Channel")

        call_args = mock_client.request.call_args
        assert call_args.kwargs["json"]["description"] == ""


@pytest.mark.asyncio
async def test_get_channel(client, mock_response):
    """Test get_channel calls correct endpoint."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.get_channel("channel-456")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        assert "https://test.example.com/api/v1/channels/channel-456" in call_args[0][1]


@pytest.mark.asyncio
async def test_update_channel_both_fields(client, mock_response):
    """Test update_channel with both name and description."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.update_channel(
            channel_id="channel-456", name="New Name", description="New Description"
        )

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert "https://test.example.com/api/v1/channels/channel-456/update" in call_args[0][1]
        assert call_args.kwargs["json"] == {"name": "New Name", "description": "New Description"}


@pytest.mark.asyncio
async def test_delete_channel(client, mock_response):
    """Test delete_channel calls correct endpoint."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.delete_channel("channel-456")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "https://test.example.com/api/v1/channels/channel-456/delete" in call_args[0][1]


@pytest.mark.asyncio
async def test_get_channel_messages(client, mock_response):
    """Test get_channel_messages with pagination params."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.get_channel_messages(channel_id="channel-456", skip=10, limit=25)

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "GET"
        url = call_args[0][1]
        assert "https://test.example.com/api/v1/channels/channel-456/messages" in url
        assert "skip=10" in url
        assert "limit=25" in url


@pytest.mark.asyncio
async def test_get_channel_messages_defaults(client, mock_response):
    """Test get_channel_messages with default pagination."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.get_channel_messages(channel_id="channel-456")

        call_args = mock_client.request.call_args
        url = call_args[0][1]
        assert "skip=0" in url
        assert "limit=50" in url


@pytest.mark.asyncio
async def test_post_channel_message(client, mock_response):
    """Test post_channel_message sends correct payload."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.post_channel_message(channel_id="channel-456", content="Hello everyone!")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "POST"
        assert (
            "https://test.example.com/api/v1/channels/channel-456/messages/post" in call_args[0][1]
        )
        assert call_args.kwargs["json"] == {"content": "Hello everyone!"}


@pytest.mark.asyncio
async def test_post_channel_message_with_parent(client, mock_response):
    """Test post_channel_message with parent_id for threading."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.post_channel_message(
            channel_id="channel-456", content="Reply", parent_id="msg-789"
        )

        call_args = mock_client.request.call_args
        assert call_args.kwargs["json"] == {"content": "Reply", "parent_id": "msg-789"}


@pytest.mark.asyncio
async def test_delete_channel_message(client, mock_response):
    """Test delete_channel_message calls correct endpoint."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = MockAsyncClient(mock_response)
        mock_client_class.return_value = mock_client

        await client.delete_channel_message(channel_id="channel-456", message_id="msg-789")

        call_args = mock_client.request.call_args
        assert call_args[0][0] == "DELETE"
        assert (
            "https://test.example.com/api/v1/channels/channel-456/messages/msg-789/delete"
            in call_args[0][1]
        )


# Tests for Pydantic models


def test_knowledge_create_param_with_data():
    """Test KnowledgeCreateParam accepts data field."""
    param = KnowledgeCreateParam(
        name="Test Knowledge",
        description="Test Description",
        data={"custom": "value"},
    )
    assert param.name == "Test Knowledge"
    assert param.description == "Test Description"
    assert param.data == {"custom": "value"}


def test_knowledge_create_param_without_data():
    """Test KnowledgeCreateParam without data field."""
    param = KnowledgeCreateParam(name="Test Knowledge")
    assert param.name == "Test Knowledge"
    assert param.description == ""
    assert param.data is None


def test_tool_create_param_with_meta():
    """Test ToolCreateParam accepts meta field."""
    param = ToolCreateParam(id="test-tool", name="Test Tool", content="code", meta={"key": "value"})
    assert param.meta == {"key": "value"}


def test_tool_create_param_default_meta():
    """Test ToolCreateParam default meta is None."""
    param = ToolCreateParam(id="test-tool", name="Test Tool", content="code")
    assert param.meta is None


def test_function_create_param_with_meta():
    """Test FunctionCreateParam accepts meta field."""
    param = FunctionCreateParam(
        id="test-func",
        name="Test Function",
        type="filter",
        content="code",
        meta={"key": "value"},
    )
    assert param.meta == {"key": "value"}


def test_function_create_param_default_meta():
    """Test FunctionCreateParam default meta is None."""
    param = FunctionCreateParam(id="test-func", name="Test Function", type="filter", content="code")
    assert param.meta is None


def test_note_create_param():
    """Test NoteCreateParam model."""
    param = NoteCreateParam(title="My Note", content="# Content")
    assert param.title == "My Note"
    assert param.content == "# Content"


def test_note_id_param():
    """Test NoteIdParam model."""
    param = NoteIdParam(note_id="note-123")
    assert param.note_id == "note-123"


def test_note_update_param():
    """Test NoteUpdateParam model."""
    param = NoteUpdateParam(note_id="note-123", title="New Title")
    assert param.note_id == "note-123"
    assert param.title == "New Title"
    assert param.content is None


def test_note_update_param_both_fields():
    """Test NoteUpdateParam with both fields."""
    param = NoteUpdateParam(note_id="note-123", title="New Title", content="New Content")
    assert param.title == "New Title"
    assert param.content == "New Content"


def test_channel_create_param():
    """Test ChannelCreateParam model."""
    param = ChannelCreateParam(name="My Channel", description="Channel desc")
    assert param.name == "My Channel"
    assert param.description == "Channel desc"


def test_channel_create_param_default_description():
    """Test ChannelCreateParam default description."""
    param = ChannelCreateParam(name="My Channel")
    assert param.name == "My Channel"
    assert param.description == ""


def test_channel_id_param():
    """Test ChannelIdParam model."""
    param = ChannelIdParam(channel_id="channel-456")
    assert param.channel_id == "channel-456"


def test_channel_update_param():
    """Test ChannelUpdateParam model."""
    param = ChannelUpdateParam(channel_id="channel-456", name="New Name")
    assert param.channel_id == "channel-456"
    assert param.name == "New Name"
    assert param.description is None


def test_channel_message_param():
    """Test ChannelMessageParam model."""
    param = ChannelMessageParam(channel_id="channel-456", content="Hello")
    assert param.channel_id == "channel-456"
    assert param.content == "Hello"
    assert param.parent_id is None


def test_channel_message_param_with_parent():
    """Test ChannelMessageParam with parent_id."""
    param = ChannelMessageParam(channel_id="channel-456", content="Reply", parent_id="msg-789")
    assert param.parent_id == "msg-789"


def test_channel_messages_param():
    """Test ChannelMessagesParam model."""
    param = ChannelMessagesParam(channel_id="channel-456")
    assert param.channel_id == "channel-456"
    assert param.skip == 0
    assert param.limit == 50


def test_channel_messages_param_custom_pagination():
    """Test ChannelMessagesParam with custom pagination."""
    param = ChannelMessagesParam(channel_id="channel-456", skip=10, limit=100)
    assert param.skip == 10
    assert param.limit == 100


def test_channel_message_id_param():
    """Test ChannelMessageIdParam model."""
    param = ChannelMessageIdParam(channel_id="channel-456", message_id="msg-789")
    assert param.channel_id == "channel-456"
    assert param.message_id == "msg-789"

from typing import Any

from fastmcp import FastMCP

from openwebui_mcp.auth import get_user_token
from openwebui_mcp.client import get_client
from openwebui_mcp.models import (
    ChannelCreateParam,
    ChannelIdParam,
    ChannelMessageIdParam,
    ChannelMessageParam,
    ChannelMessagesParam,
    ChannelUpdateParam,
    ChatIdParam,
    FileContentParam,
    FileIdParam,
    FileSearchParam,
    FolderCreateParam,
    FolderIdParam,
    FolderUpdateParam,
    FunctionCreateParam,
    FunctionIdParam,
    FunctionUpdateParam,
    GroupCreateParam,
    GroupIdParam,
    GroupUpdateParam,
    GroupUserParam,
    KnowledgeCreateParam,
    KnowledgeIdParam,
    KnowledgeUpdateParam,
    MemoryAddParam,
    MemoryIdParam,
    MemoryQueryParam,
    MemoryUpdateParam,
    ModelCreateParam,
    ModelIdParam,
    ModelUpdateParam,
    NoteCreateParam,
    NoteIdParam,
    NoteUpdateParam,
    PromptCreateParam,
    PromptIdParam,
    PromptUpdateParam,
    ToolCreateParam,
    ToolIdParam,
    ToolUpdateParam,
    UserIdParam,
    UserRoleParam,
)

# Initialize MCP server
mcp = FastMCP("openwebui-mcp-server")


# =============================================================================
# User Management Tools
# =============================================================================


@mcp.tool()
async def get_current_user() -> dict[str, Any]:
    """Get the currently authenticated user's profile.
    Returns your ID, name, email, role, and permissions."""
    return await get_client().get_current_user(get_user_token())


@mcp.tool()
async def list_users() -> dict[str, Any]:
    """List all users in Open WebUI. ADMIN ONLY."""
    result = await get_client().list_users(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_user(params: UserIdParam) -> dict[str, Any]:
    """Get details for a specific user. ADMIN ONLY."""
    return await get_client().get_user(params.user_id, get_user_token())


@mcp.tool()
async def update_user_role(params: UserRoleParam) -> dict[str, Any]:
    """Update a user's role. ADMIN ONLY. Roles: 'admin', 'user', 'pending'."""
    return await get_client().update_user_role(params.user_id, params.role, get_user_token())


@mcp.tool()
async def delete_user(params: UserIdParam) -> dict[str, Any]:
    """Delete a user. ADMIN ONLY. WARNING: Cannot be undone!"""
    return await get_client().delete_user(params.user_id, get_user_token())


# =============================================================================
# Group Management Tools
# =============================================================================


@mcp.tool()
async def list_groups() -> dict[str, Any]:
    """List all groups with their IDs, names, and member counts."""
    result = await get_client().list_groups(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def create_group(params: GroupCreateParam) -> dict[str, Any]:
    """Create a new group. ADMIN ONLY."""
    return await get_client().create_group(params.name, params.description, get_user_token())


@mcp.tool()
async def get_group(params: GroupIdParam) -> dict[str, Any]:
    """Get details for a specific group including members."""
    return await get_client().get_group(params.group_id, get_user_token())


@mcp.tool()
async def update_group(params: GroupUpdateParam) -> dict[str, Any]:
    """Update a group's name or description. ADMIN ONLY."""
    return await get_client().update_group(
        params.group_id, params.name, params.description, get_user_token()
    )


@mcp.tool()
async def add_user_to_group(params: GroupUserParam) -> dict[str, Any]:
    """Add a user to a group. ADMIN ONLY."""
    return await get_client().add_user_to_group(params.group_id, params.user_id, get_user_token())


@mcp.tool()
async def remove_user_from_group(params: GroupUserParam) -> dict[str, Any]:
    """Remove a user from a group. ADMIN ONLY."""
    return await get_client().remove_user_from_group(
        params.group_id, params.user_id, get_user_token()
    )


@mcp.tool()
async def delete_group(params: GroupIdParam) -> dict[str, Any]:
    """Delete a group. ADMIN ONLY. Removes all users from the group."""
    return await get_client().delete_group(params.group_id, get_user_token())


# =============================================================================
# Model Management Tools
# =============================================================================


@mcp.tool()
async def list_models() -> dict[str, Any]:
    """List all available models including custom models."""
    result = await get_client().list_models(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_model(params: ModelIdParam) -> dict[str, Any]:
    """Get details for a specific model including system prompt and parameters."""
    return await get_client().get_model(params.model_id, get_user_token())


@mcp.tool()
async def create_model(params: ModelCreateParam) -> dict[str, Any]:
    """Create a new custom model wrapper. ADMIN ONLY."""
    meta = {}
    if params.system_prompt:
        meta["system"] = params.system_prompt
    model_params = {}
    if params.temperature is not None:
        model_params["temperature"] = params.temperature
    if params.max_tokens is not None:
        model_params["max_tokens"] = params.max_tokens
    return await get_client().create_model(
        id=params.id,
        name=params.name,
        base_model_id=params.base_model_id,
        meta=meta if meta else None,
        params=model_params if model_params else None,
        api_key=get_user_token(),
    )


@mcp.tool()
async def update_model(params: ModelUpdateParam) -> dict[str, Any]:
    """Update a model's name, metadata, or parameters."""
    return await get_client().update_model(
        params.model_id, params.name, params.meta, params.params, get_user_token()
    )


@mcp.tool()
async def delete_model(params: ModelIdParam) -> dict[str, Any]:
    """Delete a custom model. ADMIN ONLY."""
    return await get_client().delete_model(params.model_id, get_user_token())


# =============================================================================
# Knowledge Base Management Tools
# =============================================================================


@mcp.tool()
async def list_knowledge_bases() -> dict[str, Any]:
    """List all knowledge bases with their IDs, names, and descriptions."""
    result = await get_client().list_knowledge(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_knowledge_base(params: KnowledgeIdParam) -> dict[str, Any]:
    """Get details for a knowledge base including file list."""
    return await get_client().get_knowledge(params.knowledge_id, get_user_token())


@mcp.tool()
async def create_knowledge_base(params: KnowledgeCreateParam) -> dict[str, Any]:
    """Create a new knowledge base for RAG."""
    return await get_client().create_knowledge(
        params.name, params.description, params.data, get_user_token()
    )


@mcp.tool()
async def update_knowledge_base(params: KnowledgeUpdateParam) -> dict[str, Any]:
    """Update a knowledge base's name or description."""
    return await get_client().update_knowledge(
        params.knowledge_id, params.name, params.description, get_user_token()
    )


@mcp.tool()
async def delete_knowledge_base(params: KnowledgeIdParam) -> dict[str, Any]:
    """Delete a knowledge base and all its files. WARNING: Cannot be undone!"""
    return await get_client().delete_knowledge(params.knowledge_id, get_user_token())


# =============================================================================
# File Management Tools
# =============================================================================


@mcp.tool()
async def list_files() -> dict[str, Any]:
    """List all uploaded files with metadata."""
    result = await get_client().list_files(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def search_files(params: FileSearchParam) -> dict[str, Any]:
    """Search files by filename pattern. Supports wildcards like *.pdf"""
    return await get_client().search_files(params.filename, get_user_token())


@mcp.tool()
async def get_file(params: FileIdParam) -> dict[str, Any]:
    """Get metadata for a specific file."""
    return await get_client().get_file(params.file_id, get_user_token())


@mcp.tool()
async def get_file_content(params: FileIdParam) -> dict[str, Any]:
    """Get the extracted text content from a file."""
    return await get_client().get_file_content(params.file_id, get_user_token())


@mcp.tool()
async def update_file_content(params: FileContentParam) -> dict[str, Any]:
    """Update the extracted text content of a file."""
    return await get_client().update_file_content(params.file_id, params.content, get_user_token())


@mcp.tool()
async def delete_file(params: FileIdParam) -> dict[str, Any]:
    """Delete a file."""
    return await get_client().delete_file(params.file_id, get_user_token())


@mcp.tool()
async def delete_all_files() -> dict[str, Any]:
    """Delete all files. ADMIN ONLY. WARNING: Cannot be undone!"""
    return await get_client().delete_all_files(get_user_token())


# =============================================================================
# Prompt Management Tools
# =============================================================================


@mcp.tool()
async def list_prompts() -> dict[str, Any]:
    """List all prompt templates."""
    result = await get_client().list_prompts(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def create_prompt(params: PromptCreateParam) -> dict[str, Any]:
    """Create a new prompt template triggered by a command."""
    return await get_client().create_prompt(
        params.command, params.title, params.content, get_user_token()
    )


@mcp.tool()
async def get_prompt(params: PromptIdParam) -> dict[str, Any]:
    """Get a prompt template by its command."""
    return await get_client().get_prompt(params.command, get_user_token())


@mcp.tool()
async def update_prompt(params: PromptUpdateParam) -> dict[str, Any]:
    """Update a prompt template."""
    return await get_client().update_prompt(
        params.command, params.title, params.content, get_user_token()
    )


@mcp.tool()
async def delete_prompt(params: PromptIdParam) -> dict[str, Any]:
    """Delete a prompt template."""
    return await get_client().delete_prompt(params.command, get_user_token())


# =============================================================================
# Memory Management Tools
# =============================================================================


@mcp.tool()
async def list_memories() -> dict[str, Any]:
    """List all your stored memories."""
    result = await get_client().list_memories(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def add_memory(params: MemoryAddParam) -> dict[str, Any]:
    """Add a new memory to your memory store."""
    return await get_client().add_memory(params.content, get_user_token())


@mcp.tool()
async def query_memories(params: MemoryQueryParam) -> dict[str, Any]:
    """Search memories using semantic similarity."""
    return await get_client().query_memories(params.content, params.k, get_user_token())


@mcp.tool()
async def update_memory(params: MemoryUpdateParam) -> dict[str, Any]:
    """Update an existing memory."""
    return await get_client().update_memory(params.memory_id, params.content, get_user_token())


@mcp.tool()
async def delete_memory(params: MemoryIdParam) -> dict[str, Any]:
    """Delete a specific memory."""
    return await get_client().delete_memory(params.memory_id, get_user_token())


@mcp.tool()
async def delete_all_memories() -> dict[str, Any]:
    """Delete all your memories. WARNING: Cannot be undone!"""
    return await get_client().delete_all_memories(get_user_token())


@mcp.tool()
async def reset_memories() -> dict[str, Any]:
    """Re-embed all memories in the vector database."""
    return await get_client().reset_memories(get_user_token())


# =============================================================================
# Chat Management Tools
# =============================================================================


@mcp.tool()
async def list_chats() -> dict[str, Any]:
    """List your chats."""
    result = await get_client().list_chats(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_chat(params: ChatIdParam) -> dict[str, Any]:
    """Get a chat's details and message history."""
    return await get_client().get_chat(params.chat_id, get_user_token())


@mcp.tool()
async def delete_chat(params: ChatIdParam) -> dict[str, Any]:
    """Delete a chat."""
    return await get_client().delete_chat(params.chat_id, get_user_token())


@mcp.tool()
async def delete_all_chats() -> dict[str, Any]:
    """Delete all your chats. WARNING: Cannot be undone!"""
    return await get_client().delete_all_chats(get_user_token())


@mcp.tool()
async def archive_chat(params: ChatIdParam) -> dict[str, Any]:
    """Archive a chat."""
    return await get_client().archive_chat(params.chat_id, get_user_token())


@mcp.tool()
async def share_chat(params: ChatIdParam) -> dict[str, Any]:
    """Share a chat (make it publicly accessible)."""
    return await get_client().share_chat(params.chat_id, get_user_token())


@mcp.tool()
async def clone_chat(params: ChatIdParam) -> dict[str, Any]:
    """Clone a shared chat to your account."""
    return await get_client().clone_chat(params.chat_id, get_user_token())


# =============================================================================
# Folder Management Tools
# =============================================================================


@mcp.tool()
async def list_folders() -> dict[str, Any]:
    """List all folders for organizing chats."""
    result = await get_client().list_folders(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def create_folder(params: FolderCreateParam) -> dict[str, Any]:
    """Create a new folder."""
    return await get_client().create_folder(params.name, get_user_token())


@mcp.tool()
async def get_folder(params: FolderIdParam) -> dict[str, Any]:
    """Get folder details."""
    return await get_client().get_folder(params.folder_id, get_user_token())


@mcp.tool()
async def update_folder(params: FolderUpdateParam) -> dict[str, Any]:
    """Rename a folder."""
    return await get_client().update_folder(params.folder_id, params.name, get_user_token())


@mcp.tool()
async def delete_folder(params: FolderIdParam) -> dict[str, Any]:
    """Delete a folder."""
    return await get_client().delete_folder(params.folder_id, get_user_token())


# =============================================================================
# Tool Management Tools
# =============================================================================


@mcp.tool()
async def list_tools() -> dict[str, Any]:
    """List all available tools (MCP, OpenAPI, custom)."""
    result = await get_client().list_tools(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_tool(params: ToolIdParam) -> dict[str, Any]:
    """Get details for a specific tool."""
    return await get_client().get_tool(params.tool_id, get_user_token())


@mcp.tool()
async def create_tool(params: ToolCreateParam) -> dict[str, Any]:
    """Create a new custom tool with Python code."""
    return await get_client().create_tool(
        params.id, params.name, params.content, params.meta, api_key=get_user_token()
    )


@mcp.tool()
async def update_tool(params: ToolUpdateParam) -> dict[str, Any]:
    """Update a tool's name, code, or metadata."""
    return await get_client().update_tool(
        params.tool_id, params.name, params.content, params.meta, api_key=get_user_token()
    )


@mcp.tool()
async def delete_tool(params: ToolIdParam) -> dict[str, Any]:
    """Delete a tool."""
    return await get_client().delete_tool(params.tool_id, get_user_token())


# =============================================================================
# Function Management Tools
# =============================================================================


@mcp.tool()
async def list_functions() -> dict[str, Any]:
    """List all functions (filters and pipes)."""
    result = await get_client().list_functions(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_function(params: FunctionIdParam) -> dict[str, Any]:
    """Get details for a specific function."""
    return await get_client().get_function(params.function_id, get_user_token())


@mcp.tool()
async def create_function(params: FunctionCreateParam) -> dict[str, Any]:
    """Create a new function (filter or pipe) with Python code."""
    return await get_client().create_function(
        params.id, params.name, params.type, params.content, api_key=get_user_token()
    )


@mcp.tool()
async def update_function(params: FunctionUpdateParam) -> dict[str, Any]:
    """Update a function's name or code."""
    return await get_client().update_function(
        params.function_id, params.name, params.content, api_key=get_user_token()
    )


@mcp.tool()
async def toggle_function(params: FunctionIdParam) -> dict[str, Any]:
    """Toggle a function's enabled/disabled state."""
    return await get_client().toggle_function(params.function_id, get_user_token())


@mcp.tool()
async def delete_function(params: FunctionIdParam) -> dict[str, Any]:
    """Delete a function."""
    return await get_client().delete_function(params.function_id, get_user_token())


# =============================================================================
# Notes Management Tools
# =============================================================================


@mcp.tool()
async def list_notes() -> dict[str, Any]:
    """List all your notes."""
    result = await get_client().list_notes(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def create_note(params: NoteCreateParam) -> dict[str, Any]:
    """Create a new note with markdown content."""
    return await get_client().create_note(params.title, params.content, get_user_token())


@mcp.tool()
async def get_note(params: NoteIdParam) -> dict[str, Any]:
    """Get a specific note by ID."""
    return await get_client().get_note(params.note_id, get_user_token())


@mcp.tool()
async def update_note(params: NoteUpdateParam) -> dict[str, Any]:
    """Update a note's title or content."""
    return await get_client().update_note(
        params.note_id, params.title, params.content, get_user_token()
    )


@mcp.tool()
async def delete_note(params: NoteIdParam) -> dict[str, Any]:
    """Delete a note."""
    return await get_client().delete_note(params.note_id, get_user_token())


# =============================================================================
# Channels (Team Chat) Management Tools
# =============================================================================


@mcp.tool()
async def list_channels() -> dict[str, Any]:
    """List all team chat channels."""
    result = await get_client().list_channels(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def create_channel(params: ChannelCreateParam) -> dict[str, Any]:
    """Create a new team chat channel."""
    return await get_client().create_channel(params.name, params.description, get_user_token())


@mcp.tool()
async def get_channel(params: ChannelIdParam) -> dict[str, Any]:
    """Get details for a specific channel."""
    return await get_client().get_channel(params.channel_id, get_user_token())


@mcp.tool()
async def update_channel(params: ChannelUpdateParam) -> dict[str, Any]:
    """Update a channel's name or description."""
    return await get_client().update_channel(
        params.channel_id, params.name, params.description, get_user_token()
    )


@mcp.tool()
async def delete_channel(params: ChannelIdParam) -> dict[str, Any]:
    """Delete a channel and all its messages."""
    return await get_client().delete_channel(params.channel_id, get_user_token())


@mcp.tool()
async def get_channel_messages(params: ChannelMessagesParam) -> dict[str, Any]:
    """Get messages from a channel with pagination."""
    return await get_client().get_channel_messages(
        params.channel_id, params.skip, params.limit, get_user_token()
    )


@mcp.tool()
async def post_channel_message(params: ChannelMessageParam) -> dict[str, Any]:
    """Post a message to a channel. Optionally reply to a parent message."""
    return await get_client().post_channel_message(
        params.channel_id, params.content, params.parent_id, get_user_token()
    )


@mcp.tool()
async def delete_channel_message(params: ChannelMessageIdParam) -> dict[str, Any]:
    """Delete a message from a channel."""
    return await get_client().delete_channel_message(
        params.channel_id, params.message_id, get_user_token()
    )


# =============================================================================
# Config/Settings Tools (Admin)
# =============================================================================


@mcp.tool()
async def get_system_config() -> dict[str, Any]:
    """Get system configuration. ADMIN ONLY."""
    return await get_client().get_config(get_user_token())


@mcp.tool()
async def export_config() -> dict[str, Any]:
    """Export full system configuration. ADMIN ONLY."""
    return await get_client().export_config(get_user_token())


@mcp.tool()
async def get_banners() -> dict[str, Any]:
    """Get system notification banners."""
    result = await get_client().get_banners(get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_models_config() -> dict[str, Any]:
    """Get default models configuration. ADMIN ONLY."""
    return await get_client().get_models_config(get_user_token())


@mcp.tool()
async def get_tool_servers() -> dict[str, Any]:
    """Get tool server (MCP/OpenAPI) connections. ADMIN ONLY."""
    return await get_client().get_tool_servers(get_user_token())

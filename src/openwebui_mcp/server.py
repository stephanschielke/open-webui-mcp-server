from typing import Any

from fastmcp import FastMCP

from openwebui_mcp.auth import get_user_token
from openwebui_mcp.client import get_client

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
async def get_user(user_id: str) -> dict[str, Any]:
    """Get details for a specific user. ADMIN ONLY."""
    return await get_client().get_user(user_id, get_user_token())


@mcp.tool()
async def update_user_role(user_id: str, role: str) -> dict[str, Any]:
    """Update a user's role. ADMIN ONLY. Roles: 'admin', 'user', 'pending'."""
    return await get_client().update_user_role(user_id, role, get_user_token())


@mcp.tool()
async def delete_user(user_id: str) -> dict[str, Any]:
    """Delete a user. ADMIN ONLY. WARNING: Cannot be undone!"""
    return await get_client().delete_user(user_id, get_user_token())


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
async def create_group(name: str, description: str = "") -> dict[str, Any]:
    """Create a new group. ADMIN ONLY."""
    return await get_client().create_group(name, description, get_user_token())


@mcp.tool()
async def get_group(group_id: str) -> dict[str, Any]:
    """Get details for a specific group including members."""
    return await get_client().get_group(group_id, get_user_token())


@mcp.tool()
async def update_group(
    group_id: str,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update a group's name or description. ADMIN ONLY."""
    return await get_client().update_group(group_id, name, description, get_user_token())


@mcp.tool()
async def add_user_to_group(group_id: str, user_id: str) -> dict[str, Any]:
    """Add a user to a group. ADMIN ONLY."""
    return await get_client().add_user_to_group(group_id, user_id, get_user_token())


@mcp.tool()
async def remove_user_from_group(group_id: str, user_id: str) -> dict[str, Any]:
    """Remove a user from a group. ADMIN ONLY."""
    return await get_client().remove_user_from_group(group_id, user_id, get_user_token())


@mcp.tool()
async def delete_group(group_id: str) -> dict[str, Any]:
    """Delete a group. ADMIN ONLY. Removes all users from the group."""
    result = await get_client().delete_group(group_id, get_user_token())
    if isinstance(result, bool):
        return {"success": result}
    return result


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
async def get_model(model_id: str) -> dict[str, Any]:
    """Get details for a specific model including system prompt and parameters."""
    return await get_client().get_model(model_id, get_user_token())


@mcp.tool()
async def create_model(
    id: str,
    name: str,
    base_model_id: str,
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Create a new custom model wrapper. ADMIN ONLY."""
    meta = {}
    if system_prompt:
        meta["system"] = system_prompt
    model_params = {}
    if temperature is not None:
        model_params["temperature"] = temperature
    if max_tokens is not None:
        model_params["max_tokens"] = max_tokens
    return await get_client().create_model(
        id=id,
        name=name,
        base_model_id=base_model_id,
        meta=meta if meta else None,
        params=model_params if model_params else None,
        api_key=get_user_token(),
    )


@mcp.tool()
async def update_model(
    model_id: str,
    name: str | None = None,
    meta: dict | None = None,
    params: dict | None = None,
) -> dict[str, Any]:
    """Update a model's name, metadata, or parameters."""
    return await get_client().update_model(model_id, name, meta, params, get_user_token())


@mcp.tool()
async def delete_model(model_id: str) -> dict[str, Any]:
    """Delete a custom model. ADMIN ONLY."""
    return await get_client().delete_model(model_id, get_user_token())


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
async def get_knowledge_base(knowledge_id: str) -> dict[str, Any]:
    """Get details for a knowledge base including file list."""
    return await get_client().get_knowledge(knowledge_id, get_user_token())


@mcp.tool()
async def create_knowledge_base(
    name: str,
    description: str = "",
    data: dict | None = None,
) -> dict[str, Any]:
    """Create a new knowledge base for RAG."""
    return await get_client().create_knowledge(name, description, data, get_user_token())


@mcp.tool()
async def update_knowledge_base(
    knowledge_id: str,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update a knowledge base's name or description."""
    return await get_client().update_knowledge(knowledge_id, name, description, get_user_token())


@mcp.tool()
async def delete_knowledge_base(knowledge_id: str) -> dict[str, Any]:
    """Delete a knowledge base and all its files. WARNING: Cannot be undone!"""
    result = await get_client().delete_knowledge(knowledge_id, get_user_token())
    if isinstance(result, bool):
        return {"success": result}
    return result


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
async def search_files(filename: str) -> dict[str, Any]:
    """Search files by filename pattern. Supports wildcards like *.pdf"""
    result = await get_client().search_files(filename, get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def get_file(file_id: str) -> dict[str, Any]:
    """Get metadata for a specific file."""
    return await get_client().get_file(file_id, get_user_token())


@mcp.tool()
async def get_file_content(file_id: str) -> dict[str, Any]:
    """Get the extracted text content from a file."""
    return await get_client().get_file_content(file_id, get_user_token())


@mcp.tool()
async def update_file_content(file_id: str, content: str) -> dict[str, Any]:
    """Update the extracted text content of a file."""
    return await get_client().update_file_content(file_id, content, get_user_token())


@mcp.tool()
async def delete_file(file_id: str) -> dict[str, Any]:
    """Delete a file."""
    return await get_client().delete_file(file_id, get_user_token())


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
async def create_prompt(command: str, name: str, content: str) -> dict[str, Any]:
    """Create a new prompt template triggered by a command."""
    cmd = f"/{command.lstrip('/')}"
    return await get_client().create_prompt(cmd, name, content, get_user_token())


@mcp.tool()
async def get_prompt(command: str) -> dict[str, Any]:
    """Get a prompt template by its command."""
    prompts = await get_client().list_prompts(get_user_token())
    prompt_list = prompts if isinstance(prompts, list) else prompts.get("items", [])
    cmd = command.strip().lstrip("/")
    for prompt in prompt_list:
        prompt_cmd = str(prompt.get("command", "")).strip().lstrip("/")
        if prompt_cmd.lower() == cmd.lower():
            return prompt
    raise ValueError(f"Prompt with command '/{cmd}' not found")


@mcp.tool()
async def update_prompt(
    prompt_id: str,
    name: str | None = None,
    content: str | None = None,
    command: str | None = None,
) -> dict[str, Any]:
    """Update a prompt template."""
    return await get_client().update_prompt(prompt_id, name, content, command, get_user_token())


@mcp.tool()
async def delete_prompt(prompt_id: str) -> dict[str, Any]:
    """Delete a prompt template by ID or command."""
    # Check if prompt_id looks like a UUID (contains dashes and is long)
    # If not, treat it as a command and look up the internal ID
    if len(prompt_id) < 30 or "-" not in prompt_id:
        # Treat as command - search for the prompt
        prompts = await get_client().list_prompts(get_user_token())
        prompt_list = prompts if isinstance(prompts, list) else prompts.get("items", [])
        cmd = prompt_id.strip().lstrip("/")
        for prompt in prompt_list:
            prompt_cmd = str(prompt.get("command", "")).strip().lstrip("/")
            if prompt_cmd.lower() == cmd.lower():
                prompt_id = prompt.get("id")
                break
        else:
            raise ValueError(f"Prompt with command '/{cmd}' not found")

    result = await get_client().delete_prompt(prompt_id, get_user_token())
    if isinstance(result, bool):
        return {"success": result}
    return result


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
async def add_memory(content: str) -> dict[str, Any]:
    """Add a new memory to your memory store."""
    return await get_client().add_memory(content, get_user_token())


@mcp.tool()
async def query_memories(content: str, k: int = 5) -> dict[str, Any]:
    """Search memories using semantic similarity."""
    return await get_client().query_memories(content, k, get_user_token())


@mcp.tool()
async def update_memory(memory_id: str, content: str) -> dict[str, Any]:
    """Update an existing memory."""
    return await get_client().update_memory(memory_id, content, get_user_token())


@mcp.tool()
async def delete_memory(memory_id: str) -> dict[str, Any]:
    """Delete a specific memory."""
    result = await get_client().delete_memory(memory_id, get_user_token())
    if isinstance(result, bool):
        return {"success": result}
    return result


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
async def get_chat(chat_id: str) -> dict[str, Any]:
    """Get a chat's details and message history."""
    return await get_client().get_chat(chat_id, get_user_token())


@mcp.tool()
async def delete_chat(chat_id: str) -> dict[str, Any]:
    """Delete a chat."""
    return await get_client().delete_chat(chat_id, get_user_token())


@mcp.tool()
async def delete_all_chats() -> dict[str, Any]:
    """Delete all your chats. WARNING: Cannot be undone!"""
    return await get_client().delete_all_chats(get_user_token())


@mcp.tool()
async def archive_chat(chat_id: str) -> dict[str, Any]:
    """Archive a chat."""
    return await get_client().archive_chat(chat_id, get_user_token())


@mcp.tool()
async def share_chat(chat_id: str) -> dict[str, Any]:
    """Share a chat (make it publicly accessible)."""
    return await get_client().share_chat(chat_id, get_user_token())


@mcp.tool()
async def clone_chat(chat_id: str) -> dict[str, Any]:
    """Clone a shared chat to your account."""
    return await get_client().clone_chat(chat_id, get_user_token())


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
async def create_folder(name: str) -> dict[str, Any]:
    """Create a new folder."""
    return await get_client().create_folder(name, get_user_token())


@mcp.tool()
async def get_folder(folder_id: str) -> dict[str, Any]:
    """Get folder details."""
    return await get_client().get_folder(folder_id, get_user_token())


@mcp.tool()
async def update_folder(folder_id: str, name: str) -> dict[str, Any]:
    """Rename a folder."""
    return await get_client().update_folder(folder_id, name, get_user_token())


@mcp.tool()
async def delete_folder(folder_id: str) -> dict[str, Any]:
    """Delete a folder."""
    return await get_client().delete_folder(folder_id, get_user_token())


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
async def get_tool(tool_id: str) -> dict[str, Any]:
    """Get details for a specific tool."""
    return await get_client().get_tool(tool_id, get_user_token())


@mcp.tool()
async def create_tool(
    id: str,
    name: str,
    content: str,
    meta: dict | None = None,
) -> dict[str, Any]:
    """Create a new custom tool with Python code."""
    return await get_client().create_tool(id, name, content, meta, api_key=get_user_token())


@mcp.tool()
async def update_tool(
    tool_id: str,
    name: str | None = None,
    content: str | None = None,
    meta: dict | None = None,
) -> dict[str, Any]:
    """Update a tool's name, code, or metadata."""
    return await get_client().update_tool(tool_id, name, content, meta, api_key=get_user_token())


@mcp.tool()
async def delete_tool(tool_id: str) -> dict[str, Any]:
    """Delete a tool."""
    return await get_client().delete_tool(tool_id, get_user_token())


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
async def get_function(function_id: str) -> dict[str, Any]:
    """Get details for a specific function."""
    return await get_client().get_function(function_id, get_user_token())


@mcp.tool()
async def create_function(
    id: str,
    name: str,
    type: str,
    content: str,
    meta: dict | None = None,
) -> dict[str, Any]:
    """Create a new function (filter or pipe) with Python code."""
    return await get_client().create_function(
        id, name, type, content, meta, api_key=get_user_token()
    )


@mcp.tool()
async def update_function(
    function_id: str,
    name: str | None = None,
    content: str | None = None,
    meta: dict | None = None,
) -> dict[str, Any]:
    """Update a function's name or code."""
    return await get_client().update_function(
        function_id, name, content, meta, api_key=get_user_token()
    )


@mcp.tool()
async def toggle_function(function_id: str) -> dict[str, Any]:
    """Toggle a function's enabled/disabled state."""
    return await get_client().toggle_function(function_id, get_user_token())


@mcp.tool()
async def delete_function(function_id: str) -> dict[str, Any]:
    """Delete a function."""
    return await get_client().delete_function(function_id, get_user_token())


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
async def create_note(title: str, content: str) -> dict[str, Any]:
    """Create a new note with markdown content."""
    return await get_client().create_note(title, content, get_user_token())


@mcp.tool()
async def get_note(note_id: str) -> dict[str, Any]:
    """Get a specific note by ID."""
    return await get_client().get_note(note_id, get_user_token())


@mcp.tool()
async def update_note(
    note_id: str,
    title: str | None = None,
    content: str | None = None,
) -> dict[str, Any]:
    """Update a note's title or content."""
    return await get_client().update_note(note_id, title, content, get_user_token())


@mcp.tool()
async def delete_note(note_id: str) -> dict[str, Any]:
    """Delete a note."""
    result = await get_client().delete_note(note_id, get_user_token())
    if isinstance(result, bool):
        return {"success": result}
    return result


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
async def create_channel(name: str, description: str = "") -> dict[str, Any]:
    """Create a new team chat channel."""
    return await get_client().create_channel(name, description, get_user_token())


@mcp.tool()
async def get_channel(channel_id: str) -> dict[str, Any]:
    """Get details for a specific channel."""
    return await get_client().get_channel(channel_id, get_user_token())


@mcp.tool()
async def update_channel(
    channel_id: str,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update a channel's name or description."""
    return await get_client().update_channel(channel_id, name, description, get_user_token())


@mcp.tool()
async def delete_channel(channel_id: str) -> dict[str, Any]:
    """Delete a channel and all its messages."""
    result = await get_client().delete_channel(channel_id, get_user_token())
    if isinstance(result, bool):
        return {"success": result}
    return result


@mcp.tool()
async def get_channel_messages(
    channel_id: str,
    skip: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """Get messages from a channel with pagination."""
    result = await get_client().get_channel_messages(channel_id, skip, limit, get_user_token())
    if isinstance(result, list):
        return {"items": result}
    return result


@mcp.tool()
async def post_channel_message(
    channel_id: str,
    content: str,
    parent_id: str | None = None,
) -> dict[str, Any]:
    """Post a message to a channel. Optionally reply to a parent message."""
    return await get_client().post_channel_message(channel_id, content, parent_id, get_user_token())


@mcp.tool()
async def delete_channel_message(channel_id: str, message_id: str) -> dict[str, Any]:
    """Delete a message from a channel."""
    result = await get_client().delete_channel_message(channel_id, message_id, get_user_token())
    if isinstance(result, bool):
        return {"success": result}
    return result


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

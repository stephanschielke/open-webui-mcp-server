from typing import Optional

from pydantic import BaseModel, Field


class UserIdParam(BaseModel):
    user_id: str = Field(description="User ID")


class UserRoleParam(BaseModel):
    user_id: str = Field(description="User ID")
    role: str = Field(description="New role: 'admin', 'user', or 'pending'")


class GroupCreateParam(BaseModel):
    name: str = Field(description="Group name")
    description: str = Field(default="", description="Group description")


class GroupIdParam(BaseModel):
    group_id: str = Field(description="Group ID")


class GroupUpdateParam(BaseModel):
    group_id: str = Field(description="Group ID")
    name: Optional[str] = Field(default=None, description="New group name")
    description: Optional[str] = Field(default=None, description="New group description")


class GroupUserParam(BaseModel):
    group_id: str = Field(description="Group ID")
    user_id: str = Field(description="User ID to add/remove")


class ModelCreateParam(BaseModel):
    id: str = Field(description="Model ID (slug-format)")
    name: str = Field(description="Display name")
    base_model_id: str = Field(description="Base model ID")
    system_prompt: Optional[str] = Field(default=None, description="System prompt")
    temperature: Optional[float] = Field(default=None, description="Temperature (0.0-2.0)")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens")


class ModelIdParam(BaseModel):
    model_id: str = Field(description="Model ID")


class ModelUpdateParam(BaseModel):
    model_id: str = Field(description="Model ID")
    name: Optional[str] = Field(default=None, description="New display name")
    meta: Optional[dict] = Field(default=None, description="Model metadata")
    params: Optional[dict] = Field(default=None, description="Model parameters")


class KnowledgeCreateParam(BaseModel):
    name: str = Field(description="Knowledge base name")
    description: str = Field(default="", description="Knowledge base description")
    data: Optional[dict] = Field(default=None, description="Optional data object")


class KnowledgeIdParam(BaseModel):
    knowledge_id: str = Field(description="Knowledge base ID")


class KnowledgeUpdateParam(BaseModel):
    knowledge_id: str = Field(description="Knowledge base ID")
    name: Optional[str] = Field(default=None, description="New name")
    description: Optional[str] = Field(default=None, description="New description")


class FileIdParam(BaseModel):
    file_id: str = Field(description="File ID")


class FileSearchParam(BaseModel):
    filename: str = Field(description="Filename pattern (supports wildcards like *.pdf)")


class FileContentParam(BaseModel):
    file_id: str = Field(description="File ID")
    content: str = Field(description="New text content")


class PromptCreateParam(BaseModel):
    command: str = Field(description="Command trigger (e.g., '/summarize')")
    title: str = Field(description="Prompt title")
    content: str = Field(description="Prompt template content")


class PromptIdParam(BaseModel):
    prompt_id: str = Field(description="Prompt ID")


class PromptCommandParam(BaseModel):
    command: str = Field(description="Command (without leading slash)")


class PromptUpdateParam(BaseModel):
    prompt_id: str = Field(description="Prompt ID")
    title: Optional[str] = Field(default=None, description="New title")
    content: Optional[str] = Field(default=None, description="New content")


class MemoryAddParam(BaseModel):
    content: str = Field(description="Memory content to store")


class MemoryIdParam(BaseModel):
    memory_id: str = Field(description="Memory ID")


class MemoryUpdateParam(BaseModel):
    memory_id: str = Field(description="Memory ID")
    content: str = Field(description="New content")


class MemoryQueryParam(BaseModel):
    content: str = Field(description="Query text for semantic search")
    k: int = Field(default=5, description="Number of results to return")


class ChatIdParam(BaseModel):
    chat_id: str = Field(description="Chat ID")


class FolderCreateParam(BaseModel):
    name: str = Field(description="Folder name")


class FolderIdParam(BaseModel):
    folder_id: str = Field(description="Folder ID")


class FolderUpdateParam(BaseModel):
    folder_id: str = Field(description="Folder ID")
    name: str = Field(description="New folder name")


class ToolCreateParam(BaseModel):
    id: str = Field(description="Tool ID (slug-format)")
    name: str = Field(description="Tool name")
    content: str = Field(description="Tool Python code")
    meta: Optional[dict] = Field(default=None, description="Optional metadata")


class ToolIdParam(BaseModel):
    tool_id: str = Field(description="Tool ID")


class ToolUpdateParam(BaseModel):
    tool_id: str = Field(description="Tool ID")
    name: Optional[str] = Field(default=None, description="New name")
    content: Optional[str] = Field(default=None, description="New code")
    meta: Optional[dict] = Field(default=None, description="Optional metadata")


class FunctionCreateParam(BaseModel):
    id: str = Field(description="Function ID (slug-format)")
    name: str = Field(description="Function name")
    type: str = Field(description="Type: 'filter' or 'pipe'")
    content: str = Field(description="Function Python code")
    meta: Optional[dict] = Field(default=None, description="Optional metadata")


class FunctionIdParam(BaseModel):
    function_id: str = Field(description="Function ID")


class FunctionUpdateParam(BaseModel):
    function_id: str = Field(description="Function ID")
    name: Optional[str] = Field(default=None, description="New name")
    content: Optional[str] = Field(default=None, description="New code")


class NoteCreateParam(BaseModel):
    title: str = Field(description="Note title")
    content: str = Field(description="Note content (markdown supported)")


class NoteIdParam(BaseModel):
    note_id: str = Field(description="Note ID")


class NoteUpdateParam(BaseModel):
    note_id: str = Field(description="Note ID")
    title: Optional[str] = Field(default=None, description="New title")
    content: Optional[str] = Field(default=None, description="New content")


class ChannelCreateParam(BaseModel):
    name: str = Field(description="Channel name")
    description: str = Field(default="", description="Channel description")


class ChannelIdParam(BaseModel):
    channel_id: str = Field(description="Channel ID")


class ChannelUpdateParam(BaseModel):
    channel_id: str = Field(description="Channel ID")
    name: Optional[str] = Field(default=None, description="New channel name")
    description: Optional[str] = Field(default=None, description="New description")


class ChannelMessageParam(BaseModel):
    channel_id: str = Field(description="Channel ID")
    content: str = Field(description="Message content")
    parent_id: Optional[str] = Field(default=None, description="Parent message ID for threading")


class ChannelMessagesParam(BaseModel):
    channel_id: str = Field(description="Channel ID")
    skip: int = Field(default=0, description="Number of messages to skip")
    limit: int = Field(default=50, description="Maximum number of messages to return")


class ChannelMessageIdParam(BaseModel):
    channel_id: str = Field(description="Channel ID")
    message_id: str = Field(description="Message ID")

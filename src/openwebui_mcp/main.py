"""Open WebUI MCP Server - Main entry point.

This MCP server exposes Open WebUI's API as MCP tools, allowing AI assistants
to manage users, groups, models, knowledge bases, files, prompts, memories, and more.

IMPORTANT: All operations use the current user's session token automatically.
When configured with "session" auth in Open WebUI, the user's token is passed
through, ensuring all operations respect their permissions.
"""

import os

from openwebui_mcp.auth import AuthMiddleware
from openwebui_mcp.server import mcp


def main():
    """Run the MCP server."""
    import sys

    if not os.getenv("WEBUI_URL"):
        print("ERROR: WEBUI_URL environment variable is required", file=sys.stderr)
        print("Example: export WEBUI_URL=https://ai.example.com", file=sys.stderr)
        sys.exit(1)

    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    host = os.getenv("MCP_HTTP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_HTTP_PORT", "8000"))
    path = os.getenv("MCP_HTTP_PATH", "/mcp")

    if transport == "http":
        import uvicorn

        app = mcp.http_app(path=path)
        app = AuthMiddleware(app)
        # noinspection HttpUrlsUsage
        print(f"Starting Open WebUI MCP server on http://{host}:{port}{path}", file=sys.stderr)
        uvicorn.run(app, host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()

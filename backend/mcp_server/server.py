"""
Sentio MCP Server - Main entry point.

This server provides data access tools for LangGraph agents via the Model Context Protocol.
Run with: python -m mcp_server.server
"""

import asyncio
import sys
import os
import json
from typing import Any

# Add the backend directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import tool implementations
from mcp_server.tools import projects as projects_tools
from mcp_server.tools import stakeholders as stakeholders_tools
from mcp_server.tools import assessments as assessments_tools
from mcp_server.tools import recommendations as recommendations_tools
from mcp_server.tools import sessions as sessions_tools
from mcp_server.tools import surveys as surveys_tools
from mcp_server.tools import documents as documents_tools
from mcp_server.tools import workflow as workflow_tools

# Create the MCP server
server = Server("sentio-mcp")

# Collect all tools from modules
ALL_TOOLS = {}


def collect_tools():
    """Collect all tool definitions from tool modules."""
    modules = [
        projects_tools,
        stakeholders_tools,
        assessments_tools,
        recommendations_tools,
        sessions_tools,
        surveys_tools,
        documents_tools,
        workflow_tools,
    ]

    for module in modules:
        if hasattr(module, 'TOOLS'):
            ALL_TOOLS.update(module.TOOLS)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    collect_tools()
    return [
        Tool(
            name=name,
            description=tool_def["description"],
            inputSchema=tool_def["input_schema"]
        )
        for name, tool_def in ALL_TOOLS.items()
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    collect_tools()

    if name not in ALL_TOOLS:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    tool_def = ALL_TOOLS[name]
    handler = tool_def["handler"]

    try:
        result = await handler(**arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    """Main entry point for the MCP server."""
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

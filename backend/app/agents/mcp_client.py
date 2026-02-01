"""
MCP Client Manager for LangGraph Agents.

This module manages the connection to the Sentio MCP server and provides
tools to agents via langchain-mcp-adapters.
"""

import asyncio
import os
import sys
from typing import List, Optional

from langchain_mcp_adapters.client import MultiServerMCPClient


class MCPClientManager:
    """
    Singleton manager for MCP server connection.

    Provides tools to LangGraph agents via the MCP protocol.
    """

    _instance: Optional["MCPClientManager"] = None
    _client: Optional[MultiServerMCPClient] = None
    _tools: Optional[List] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_tools(cls) -> List:
        """
        Get MCP tools, initializing client if needed.

        Returns:
            List of LangChain tools from the MCP server
        """
        async with cls._lock:
            if cls._tools is None:
                await cls._initialize()
            return cls._tools

    @classmethod
    async def _initialize(cls):
        """Initialize the MCP client connection."""
        # Get the path to the mcp_server module
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        cls._client = MultiServerMCPClient({
            "sentio": {
                "command": sys.executable,  # Use the current Python interpreter
                "args": ["-m", "mcp_server.server"],
                "transport": "stdio",
                "cwd": backend_dir,  # Run from the backend directory
            }
        })

        # New API: get_tools() directly on the client
        cls._tools = await cls._client.get_tools()

    @classmethod
    async def disconnect(cls):
        """Disconnect from the MCP server."""
        async with cls._lock:
            if cls._client is not None:
                # The new API may handle cleanup differently
                # Try to close any sessions if available
                try:
                    if hasattr(cls._client, 'close'):
                        await cls._client.close()
                except Exception:
                    pass
                cls._client = None
                cls._tools = None

    @classmethod
    async def get_tool_by_name(cls, name: str):
        """
        Get a specific tool by name.

        Args:
            name: The name of the tool

        Returns:
            The tool object or None if not found
        """
        tools = await cls.get_tools()
        for tool in tools:
            if tool.name == name:
                return tool
        return None

    @classmethod
    async def get_tools_by_names(cls, names: List[str]) -> List:
        """
        Get multiple tools by their names.

        Args:
            names: List of tool names to retrieve

        Returns:
            List of matching tools
        """
        tools = await cls.get_tools()
        return [tool for tool in tools if tool.name in names]

    @classmethod
    async def invoke_tool(cls, name: str, **kwargs) -> str:
        """
        Invoke a tool by name with the given arguments.

        Args:
            name: The name of the tool to invoke
            **kwargs: Arguments to pass to the tool

        Returns:
            The tool's response as a JSON string
        """
        tool = await cls.get_tool_by_name(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        result = await tool.ainvoke(kwargs)

        # langchain-mcp-adapters returns a list of content objects
        # Extract the text from the first TextContent object
        if isinstance(result, list) and len(result) > 0:
            # Handle content objects like [{'type': 'text', 'text': '...'}]
            first_item = result[0]
            if isinstance(first_item, dict) and 'text' in first_item:
                return first_item['text']
            # Handle other list formats (e.g., direct list of results)
            return str(result)

        return str(result) if result is not None else "{}"

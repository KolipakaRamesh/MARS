"""
MARS — MCP Client.

Provides connectivity to external MCP servers, allowing MARS agents
to use tools provided by the broader MCP ecosystem.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Connects to an MCP server and exposes its tools as MARS-compatible functions.
    """

    def __init__(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
        self.name = name
        self.parameters = StdioServerParameters(
            command=command,
            args=args or [],
            env=env
        )
        self._session: Optional[ClientSession] = None
        self._exit_stack = None

    async def connect(self):
        """Establish connection to the MCP server."""
        if self._session:
            return

        logger.info("Connecting to MCP server: %s", self.name)
        try:
            # We use a simplified connection pattern for now
            self._client_gen = stdio_client(self.parameters)
            self._read, self._write = await self._client_gen.__aenter__()
            self._session = ClientSession(self._read, self._write)
            await self._session.__aenter__()
            await self._session.initialize()
            logger.info("MCP server '%s' initialized ✓", self.name)
        except Exception as exc:
            logger.error("Failed to connect to MCP server '%s': %s", self.name, exc)
            raise

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Fetch available tools from the server."""
        if not self._session:
            await self.connect()
        
        response = await self._session.list_tools()
        return [{"name": t.name, "description": t.description, "input_schema": t.inputSchema} for t in response.tools]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Call a specific tool on the MCP server."""
        if not self._session:
            await self.connect()

        try:
            result = await self._session.call_tool(tool_name, arguments)
            # Standard MCP tools return content list
            text_parts = [c.text for c in result.content if hasattr(c, 'text')]
            return "\n".join(text_parts) if text_parts else str(result)
        except Exception as exc:
            logger.error("MCP tool call failed (%s/%s): %s", self.name, tool_name, exc)
            return f"Error: {str(exc)}"

    async def disconnect(self):
        """Close connection."""
        if self._session:
            await self._session.__aexit__(None, None, None)
            await self._client_gen.__aexit__(None, None, None)
            self._session = None
            logger.info("Disconnected from MCP server: %s", self.name)


async def get_tools_from_server(name: str, command: str, args: List[str] = None) -> List[Dict[str, Any]]:
    """Helper to quickly list tools from a server without keeping connection open."""
    client = MCPClient(name, command, args)
    try:
        await client.connect()
        tools = await client.list_tools()
        return tools
    finally:
        await client.disconnect()

"""
MARS — MCP Server.

Exposes MARS research tools via the Model Context Protocol.
This allows MARS to be used as a tool provider for other agents.
"""
import asyncio
import logging
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from backend.tools.registry import build_default_registry

logger = logging.getLogger(__name__)

# Initialize MARS tool registry
registry = build_default_registry()

server = Server("mars-research-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available research tools."""
    tools = []
    for t in registry.list_tools():
        tools.append(types.Tool(
            name=t["name"],
            description=t["description"],
            inputSchema={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "The input string for the tool"
                    }
                },
                "required": ["input"]
            }
        ))
    return tools

@server.call_tool()
async def handle_call_tool(
    name: str, 
    arguments: dict | None
) -> list[types.TextContent]:
    """Execute a research tool."""
    if not arguments or "input" not in arguments:
        raise ValueError("Missing 'input' argument")
    
    input_str = arguments["input"]
    
    # Execute the tool via our registry
    result = await registry.call(name, input_str)
    
    return [
        types.TextContent(
            type="text",
            text=result
        )
    ]

async def main():
    """Run the MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mars-research-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

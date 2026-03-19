import asyncio
from mcp.client import ClientSession

class MCPBridge:
    def __init__(self):
        self.session = ClientSession()

    def call(self, tool_name: str, args: dict):
        return asyncio.run(self.session.call_tool(tool_name, args))


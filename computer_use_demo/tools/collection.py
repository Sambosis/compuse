## collection.py
"""Collection classes for managing multiple tools."""

from typing import Union, List, Dict, Any, Optional

from anthropic.types.beta import BetaToolUnionParam
from icecream import ic
from .base import (
    BaseAnthropicTool,
    ToolError,
    ToolFailure,
    ToolResult,
)
from rich import print as rr
def write_to_file(s):
  with open('icecream_output.txt', 'a') as f:
    f.write(s + '\n')

class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, *tools: BaseAnthropicTool):
        self.tools = tools
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}

    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
        return [tool.to_params() for tool in self.tools]

    async def run(self, *, name: str, tool_input: dict[str, Any]) -> ToolResult:
        ic.configureOutput(includeContext=True, outputFunction=rr)
        ic()
        # ic.configureOutput(includeContext=True, outputFunction=write_to_file)

        tool = self.tool_map.get(name)
    
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            ic(tool_input)
            return await tool(**tool_input)
        except ToolError as e:
            return "ToolFailure(error=e.message)"

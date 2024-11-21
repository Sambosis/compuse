## collection.py
"""Collection classes for managing multiple tools."""

<<<<<<< HEAD
from typing import Any
=======
from typing import Union, List, Dict, Any, Optional
>>>>>>> 762abff2d378c3944d7e1d8a7f2f24cc7c1b4e3d
import json
from anthropic.types.beta import BetaToolUnionParam
from icecream import ic
from .base import (
    BaseAnthropicTool,
    ToolError,
    ToolFailure,
    ToolResult,
)
<<<<<<< HEAD
ICECREAM_OUTPUT_FILE = "debug_log.json"
=======
from rich import print as rr
ICECREAM_OUTPUT_FILE = "debug_log.txt"
>>>>>>> 762abff2d378c3944d7e1d8a7f2f24cc7c1b4e3d

def write_to_file(s, file_path=ICECREAM_OUTPUT_FILE):
    """
    Write debug output to a file, formatting JSON content in a pretty way.
    """
    lines = s.split('\n')
    formatted_lines = []
    
    for line in lines:
        if "tool_input:" in line:
            try:
                # Extract JSON part from the line
                json_part = line.split("tool_input: ")[1]
                # Parse and pretty-print the JSON
                json_obj = json.loads(json_part)
                pretty_json = json.dumps(json_obj, indent=4)
                formatted_lines.append("tool_input: " + pretty_json)
            except (IndexError, json.JSONDecodeError):
                # If parsing fails, just append the original line
                formatted_lines.append(line)
        else:
            formatted_lines.append(line)
    
    # Write to file
    with open(file_path, 'a', encoding="utf-8") as f:
        f.write('\n'.join(formatted_lines))
        f.write('\n' + '-' * 80 + '\n')  # Add separator between entries
<<<<<<< HEAD
=======

# Configure icecream
ic.configureOutput(includeContext=True, outputFunction=write_to_file)    # Write to file

# Configure icecream
ic.configureOutput(includeContext=True, outputFunction=rr)
ic()
ic.configureOutput(includeContext=True, outputFunction=write_to_file)
>>>>>>> 762abff2d378c3944d7e1d8a7f2f24cc7c1b4e3d

class ToolCollection:
    """A collection of anthropic-defined tools."""

    def __init__(self, *tools: BaseAnthropicTool):
        self.tools = tools
        ic(self.tools)
        self.tool_map = {tool.to_params()["name"]: tool for tool in tools}
        ic(self.tool_map)
    def to_params(
        self,
    ) -> list[BetaToolUnionParam]:
<<<<<<< HEAD
        ic()
        params = [tool.to_params() for tool in self.tools]
        if params:
            params[-1]["cache_control"] = {"type": "ephemeral"}
=======

        params = [tool.to_params() for tool in self.tools]
        params[-1]["cache_control"] = {"type": "ephemeral"}
>>>>>>> 762abff2d378c3944d7e1d8a7f2f24cc7c1b4e3d
        return params

    async def run(self, *, name: str, tool_input: dict[str, Any]) -> ToolResult:
        ic.configureOutput(includeContext=True, outputFunction=write_to_file)

        tool = self.tool_map.get(name)
    
        if not tool:
            return ToolFailure(error=f"Tool {name} is invalid")
        try:
            ic(tool_input)
            return await tool(**tool_input)
        except ToolError as e:
<<<<<<< HEAD
            return ToolFailure(error=e.message)
=======
            return "ToolFailure(error=e.message)"
>>>>>>> 762abff2d378c3944d7e1d8a7f2f24cc7c1b4e3d
#"C:/repo/code_test/code_context_manager.py"
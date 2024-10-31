## bash.py
import asyncio
import os
from typing import ClassVar, Literal
from anthropic.types.beta import BetaToolBash20241022Param
from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
import subprocess
import platform
# Using subprocess directly for shell commands

class BashTool(BaseAnthropicTool):
    """
    A tool that allows the agent to run bash commands. On Windows it uses PowerShell
    The tool parameters are defined by Anthropic and are not editable.
    """

    name: ClassVar[Literal["bash"]] = "bash"
    api_type: ClassVar[Literal["bash_20241022"]] = "bash_20241022"

    async def __call__(
        self, command: str | None = None, **kwargs
    ):
        if command is not None:
             if platform.system() == 'Windows':
                 command = f"powershell.exe -command {command}" # Run PowerShell commands on Windows
             return await self._run_command(command)

        raise ToolError("no command provided.")

    async def _run_command(self, command: str):
        """Execute a command in the shell."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode().strip() if stdout else ""
            error = stderr.decode().strip() if stderr else None


            return CLIResult(output=output, error=error)

        except Exception as e:

            return ToolResult(output=None, error=str(e))

    def to_params(self) -> BetaToolBash20241022Param:
        return {
            "type": self.api_type,
            "name": self.name,
        }   
    


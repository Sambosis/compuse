## bash.py
import asyncio
from typing import ClassVar, Literal
from anthropic.types.beta import BetaToolBash20241022Param
# from torch import error
from .base import BaseAnthropicTool, CLIResult, ToolError, ToolResult
import platform
# Using subprocess directly for shell commands
from rich import print as rr
def convert_bash_to_powershell(bash_command: str) -> str:
    """
    Convert a Bash command to its PowerShell equivalent.

    Args:
        bash_command (str): The Bash command as a string.

    Returns:
        str: The equivalent PowerShell command.

    Raises:
        ValueError: If the command or flags are unsupported.
    """
    command_map = {
        'ls': 'Get-ChildItem',
        'pwd': 'Get-Location',
        'cd': 'Set-Location',
        'cp': 'Copy-Item',
        'mv': 'Move-Item',
        'rm': 'Remove-Item',
        'cat': 'Get-Content',
        'echo': 'Write-Output',
        'mkdir': 'New-Item -ItemType Directory',
        'touch': 'New-Item -ItemType File -Force',
        'grep': 'Select-String',
        'find': 'Get-ChildItem',
    }

    flag_map = {
        'ls': {
            '-l': '',
            '-a': '-Force',
            '-la': '-Force',
            '-al': '-Force',
            '-R': '-Recurse',
            '-r': '-Recurse',
        },
        'rm': {
            '-r': '-Recurse',
            '-f': '-Force',
            '-rf': '-Recurse -Force',
            '-fr': '-Recurse -Force',
        },
        'cp': {
            '-r': '-Recurse',
            '-R': '-Recurse',
            '-f': '-Force',
        },
        'grep': {
            '-i': '-CaseSensitive:$false',
            '-v': '-NotMatch',
            '-r': '-Recurse',
            '-n': '',
        },
        'find': {
            '-name': '-Filter',
            '-iname': '-Filter',
            '-type': '',
        },
    }

    def translate_path(path: str) -> str:
        """Translate Unix-style paths to Windows-style paths."""
        if path.startswith('~'):
            path = path.replace('~', '$env:USERPROFILE')
        path = re.sub(r'\$(?!env:)(\w+)', r'$env:\1', path)  # Avoid double $env:
        path = path.replace('/', '\\')
        if re.match(r'^\\', path):
            path = 'C:' + path
        return f"'{path}'"

    def verify_path(path: str) -> str:
        """Verify if the translated path exists."""
        path = path.strip("'")
        if not os.path.exists(path):
            raise ValueError(f"Path '{path}' does not exist.")
        return path

    parts = shlex.split(bash_command)
    if not parts:
        raise ValueError("Empty command provided.")

    command = parts[0]
    args = parts[1:]

    if command not in command_map:
        raise ValueError(f"Unsupported command: '{command}'.")

    ps_command = command_map[command]
    ps_args = []

    if command == 'grep':
        # Handle grep specifically
        flags = []
        search_term = None
        file_path = None

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if arg in flag_map[command]:
                    flags.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            elif search_term is None:
                search_term = arg
            elif file_path is None:
                file_path = translate_path(arg)
            else:
                raise ValueError(f"Unexpected argument '{arg}' for command 'grep'.")
            i += 1

        if not search_term:
            raise ValueError("Missing search term for 'grep'.")
        if not file_path:
            raise ValueError("Missing file path for 'grep'.")

        ps_args.append(f"-Pattern {search_term}")
        ps_args.append(f"-Path {file_path}")
        ps_args.extend(flags)

    elif command == 'find':
        # Handle find specifically
        base_path = None
        flags = []

        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if arg == '-type':
                    i += 1
                    if i < len(args):
                        type_arg = args[i]
                        if type_arg == 'f':
                            flags.append('| Where-Object { -not $_.PSIsContainer }')
                        elif type_arg == 'd':
                            flags.append('| Where-Object { $_.PSIsContainer }')
                        else:
                            raise ValueError(f"Unsupported type '{type_arg}' for '-type'.")
                    else:
                        raise ValueError("Expected type after '-type'.")
                elif arg in ['-name', '-iname']:
                    i += 1
                    if i < len(args):
                        name_arg = args[i]
                        flags.append(f"| Where-Object {{ $_.Name -like '{name_arg}' }}")
                    else:
                        raise ValueError(f"Expected pattern after '{arg}'.")
                elif arg in flag_map[command]:
                    flags.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            elif base_path is None:
                base_path = translate_path(arg)
            else:
                raise ValueError(f"Unexpected argument '{arg}' for command 'find'.")
            i += 1

        if not base_path:
            raise ValueError("Missing base path for 'find'.")

        ps_args.append(f"-Path {base_path}")
        ps_args.extend(flags)

    elif command == 'echo':
        ps_args.append(f"'{ ' '.join(args) }'")

    elif command == 'rm':
        ps_args.append('-ErrorAction SilentlyContinue')
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if command in flag_map and arg in flag_map[command]:
                    ps_args.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            else:
                ps_args.append(translate_path(arg))
            i += 1

    else:
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-'):
                if command in flag_map and arg in flag_map[command]:
                    ps_args.append(flag_map[command][arg])
                else:
                    raise ValueError(f"Unsupported flag '{arg}' for command '{command}'.")
            else:
                ps_args.append(translate_path(arg))
            i += 1

    return f"{ps_command} {' '.join(ps_args)}"

class BashTool(BaseAnthropicTool):
    description="""
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
                 command = convert_bash_to_powershell(command)  
                 
                 command = f"powershell.exe -command cd c:/repo && {command}" # Run PowerShell commands on Windows
             return await self._run_command(command)

        raise ToolError("no command provided.")

    async def _run_command(self, command: str):
        """Execute a command in the shell."""
        try:
            rr(command)
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode().strip() if stdout else ""
            error = stderr.decode().strip() if stderr else None
            rr(output)
            if error:
                rr(error)

            return CLIResult(output=output, error=error)

        except Exception as e:

            return ToolResult(output=None, error=str(e))

    def to_params(self) -> BetaToolBash20241022Param:
        return {
            "type": self.api_type,
            "name": self.name,
        }   
    


## base.py
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, replace
from typing import Any, Optional, Dict



class BaseAnthropicTool(metaclass=ABCMeta):
    """Base class for all tools."""

    def __init__(self, input_schema: Optional[Dict[str, Any]] = None):
        self.input_schema = input_schema or {
            "type": "object",
            "properties": {},
            "required": []
        }

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does."""
        pass

    @abstractmethod
    def __call__(self, **kwargs) -> Any:
        """Execute the tool with the given arguments."""
        pass

    def to_params(self) -> Dict[str, Any]:
        """Convert the tool to xAI API parameters."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema
            }
        }


@dataclass(kw_only=True, frozen=True)
class ToolResult:
    """Represents the result of a tool execution."""

    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None
    system: Optional[str] = None

    def __bool__(self):
        return any(getattr(self, field.name) for field in fields(self))

    def __add__(self, other: "ToolResult"):
        def combine_fields(
            field: str | None, other_field: str | None, concatenate: bool = True
        ):
            if field and other_field:
                if concatenate:
                    return field + other_field
                raise ValueError("Cannot combine tool results")
            return field or other_field

        return ToolResult(
            output=combine_fields(self.output, other.output),
            error=combine_fields(self.error, other.error),
            base64_image=combine_fields(self.base64_image, other.base64_image, False),
            system=combine_fields(self.system, other.system),
        )

    def replace(self, **kwargs):
        """Returns a new ToolResult with the given fields replaced."""
        return replace(self, **kwargs)


class CLIResult(ToolResult):
    """A ToolResult that can be rendered as a CLI output."""
    pass


class ToolFailure(ToolResult):
    """A ToolResult that represents a failure."""
<<<<<<< HEAD
    pass


=======
>>>>>>> 762abff2d378c3944d7e1d8a7f2f24cc7c1b4e3d
@dataclass(kw_only=True, frozen=True)
class ToolError(Exception):
    """Raised when a tool encounters an error."""
    message: str

    def __init__(self, message: str):
<<<<<<< HEAD
        object.__setattr__(self, 'message', message)
=======
        # Use object.__setattr__ to set attributes on frozen dataclass
        object.__setattr__(self, 'message', message)
        # Initialize the parent Exception class
>>>>>>> 762abff2d378c3944d7e1d8a7f2f24cc7c1b4e3d
        super().__init__(message)

    def __str__(self):
        return self.message
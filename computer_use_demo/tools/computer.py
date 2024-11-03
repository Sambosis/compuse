## computer.py

import asyncio
import base64
import os
import platform
from enum import StrEnum
from typing import List, Optional, Union, Tuple, Literal, TypedDict
from pathlib import Path
from uuid import uuid4
import pyautogui
import logging
import concurrent.futures
import time
import pygetwindow as gw
from anthropic.types.beta import BetaToolComputerUse20241022Param
import pyperclip
from .base import CLIResult, ToolError, ToolResult, BaseAnthropicTool

# Configure logging with platform-appropriate paths
if platform.system() == 'Windows':
    LOG_FILE = Path(os.getenv('APPDATA')) / 'computer_tool' / 'logs.txt'
    SCREENSHOT_DIR = Path(os.getenv('APPDATA')) / 'computer_tool' / 'screenshots'
else:
    LOG_FILE = Path.home() / '.computer_tool' / 'logs.txt'
    SCREENSHOT_DIR = Path.home() / '.computer_tool' / 'screenshots'

# Ensure directories exist
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    filename=str(LOG_FILE),
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
    # "speak",  # Add speak action
    "open_url", # Add open_url action
    "get_window_title", # Add get_window_title
]

class Resolution(TypedDict):
    width: int
    height: int


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"

class Options(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: Optional[int]

class GuiAutomation: # removed unecessary async functions and made synchronous
    """Helper class for common GUI automation patterns"""

    @staticmethod
    def open_chrome(url: Optional[str] = None):
        """Open Chrome and optionally navigate to a URL."""
        pyautogui.press('start')
        time.sleep(0.5)
        pyautogui.write('chrome')
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(2) # give chrome time to open

        if url:
                pyautogui.hotkey('ctrl', 'l')
                time.sleep(0.2)
                pyperclip.copy(url)
                pyperclip.paste()
                pyautogui.press('enter')


    @staticmethod
    def wait_for_window(title: str, timeout: int = 10) -> bool:
        elapsed_time = 0
        while elapsed_time < timeout:
            if any(title in w.title for w in gw.getAllWindows()):
                return True
            time.sleep(0.2)
            elapsed_time += 0.2
        return False

    @staticmethod
    def switch_app(key_combo: Union[str, Tuple[str, ...]]):
        """Switch between applications using keyboard shortcuts."""
        if isinstance(key_combo, str):
            pyautogui.press(key_combo)
        else:
            pyautogui.hotkey(*key_combo)
        time.sleep(0.5)

    @staticmethod
    def copy_selection():
        """Copy current selection to clipboard."""
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)  # Wait for clipboard

    @staticmethod
    def paste_text():
        """Paste clipboard content."""
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)



class WindowsUseTool(BaseAnthropicTool):
    """
    A Windows-specific tool that allows the agent to interact with the screen, keyboard, and mouse.
    """

    name: Literal["windows"] = "windows"
    api_type: Literal["custom"] = "custom"
    width: int
    height: int
    display_num: Optional[int]

    _screenshot_delay = 1.0
    _scaling_enabled = True

    @property
    def options(self) -> Options:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": self.display_num,
        }

    def to_params(self) -> dict:
        return {
            "name": self.name,
            "type": self.api_type,
            "description": "A tool for controlling Windows GUI elements using mouse and keyboard",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "key",
                            "type",
                            "mouse_move",
                            "left_click",
                            "left_click_drag",
                            "right_click",
                            "middle_click",
                            "double_click",
                            "screenshot",
                            "cursor_position",
                            "open_url",
                            "get_window_title"
                        ],
                        "description": "The action to perform"
                    },
                    "text": {
                        "type": "string",
                        "description": "Text to type or key to press"
                    },
                    "coordinate": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                        "description": "X,Y coordinates for mouse actions"
                    },
                    "url": {
                        "type": "string",
                        "description": "URL to open in browser"
                    }
                },
                "required": ["action"]
            }
        }

    def __init__(self):
        super().__init__()

        # Get screen size using pyautogui instead of fixed values
        screen_width, screen_height = pyautogui.size()
        self.width = screen_width
        self.height = screen_height

        # Handle display number (Not relevant for Windows, maintain None)
        self.display_num = None

        logging.debug(f"Initialized  with resolution: {self.width}x{self.height}")

    async def __call__(
        self,
        *,
        action: Action,
        text: Optional[str] = None,
        coordinate: Optional[tuple[int, int]] = None,
        url: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        logging.debug(f"Action: {action}, Text: {text}, Coordinate: {coordinate}")

        try:
            # Fail-safe in case the mouse goes out of control
            pyautogui.FAILSAFE = True
            start_time = time.time()

            if action == "key":
                if not text:
                    raise ToolError("No key specified for 'key' action.")
                pyautogui.press(text)
                return ToolResult(output=f"Pressed key: {text}", error=None)

            elif action == "type":
                if not text:
                    raise ToolError("No text specified for 'type' action.")
                # Handle platform-specific line endings (Not needed for ctrl+v)
                
                # Type using pyperclip for better handling of special characters and unicode
                original_clipboard = pyperclip.paste()
                try:
                    pyperclip.copy(text)
                    pyautogui.hotkey('ctrl', 'v')
                    return ToolResult(output=f"Typed text: {text}", error=None)
                finally:
                    pyperclip.copy(original_clipboard)


            elif action == "mouse_move":
                if not coordinate or len(coordinate) != 2:
                    raise ToolError("Invalid coordinates for 'mouse_move' action.")
                x, y = coordinate
                # Ensure coordinates are within screen bounds
                if not (0 <= x <= self.width and 0 <= y <= self.height):
                    raise ToolError(f"Coordinates {coordinate} are out of screen bounds ({self.width}x{self.height})")
                pyautogui.moveTo(x, y)
                return ToolResult(output=f"Moved mouse to {coordinate}", error=None)

            elif action == "left_click":
                pyautogui.click(button='left')
                return ToolResult(output="Left clicked", error=None)

            elif action == "right_click":
                pyautogui.click(button='right')
                return ToolResult(output="Right clicked", error=None)

            elif action == "middle_click":
                pyautogui.click(button='middle')
                return ToolResult(output="Middle clicked", error=None)

            elif action == "double_click":
                pyautogui.doubleClick()
                return ToolResult(output="Double clicked", error=None)

            elif action == "screenshot":
                return await self.screenshot()

            elif action == "cursor_position":
                position = pyautogui.position()
                return ToolResult(output=str(position), error=None)

            elif action == "speak": # new action
                if not text:
                    raise ToolError("No text specified for 'speak' action.")
                # Requires a platform-specific implementation (Example uses Windows)
                if platform.system() == 'Windows':
                    # Escape double quotes in the text
                    escaped_text = text.replace('"', '\\"')
                    await self.shell(f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\"{escaped_text}\")"') # uses powershell to speak on windows
                else:
                    # Replace with appropriate command for other platforms (e.g., say on macOS)
                    await self.shell(f"say '{text}'")  # Example for macOS

                return ToolResult(output=f"Spoke text: {text}", error=None)
            
            elif action == "open_url":
                if not url:
                    raise ToolError("No URL specified for 'open_url' action.")
                GuiAutomation.open_chrome(url) # added this
                return ToolResult(output=f"Opened URL: {url}", error=None)


            elif action == "get_window_title": # new action
                current_window = gw.getActiveWindow()
                if current_window:
                    return ToolResult(output=current_window.title, error=None)
                else:
                    return ToolResult(output="No active window found", error=None)


            else:
                raise ToolError(f"Unsupported action: {action}")

        except pyautogui.FailSafeException:
            error_msg = "PyAutoGUI fail-safe triggered. Mouse moved to a corner of the screen."
            logging.error(error_msg)
            return ToolResult(output=None, error=error_msg, base64_image=None)
        except ToolError as te:
            logging.error(f"Tool Error: {te}")
            return ToolResult(output=None, error=str(te), base64_image=None)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return ToolResult(output=None, error=str(e), base64_image=None)


    async def shell(self, command: str, take_screenshot=True) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        logging.debug(f"Executing command: {command}")
        try:
            # Use PowerShell for Windows and default shell otherwise
            if platform.system() == 'Windows':
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True  # Use cmd.exe on Windows to call powershell
                )

            else:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )


            stdout, stderr = await process.communicate()

            stdout = stdout.decode().strip() if stdout else ""
            stderr = stderr.decode().strip() if stderr else None

            logging.debug(f"Command output: {stdout}")
            if stderr:
                logging.debug(f"Command error: {stderr}")

            base64_image = None

            if take_screenshot:
                await asyncio.sleep(self._screenshot_delay)
                base64_image = (await self.screenshot()).base64_image

            return ToolResult(output=stdout, error=stderr, base64_image=base64_image)
        except Exception as e:
            logging.error(f"Error executing command '{command}': {e}")
            return ToolResult(output=None, error=str(e), base64_image=None)


    async def screenshot(self) -> ToolResult:
        """Take a screenshot and return the base64-encoded image."""
        try:
            screenshot_path = SCREENSHOT_DIR / f"screenshot_{uuid4().hex}.png"
            pyautogui.screenshot(str(screenshot_path)) # removed unnecessary async call

            with open(screenshot_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            # Clean up old screenshots to prevent disk space issues
            self._cleanup_old_screenshots()

            return ToolResult(output="Screenshot taken", error=None, base64_image=base64_image)
        except Exception as e:
            logging.error(f"Error taking screenshot: {e}")
            return ToolResult(output=None, error=str(e), base64_image=None)

    def _cleanup_old_screenshots(self, max_files: int = 100):
        """Clean up old screenshots to prevent disk space issues."""
        try:
            screenshots = sorted(SCREENSHOT_DIR.glob("*.png"), key=lambda x: x.stat().st_mtime)
            if len(screenshots) > max_files:
                for screenshot in screenshots[:-max_files]:
                    screenshot.unlink()
        except Exception as e:
            logging.warning(f"Error cleaning up screenshots: {e}")


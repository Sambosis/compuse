#loop.py
"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
"""
from http import client
from json import tool
from re import X
from icecream import ic
import platform
from collections.abc import Callable
from datetime import datetime
from enum import StrEnum
from typing import Any, cast, List, Optional
from pathlib import Path
import httpx
from anthropic import APIResponse
from anthropic.types.beta import BetaContentBlock
import hashlib
import base64
import os
import asyncio  
import pyautogui
from regex import R, W
from rich import print as rr
from icecream import install
from openai import OpenAI
# load the API key from the environment
import os
from dotenv import load_dotenv
load_dotenv()
install()
import json
from icecream import ic

ICECREAM_OUTPUT_FILE = "debug_log.txt"

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

# Configure icecream
ic.configureOutput(includeContext=True, outputFunction=write_to_file)
# Define the system prompt
# read the system prompt from a file named system_prompt.md
with open(r"C:\mygit\compuse\computer_use_demo\system_prompt.md", 'r',encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

rr(SYSTEM_PROMPT)



from anthropic import (
    Anthropic,
    AnthropicBedrock,
    AnthropicVertex,
    APIError,
    APIResponseValidationError,
    APIStatusError,
)
from anthropic.types.beta import (
    BetaCacheControlEphemeralParam,
    BetaContentBlockParam,
    BetaImageBlockParam,
    BetaMessage,
    BetaMessageParam,
    BetaTextBlock,
    BetaTextBlockParam,
    BetaToolResultBlockParam,
    BetaToolUseBlockParam,
)

from tools import BashTool, WindowsUseTool, EditTool, ToolCollection, ToolResult, GetExpertOpinionTool, WebNavigatorTool, GoToURLReportsTool

class OutputManager:
    """Manages and formats tool outputs and responses."""

    def __init__(self, image_dir: Optional[Path] = None ):
        # Set up image directory
        self.image_dir = image_dir
        self.image_dir.mkdir(parents=True, exist_ok=True)
        self.image_counter = 0

    def save_image(self, base64_data: str) -> Optional[Path]:
        """Save base64 image data to file and return path."""
        self.image_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a short hash of the image data for uniqueness
        image_hash = hashlib.md5(base64_data.encode()).hexdigest()[:8]
        image_path = self.image_dir / f"image_{timestamp}_{image_hash}.png"

        try:
            image_data = base64.b64decode(base64_data)
            with open(image_path, 'wb') as f:
                f.write(image_data)
            return image_path
        except Exception as e:
            ic(f"Error saving image: {e}")
            return None

    def format_tool_output(self, result: ToolResult, tool_id: str) -> None:
        """Format and print tool output without base64 data."""
        # ic(f"Tool Execution [{tool_id}]:")
        if result.error:
            ic(f"ERROR: {result.error}")
        else:
            if result.output:
                ic(f"Output: {result.output}")
                rr(result.output[:1000])
            
            if result.base64_image:
                image_path = self.save_image(result.base64_image)
                if image_path:
                    ic(f"Screenshot saved: {image_path}")
                else:
                    ic("Failed to save screenshot")

    def format_api_response(self, response: APIResponse) -> None:
        """Format and print API response."""
        ic(f"\nAPI Response ID: {getattr(response, 'id', 'unknown')}")
        # ic(f"API Response Content: {response.content}")
        # print out the available methods and attributes of the response object

        rr(f"Claude Response: {response.content[0].text}")
    def format_content_block(self, block: BetaContentBlock) -> None:
        """Format and print content block."""
        if getattr(block, 'type', None) == "tool_use":
            ic(f"\nTool Use: {block.name}")
            # Only print non-image related inputs
            safe_input = {k: v for k, v in block.input.items()
                         if not isinstance(v, str) or len(v) < 1000}
            ic(f"Input: {safe_input}")
        elif hasattr(block, 'text'):
            ic(f"\nText: {block.text}")

def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> dict:
    """Convert tool result to API format."""
    tool_result_content = []
    is_error = False
    ic(result)
    rr("Tool Result Content: ")
    if result.error:
        is_error = True
        tool_result_content.append({
            "type": "text",
            "text": result.error
        })
    else:
        if result.output:
            tool_result_content.append({
                "type": "text",
                "text": result.output
            })
        if result.base64_image:
            tool_result_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": result.base64_image,
                }
            })
            rr("Image Source: base64 source too big")

    
    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }



COMPUTER_USE_BETA_FLAG = "computer-use-2024-10-22"
PROMPT_CACHING_BETA_FLAG = "prompt-caching-2024-07-31"


# SYSTEM_PROMPT = """You are a eager, pro-active assistant with access to Windows GUI automation, web browsing and a programming environment where you can develop and execute code.
# * You are utilizing a Windows machine with internet access via the WindowsUseTool.
# * The WindowsUseTool provides actions for:
#   - Keyboard input ("key", "type")
#   - Mouse control ("mouse_move", "left_click", "right_click", "middle_click", "double_click")
#   - Screen capture ("screenshot")
#   - Browser automation ("open_url")
#   - Window management ("get_window_title")
#   - Cursor information ("cursor_position")
# * You should always use Chrome Browser when searching the internet via the "open_url" action.
# * You can install Windows applications using PowerShell. Use Invoke-WebRequest for downloading files.
# * You can send keys using pyautogui to automate tasks by controlling the mouse and keyboard, especially useful for keyboard shortcuts.
# * If GUI app launching fails, you can use PowerShell's Start-Process command as a fallback.
#     - You can:
#     - Search the web and read web pages
#     - Create and edit documents
#     - Install apps and packages
#     - Write and execute scripts and Python code
#     - Use py.exe to execute python code
#     - Use uv pip install to install packages
#     - Use VS Code to develop apps
#     - Take screenshots to help you monitor your progress
#     - Use the clipboard for efficient data transfer

#     Valid pyautogui keyboard keys include:
#     ['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
#     ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
#     '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
#     'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
#     'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
#     'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
#     'browserback', 'browserfavorites', 'browserforward', 'browserhome',
#     'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
#     'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
#     'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
#     'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
#     'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
#     'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
#     'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
#     'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
#     'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
#     'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
#     'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
#     'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
#     'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
#     'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
#     'command', 'option', 'optionleft', 'optionright']

#     Best Practices:
#     * When viewing a webpage, zoom out to see everything or scroll down completely before concluding something isn't available
#     * WindowsUseTool actions take time to execute - chain multiple actions into one request when feasible
#     * For PDFs, consider downloading and converting to text for better processing
#     * Before interacting with a window, take a screenshot to verify the active window and tab
#     * After completing an action, take a screenshot to verify success
#     * Always evaluate available applications and choose the best method for the task
#     Rembember, you are working in windows and will be working on the C: drive.
#     Directories should look like C:/path/to/directory and files should look like C:/path/to/file.txt
#     when possible use the raw string format r'C:/path/to/file.txt'
#     The current date is {datetime.today()}.
# """

async def sampling_loop(*, model: str, messages: List[BetaMessageParam], api_key: str, max_tokens: int = 8000,) -> List[BetaMessageParam]:
    ic()
    tool_collection = ToolCollection(
                                        BashTool(),
                                        EditTool(),
                                        GetExpertOpinionTool(),
                                        WindowsUseTool(),
                                        WebNavigatorTool(),
                                        GoToURLReportsTool(),  # Add the GoToURLReportsTool instance
                                    )
    ic(tool_collection)            
    system = BetaTextBlockParam(
                                type="text",
                                text=f"{SYSTEM_PROMPT}",  
                                )
    output_manager = OutputManager(image_dir=Path('logs/computer_tool_images')  )
    client = Anthropic(api_key=api_key)
    i=1
    running = True
    while running:
        rr(f"Iteration {i}")
        i+=1
        enable_prompt_caching = True
        betas = [COMPUTER_USE_BETA_FLAG, PROMPT_CACHING_BETA_FLAG]
        image_truncation_threshold = 10
        only_n_most_recent_images = 3
        if enable_prompt_caching:
            _inject_prompt_caching(messages)
            # Is it ever worth it to bust the cache with prompt caching?
            image_truncation_threshold = 50
            system=[
                        {
                            "type": "text",
                            "text": SYSTEM_PROMPT,
                            "cache_control": {"type": "ephemeral"}
                        },
                    ]

        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(
                messages,
                only_n_most_recent_images,
                min_removal_threshold=image_truncation_threshold,
            )

        try:
            ic(tool_collection.to_params())
            ic(f"Messages: {messages}")
            # if i % 2 == 0:
            #     # wait for 10 seconds
                # await asyncio.sleep(10) 

            response = client.beta.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=system,
                tools=tool_collection.to_params(),
                betas=betas,
                )
            rr(f"Cache Creation Tokens: {response.usage.cache_creation_input_tokens}")
            rr(f"Cache Retrieval Tokens: {response.usage.cache_read_input_tokens}")
            rr(f"Output Tokens: {response.usage.output_tokens}")
            rr(f"Input Tokens: {response.usage.input_tokens}")
            ic(f"Response: {response}")
            # output_manager.format_api_response(response)
            
            # Convert response content to params format
            response_params = []
            for block in response.content:
                if hasattr(block, 'text'):
                    output_manager.format_api_response(response)

                    response_params.append({
                        "type": "text",
                        "text": block.text
                    })
                elif getattr(block, 'type', None) == "tool_use":
                    response_params.append({
                        "type": "tool_use",
                        "name": block.name,
                        "id": block.id,
                        "input": block.input
                    })
            # Append assistant message with full response content
            messages.append({
                "role": "assistant",
                "content": response_params
            })
            # Process tool uses and collect results
            tool_result_content: list[BetaToolResultBlockParam] = []
            for content_block in response_params:
                output_manager.format_content_block(content_block)
                if content_block["type"] == "tool_use":
                    ic(f"Tool Use: {response_params}")
                    result = await tool_collection.run(
                        name=content_block["name"],
                        tool_input=content_block["input"],
                    )
                    ic.configureOutput(includeContext=True, outputFunction=rr,argToStringFunction=repr)
                    ic()
                    ic.configureOutput(includeContext=True, outputFunction=write_to_file,argToStringFunction=repr)
                    ic(content_block)
                    output_manager.format_tool_output(result, content_block["id"])
                    ic()
                    tool_result = _make_api_tool_result(result, content_block["id"])
                    ic(tool_result)
                    tool_result_content.append(tool_result)
                    ic(tool_result_content)
            # If no tool results, we're done
            if not tool_result_content:
                pyautogui.alert('cecking for usner input')
                task = input("What would you like to do next?  Enter 'no' to exit: ")
                if task.lower() == "no" or task.lower() == "n":
                    running = False
                messages.append({"role": "user","content": task})   
            else:
                # Append tool results as user message
                messages.append({
                    "role": "user",
                    "content": tool_result_content
                })
        except UnicodeEncodeError as ue:
            ic(f"UnicodeEncodeError: {ue}")
            rr(f"Unicode encoding error: {ue}")
            rr(f"ascii: {ue.args[1].encode('ascii', errors='replace').decode('ascii')}")
            # Handle or skip the problematic message
            break        
        except Exception as e:
            ic(f"Error in sampling loop: {str(e).encode('ascii', errors='replace').decode('ascii')}")
            ic(f"The error occurred at the following message: {messages[-1]} and line: {e.__traceback__.tb_lineno}")
            ic(e.__traceback__.tb_frame.f_locals)
            raise
    return messages


def _inject_prompt_caching(
    messages: list[BetaMessageParam],
):
    """
    Set cache breakpoints for the 3 most recent turns
    one cache breakpoint is left for tools/system prompt, to be shared across sessions
    """

    breakpoints_remaining = 2
    for message in reversed(messages):
        if message["role"] == "user" and isinstance(
            content := message["content"], list
        ):
            rr(breakpoints_remaining)
            if breakpoints_remaining:
                breakpoints_remaining -= 1
                content[-1]["cache_control"] = BetaCacheControlEphemeralParam(
                    {"type": "ephemeral"}
                )
            else:
                rr("removing cache control")
                content[-1].pop("cache_control", None)
                # we'll only every have one extra turn per loop
                break

def _maybe_filter_to_n_most_recent_images(
    messages: list[BetaMessageParam],
    images_to_keep: int,
    min_removal_threshold: int,
):
    """
    With the assumption that images are screenshots that are of diminishing value as
    the conversation progresses, remove all but the final `images_to_keep` tool_result
    images in place, with a chunk of min_removal_threshold to reduce the amount we
    break the implicit prompt cache.
    """
    if images_to_keep is None:
        return messages

    tool_result_blocks = cast(
        list[BetaToolResultBlockParam],
        [
            item
            for message in messages
            for item in (
                message["content"] if isinstance(message["content"], list) else []
            )
            if isinstance(item, dict) and item.get("type") == "tool_result"
        ],
    )

    total_images = sum(
        1
        for tool_result in tool_result_blocks
        for content in tool_result.get("content", [])
        if isinstance(content, dict) and content.get("type") == "image"
    )

    images_to_remove = total_images - images_to_keep
    # for better cache behavior, we want to remove in chunks
    images_to_remove -= images_to_remove % min_removal_threshold

    for tool_result in tool_result_blocks:
        if isinstance(tool_result.get("content"), list):
            new_content = []
            for content in tool_result.get("content", []):
                if isinstance(content, dict) and content.get("type") == "image":
                    if images_to_remove > 0:
                        images_to_remove -= 1
                        continue
                new_content.append(content)
            tool_result["content"] = new_content

async def run_sampling_loop(task: str) -> List[BetaMessageParam]:
    """Run the sampling loop with clean output handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    ic(messages)
    running = True
    if not api_key:
        ic()
        raise ValueError("API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    ic(messages.append({"role": "user","content": task}))
    messages = await sampling_loop(
                                model="claude-3-5-sonnet-20241022",
                                messages=messages,
                                api_key=api_key,
                            )

    return messages

async def main_async():
    """Async main function with proper error handling."""
    # task = input("Enter the task you want to perform: ")
    task = '''I need you to get an expert opinion on how to test, run,implement use cases and test the functionality for the code in the file C:/repo/code_test/code_context_manager.py . The commands you run will be from a different directory so please use absolute paths for EVERYTHING!'''
    try:
        
        messages = await run_sampling_loop(task)
        rr("\nTask Completed Successfully")
        rr("\nFinal Messages:")
        for msg in messages:
            rr(f"\n{msg['role'].upper()}:")
            # If content is a list of dicts (like tool_result), format accordingly
            if isinstance(msg['content'], list):
                for content_block in msg['content']:
                    if isinstance(content_block, dict):
                        if content_block.get("type") == "tool_result":
                            rr(f"Tool Result [ID: {content_block.get('name', 'unknown')}]:")
                            for item in content_block.get("content", []):
                                if item.get("type") == "text":
                                    rr(f"Text: {item.get('text')}")
                                elif item.get("type") == "image":
                                    rr(f"Image Source: base64 source too big")#{item.get('source', {}).get('data')}")
                        else:
                            for key, value in content_block.items():
                                rr(f"{key}: {value}")
                    else:
                        rr(content_block)
            else:
                rr(msg['content'])

    except Exception as e:
        rr(f"Error during execution: {e}")

def main():
    """Main entry point with proper async handling."""

    asyncio.run(main_async())

if __name__ == "__main__":
    main()
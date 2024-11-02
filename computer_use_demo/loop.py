"""
Agentic sampling loop that calls the Anthropic API and local implementation of anthropic-defined computer use tools.
"""
from http import client
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
from regex import R
from rich import print as rr
from icecream import install
from openai import OpenAI
# load the API key from the environment
import os
from dotenv import load_dotenv
load_dotenv()
install()
def write_to_file(s):
  with open('icecream_output.txt', 'a') as f:
    f.write(s + '\n')

ic.configureOutput(includeContext=True, outputFunction=rr)
ic()
ic.configureOutput(includeContext=True, outputFunction=write_to_file)


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

from tools import BashTool, ComputerTool, EditTool, ToolCollection, ToolResult, GetExpertOpinionTool

class OutputManager:
    """Manages and formats tool outputs and responses."""

    def __init__(self, image_dir: Optional[Path] = None ):
        # Set up image directory
        self.image_dir = image_dir or Path.home() / 'computer_tool_images'
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
                rr(result.output)
            
            if result.base64_image:
                image_path = self.save_image(result.base64_image)
                if image_path:
                    ic(f"Screenshot saved: {image_path}")
                else:
                    ic("Failed to save screenshot")

    def format_api_response(self, response: APIResponse) -> None:
        """Format and print API response."""
        ic(f"\nAPI Response ID: {getattr(response, 'id', 'unknown')}")
        # rr(f"API Response Status: {response.content[0].text}")
    def format_content_block(self, block: BetaContentBlock) -> None:
        """Format and print content block."""
        if getattr(block, 'type', None) == "tool_use":
            ic(f"\nTool Use: {block.name}")
            rr(f"Tool Use: {block.name}")
            # Only print non-image related inputs
            safe_input = {k: v for k, v in block.input.items()
                         if not isinstance(v, str) or len(v) < 1000}
            ic(f"Input: {safe_input}")
        elif hasattr(block, 'text'):
            ic(f"\nText: {block.text}")
            rr(f"[red]{block.text}[/red]")

def _make_api_tool_result(result: ToolResult, tool_use_id: str) -> dict:
    """Convert tool result to API format."""
    tool_result_content = []
    is_error = False

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

    return {
        "type": "tool_result",
        "content": tool_result_content,
        "tool_use_id": tool_use_id,
        "is_error": is_error,
    }



BETA_FLAG = "computer-use-2024-10-22"


system_prompt = """You are a eager, pro-active assistant with access to computer controls, web browsing and a programming environment where you can develop and execute code.
* You are utilizing a Windows machine with internet access.
* You should always use the Chrome Browser when searching the internet.
* You can install Windows applications using PowerShell. Use Invoke-WebRequest for downloading files.
* if you want to use pyautogui you can write a script to automate tasks on your computer. You can use it to control the mouse and keyboard to do things like clicking and typing and particularly useful would be keyboard shortcuts.
* If GUI app launching fails, you can use PowerShell's Start-Process command as a fallback.
- You can:
- Search the web and read web pages
- Create and edit documents.
- Install apps and packages.
- Write and execute scripts and Python code.
- use py.exe to execute python code.
- use uv pip install to install packages.
- Use VS Code to develop apps.
- Take screenshots to help you monitor your progress and judge if something completed correctly.
- Use the clipboard for efficient data transfer and fast data entry

use pyautogui to automate tasks on your computer. You can use it to control the mouse and keyboard to do things like clicking and typing and particularly useful would be keyboard shortcuts.
['\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
'8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
'browserback', 'browserfavorites', 'browserforward', 'browserhome',
'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
'command', 'option', 'optionleft', 'optionright']


If you need more info or assistance from a human helper you can:
If you need to pause the program until the user clicks OK on something, or want to display some information to the user, the message box functions have similar names that JavaScript has:

1. You can view the source of the web page to find information
2. you can also press Ctrl + U to view the source of the page
3. After each step, take a screenshot and carefully evaluate if you have achieved the right outcome. Explicitly show your thinking: "I have evaluated step X..." If not correct, try again. Only when you confirm a step was executed correctly should you move on to the next one
* When viewing a page it can be helpful to zoom out so that you can see everything on the page.  Either that, or make sure you scroll down to see everything before deciding something isn't available.
* When using your computer function calls, they take a while to run and send back to you.  Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document, determine the URL, download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
* If your clicking does not seem to be working, take another screen shot, make sure you are focused on the correct window and tab.
BEFORE YOU INTERACT IN A WINDOW, TAKE A SCREEN SHOT TO SEE WHAT WINDOW IS ACTIVE AND WHAT TAB YOU ARE ON.\
AFTER YOU FINISH AN INTERACTION, TAKE A SCREEN SHOT AND EVALUATE IF YOUR ACTION WAS SUCCESSFUL AND ANY TEXT IS WHERE IT SHOULD BE.
USE YOUR BEST METHOD TO SEE WHAT APPLICATIONS ARE AVAILABLE TO COMPLETE THE TASK AT HAND AND CHOOSE THE BEST METHOD AND APP TO COMPLETE THE TASK.
The current date is {datetime.today()}.
"""
async def sampling_loop(*, model: str, messages: List[BetaMessageParam], api_key: str, max_tokens: int = 8096,) -> List[BetaMessageParam]:

    tool_collection = ToolCollection(
                                        ComputerTool(),
                                        BashTool(),
                                        EditTool(),
                                        GetExpertOpinionTool(),
                                        # GoToURLReportsTool(),  # Add the GoToURLReportsTool instance
                                    )
                    
    output_manager = OutputManager(image_dir=Path('./logs/computer_tool_images')  )
    client = Anthropic(api_key=api_key)
    i=1
    running = True
    while running:
        print(f"Iteration {i}")
        i+=1
        try:
            ic(tool_collection.to_params())
            ic(f"Messages: {messages}")
            response = client.beta.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
                system=system_prompt,
                tools=tool_collection.to_params(),
                betas=[BETA_FLAG],
            )
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
            tool_result_content = []
            for content_block in response_params:
                ic(output_manager.format_content_block(content_block))
                if content_block["type"] == "tool_use":
                    # ic(f"Tool Use: {response_params}")
                    result = await tool_collection.run(
                        name=content_block["name"],
                        tool_input=content_block["input"],
                    )
                    ic.configureOutput(includeContext=True, outputFunction=rr,argToStringFunction=repr)
                    ic()
                    # ic.configureOutput(includeContext=True, outputFunction=write_to_file,argToStringFunction=repr)

                    output_manager.format_tool_output(result, content_block["id"])
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
        except Exception as e:
            ic(f"Error in sampling loop: {e}")
            ic(f"The error occurred at the following message: {messages[-1]} and line: {e.__traceback__.tb_lineno}")
            ic(e.__traceback__.tb_frame.f_globals)
            raise
    return messages

async def run_sampling_loop(task: str) -> List[BetaMessageParam]:
    """Run the sampling loop with clean output handling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    messages = []
    running = True
    if not api_key:
        raise ValueError("API key not found. Please set the ANTHROPIC_API_KEY environment variable.")
    messages.append({"role": "user","content": task})
    messages = await sampling_loop(
                                model="claude-3-5-sonnet-20241022",
                                messages=messages,
                                api_key=api_key,
                            )

    return messages

async def main_async():
    """Async main function with proper error handling."""
    # task = input("Enter the task you want to perform: ")
    # task = "Try to figure out the reports and run some until you can tell me who our biggest 3 customers are by sales volume."
    task = input("Enter the task you want to perform: ")
    # Read C:\mygit\compuse\mystery_game_project\docs\game_concept.md into a sting named task
    # with open(Xxxxxxxxxxxxxxxxxx', 'r') as file:
    #     task = file.read()


    # prompt = f"""
    # Objective:
    # You are a Task Decomposition Specialist. Your goal is to meticulously break down any given computer-based task into the smallest reasonable steps. Each step should be clear, actionable, and independently verifiable for completion by someone without prior knowledge of the task or access to the execution environment.
    # Instructions:
    # For each step (and sub-step, if necessary), provide the following:
    # Step [Number]:
    # Action: A detailed and specific description of the action to be performed.
    # Expected Result: A description of what should occur or be produced after the action is completed.
    # Verification Method: A precise method to confirm that the step has been completed, which should:
    # Be executable by someone who has not seen the previous steps.
    # Not require access to the environment where the task was performed.
    # Focus on confirming the completion of the action, not the accuracy of the result (unless completion inherently requires accuracy).
    # Guidelines:
    # Clarity and Specificity:
    # Use clear, unambiguous language.
    # Include specific details such as file names, URLs, commands, or search queries where applicable.
    # Step Structure:
    # Main Steps: Numbered sequentially (e.g., Step 1, Step 2, Step 3).
    # Sub-Steps: If a step requires multiple actions, break it down into sub-steps (e.g., Sub-Step 1.1, Sub-Step 1.2).
    # Formatting Requirements:
    # Use bold headings for Action, Expected Result, and Verification Method for clarity.
    # Present information in a structured and organized manner.
    # Independent Verification:
    # Ensure each verification method can be performed independently of other steps.
    # Verification should rely only on the outputs or artifacts produced by that specific step.
    # Verification Methods:
    # Should be objective, measurable, and specific.
    # May include:
    # Checking the existence or properties of a file or document.
    # Viewing metadata, timestamps, or file contents.
    # Confirming the presence of specific data, entries, or outputs.
    # Reviewing screenshots or exported logs.
    # No Assumptions:
    # Do not assume the verifier has any prior knowledge of the task or access to previous results.
    # Do not require the verifier to access the execution environment or external systems beyond what is produced in the step.
    # Example Format:
    # Step 1:
    # Action: Create a new folder named Elevator_Project on your desktop.
    # Expected Result: A folder named Elevator_Project exists on the desktop.
    # Verification Method: Check the desktop for the presence of the Elevator_Project folder.
    # Sub-Step 1.1:
    # Action: Inside the Elevator_Project folder, create an Excel file named elevator_data.xlsx with two sheets labeled Company_Info and Models.
    # Expected Result: An Excel file elevator_data.xlsx with two sheets named Company_Info and Models exists in the Elevator_Project folder.
    # Verification Method: Open elevator_data.xlsx and confirm the sheets Company_Info and Models are present.
    # Sub-Step 1.2:
    # Action: In the Company_Info sheet, add column headers in the first row: Manufacturer, Public/Private, Number of Employees, Years in Business.
    # Expected Result: The Company_Info sheet has the specified headers correctly labeled in the first row.
    # Verification Method: Open the Company_Info sheet and verify the headers are present and correctly labeled.
    # Your Task:
    # {task}
    # Apply the above guidelines and format to break down the provided task:
    # Instructions for Completion:
    # Identify Main Steps:
    # Start by outlining the major components required to complete the task.
    # Decompose into Sub-Steps:
    # Break down each main step into smaller, actionable sub-steps as necessary.
    # Detail Each Step:
    # For every step and sub-step, provide the Action, Expected Result, and Verification Method as per the guidelines.
    # Ensure Independent Verification:
    # Make sure that each verification method allows someone to confirm completion without prior knowledge or access to the execution environment.
    # Maintain Clarity and Organization:
    # Use the specified formatting for consistency and ease of understanding.
    # Begin your detailed task breakdown below:"""
    # client = OpenAI()
    # response = client.chat.completions.create(
    #     model="o1-mini",
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "text",
    #                     "text": prompt
    #                 },
    #             ],
    #         }
    #     ]
    # )
    # task = response.choices[0].message.content
    # rr(task)
    try:
        # task = "develop, implmennt and test the game described in C:\repo\game_concept.md"
        
        messages = await run_sampling_loop(task)
        print("\nTask Completed Successfully")
        print("\nFinal Messages:")
        for msg in messages:
            print(f"\n{msg['role'].upper()}:")
            # If content is a list of dicts (like tool_result), format accordingly
            if isinstance(msg['content'], list):
                for content_block in msg['content']:
                    if isinstance(content_block, dict):
                        if content_block.get("type") == "tool_result":
                            print(f"Tool Result [ID: {content_block.get('tool_use_id', 'unknown')}]:")
                            for item in content_block.get("content", []):
                                if item.get("type") == "text":
                                    print(f"Text: {item.get('text')}")
                                elif item.get("type") == "image":
                                    print(f"Image Source: base64 source too big")#{item.get('source', {}).get('data')}")
                        else:
                            print(content_block)
                    else:
                        print(content_block)
            else:
                print(msg['content'])

    except Exception as e:
        print(f"Error during execution: {e}")

def main():
    """Main entry point with proper async handling."""

    asyncio.run(main_async())

if __name__ == "__main__":
    main()
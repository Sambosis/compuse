import asyncio
import pyautogui
import pyperclip
import time
import base64
from pathlib import Path
from anthropic import Anthropic
from tools.computer import ComputerTool
from tools.base import ToolResult
import os 
api_key = os.getenv("ANTHROPIC_API_KEY")
# Initialize Anthropic client (replace with your actual API key)
anthropic = Anthropic(api_key=api_key)
async def ask_model(prompt, image=None):
    messages = [{"role": "user", "content": prompt}]
    if image:
        messages[0]["content"] = [
            {"type": "text", "text": prompt},
            {"type": "image", "image": image}
        ]
    
    response = anthropic.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=messages
    )
    return response.content[0].text

async def take_screenshot():
    computer_tool = ComputerTool()
    result = await computer_tool(action="screenshot")
    if isinstance(result, ToolResult) and result.base64_image:
        return result.base64_image
    return None

async def web_scrape_to_word():
    computer_tool = ComputerTool()

    # Open Chrome
    await computer_tool(action="key", text="win")
    time.sleep(1)
    await computer_tool(action="type", text="Chrome")
    await computer_tool(action="key", text="enter")
    time.sleep(5)  # Wait for Chrome to open

    # Verify Chrome is open
    screenshot = await take_screenshot()
    response = await ask_model("Is Chrome open in this screenshot?", screenshot)
    if "yes" not in response.lower():
        print("Chrome didn't open properly. Stopping.")
        return

    # Focus on address bar
    await computer_tool(action="key", text=["ctrl", "l"])
    time.sleep(1)

    # Paste the URL using clipboard
    url = "https://www.autochlor.net/wps"
    original_clipboard = pyperclip.paste()  # Save original clipboard content
    pyperclip.copy(url)  # Copy URL to clipboard
    await computer_tool(action="key", text=["ctrl", "v"])  # Paste URL
    await computer_tool(action="key", text="enter")
    pyperclip.copy(original_clipboard)  # Restore original clipboard content
    time.sleep(10)  # Wait for page to load

    # Verify page loaded
    screenshot = await take_screenshot()
    response = await ask_model(f"Has the webpage {url} loaded successfully?", screenshot)
    if "yes" not in response.lower():
        print("Webpage didn't load properly. Stopping.")
        return

    print("Web content has been successfully copied to Word document.")

# Run the script
asyncio.run(web_scrape_to_word())
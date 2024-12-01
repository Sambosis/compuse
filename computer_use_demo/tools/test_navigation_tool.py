# windows_navigation_tool.py
# windows_navigation_tool.py

from numpy import short
import pyautogui
import time
from typing import Optional
from rich import print as rr
# Define available shortcuts
# shortcuts = {
#     "switch_window": {"keys": ["alt", "tab"]},
#     "open_start_menu": {"keys": ["win"]},
#     "minimize_window": {"keys": ["win", "down"]},
#     "maximize_window": {"keys": ["win", "up"]},
#     "close_window": {"keys": ["alt", "f4"]},
#     "take_screenshot": {"keys": ["win", "printscreen"]},
#     # Add more shortcuts as needed
# }
shortcuts = {
    "switch_window": {
        "keys": ["alt", "tab"]
                    },
    "open_start_menu": {
        "keys": ["win"]
                    },
    "minimize_window": {
        "keys": ["win", "down"]
                    },
    "maximize_window": {
        "keys": ["win", "up"]
                    },
    "restore_window": {
        "keys": ["win", "down"]
                    },
    "close_window": {
        "keys": ["alt", "f4"]
                    },
    "take_screenshot": {
        "keys": ["win", "prtsc"]
                    },
    "go_to_desktop": {
        "keys": ["win", "d"]
                    },
    "switch_virtual_desktop_left": {
        "keys": ["win", "ctrl", "left"]
                    },
    "switch_virtual_desktop_right": {
        "keys": ["win", "ctrl", "right"]
                    },
    "open_file_explorer": {
        "keys": ["win", "e"]
                    },
    "refresh_explorer": {
        "keys": ["f5"]
                    },
    "open_task_manager": {
        "keys": ["ctrl", "shift", "esc"]
                    },
    "lock_workstation": {
        "keys": ["win", "l"]
                    },
    "sign_out": {
        "keys": ["ctrl", "alt", "del"]
                    },
    "hibernate": {
        "keys": ["win", "x", "u", "h"]
                    },
    "sleep": {
        "keys": ["win", "x", "u", "s"]
                    },
    "copy": {
        "keys": ["ctrl", "c"]
                    },
    "paste": {
        "keys": ["ctrl", "v"]
                    },
    "cut": {
        "keys": ["ctrl", "x"]
                    },
    "select_all": {
        "keys": ["ctrl", "a"]
                    },
    "open_run_dialog": {
        "keys": ["win", "r"]
                    },
    "open_settings": {
        "keys": ["win", "i"]
                    },
    "open_search": {
        "keys": ["win", "s"]
                    },
    "toggle_high_contrast": {
        "keys": ["left_alt", "left_shift", "printscreen"]
                    },
    "toggle_narrator": {
        "keys": ["left_win", "ctrl", "enter"]
                    },
    "toggle_magnifier": {
        "keys": ["left_win", "plus"]
                    }

}

def windows_navigate(action: str, modifier: Optional[str] = None, target: Optional[str] = None) -> str:
    """
    Execute the requested Windows action.

    Args:
        action (str): The action to perform.
        modifier (Optional[str]): Optional modifier key(s).
        target (Optional[str]): Optional target for the action.

    Returns:
        str: Result message.
    """
    try:
        shortcut = shortcuts.get(action)
        if not shortcut:
            return f"Unknown action: {action}"

        keys = shortcut["keys"]
        if modifier:
            keys = [modifier] + keys

        # Activate target window if specified
        if target:
            windows = pyautogui.getWindowsWithTitle(target)
            if windows:
                windows[0].activate()
                time.sleep(0.5)
            else:
                return f"No window found with title '{target}'"

        # Execute the key combination
        pyautogui.hotkey(*keys)
        time.sleep(0.1)

        return f"Successfully executed '{action}'"
    except Exception as e:
        return f"Failed to execute '{action}': {str(e)}"

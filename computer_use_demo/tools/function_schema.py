from test_navigation_tool import shortcuts

windows_navigate_function = {
    "name": "windows_navigate",
    "description": "A tool for Windows navigation using keyboard shortcuts.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": list(shortcuts.keys()),
                "description": "The Windows action to perform."
            },
            "modifier": {
                "type": ["string", "null"],
                "enum": ["ctrl", "alt", "shift", "win"],
                "description": "Optional modifier key."
            },
            "target": {
                "type": ["string", "null"],
                "description": "Optional target for the action (e.g., window title)."
            }
        },
        "required": ["action"],
    },
}

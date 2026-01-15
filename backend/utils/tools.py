"""
Tools that can be passed to the Backboard assistant
"""
from datetime import datetime
from typing import Dict, Any


def get_current_date() -> Dict[str, Any]:
    """
    Get the current date in YYYY-MM-DD format.
    
    Returns:
        dict: Tool definition for Backboard assistant
    """
    return {
        "type": "function",
        "function": {
            "name": "get_current_date",
            "description": "Get the current date in YYYY-MM-DD format. Use this to ensure accurate date calculations and timeline planning.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }


def execute_get_current_date() -> str:
    """
    Execute the get_current_date tool.
    
    Returns:
        str: Current date in YYYY-MM-DD format
    """
    return datetime.now().strftime("%Y-%m-%d")


# Tool registry for easy access
AVAILABLE_TOOLS = [
    get_current_date()
]

# Execution handlers mapping
TOOL_HANDLERS = {
    "get_current_date": execute_get_current_date
}

import os


CLIENT_VERSION = "0.2"

FRIENDLY_COLOR = "deep_sky_blue1"

REQUIRED_SETUP_KEYS = ["EULA",
                       "NICKNAME",
                       "CRASH_INFO_LEVEL",
                       "PROVIDE_FEEDBACK",
                       "AGENTAI_API_KEY"]

def parse_display_number(display_str=None):
    """
    Parse X11 DISPLAY environment variable to extract the display number.
    Returns None if not running in X11 environment.

    Must be here, since placing it in parsing.py causes a circular import
    
    Args:
        display_str (str, optional): The DISPLAY environment variable string.
            If None, reads from environment.
        
    Returns:
        int or None: The display number, or None if not in X11 environment
    """
    # If no display string provided, try to get from environment
    if display_str is None:
        display_str = os.environ.get('DISPLAY')
    
    # Return None if no display string found
    if not display_str:
        return None
        
    try:
        # Remove hostname part if present (everything before last :)
        display_part = display_str.split(":")[-1]
        
        # Get first component before any dot
        display_number = display_part.split(".")[0]
        
        return int(display_number)
    except (ValueError, IndexError):
        return None

COMPUTER_TOOLS = [
    # {
    #     "type": "computer_20241022",
    #     "name": "computer",
    #     "display_width_px": 1024,
    #     "display_height_px": 768,
    #     "display_number": parse_display_number(os.environ.get("DISPLAY"))
    # },
    # {
    #     "type": "text_editor_20241022",
    #     "name": "str_replace_editor"
    # },
    {
        "type": "bash_20241022",
        "name": "bash"
    },
    {
        "name": "python",
        "description": "Execute Python code and return the result",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "ui",
        "description": "Send a message to the UI agent and wait for response",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to send to the UI agent"
                }
            },
            "required": ["message"]
        }
    }
]

def get_env_constants():
    LOCAL_LOGS = os.environ.get("LOCAL_LOGS").lower() == "true"
    USE_ANTHROPIC = os.environ.get("USE_ANTHROPIC").lower() == "true"
    DEBUG = os.environ.get("DEBUG").lower() == "true"

    return {
        "LOCAL_LOGS": LOCAL_LOGS,
        "USE_ANTHROPIC": USE_ANTHROPIC,
        "DEBUG": DEBUG
    }
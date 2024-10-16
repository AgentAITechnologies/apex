import os
import dotenv


CLIENT_VERSION = "0.1"

FRIENDLY_COLOR = "deep_sky_blue1"

REQUIRED_SETUP_KEYS = ["EULA",
                       "NICKNAME",
                       "CRASH_INFO_LEVEL",
                       "PROVIDE_FEEDBACK",
                       "AGENTAI_API_KEY"]

LOCAL_LOGS = None

USE_ANTHROPIC = None


def on_load_dotenv():
    LOCAL_LOGS = os.environ.get("LOCAL_LOGS").lower() == "true"
    
    USE_ANTHROPIC = os.environ.get("USE_ANTHROPIC").lower() == "true"
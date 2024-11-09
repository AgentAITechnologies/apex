import os


CLIENT_VERSION = "0.1"

FRIENDLY_COLOR = "deep_sky_blue1"

REQUIRED_SETUP_KEYS = ["EULA",
                       "CRASH_INFO_LEVEL",
                       "PROVIDE_FEEDBACK",
                       "AGENTAI_API_KEY"]

def get_env_constants():
    LOCAL_LOGS = os.environ.get("LOCAL_LOGS").lower() == "true"
    USE_ANTHROPIC = os.environ.get("USE_ANTHROPIC").lower() == "true"
    DEBUG = os.environ.get("DEBUG").lower() == "true"

    return {
        "LOCAL_LOGS": LOCAL_LOGS,
        "USE_ANTHROPIC": USE_ANTHROPIC,
        "DEBUG": DEBUG
    }
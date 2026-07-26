import os


CLIENT_VERSION = "0.1"

FRIENDLY_COLOR = "deep_sky_blue1"

REQUIRED_SETUP_KEYS = ["EULA",
                       "CRASH_INFO_LEVEL",
                       "PROVIDE_FEEDBACK",
                       "AGENTAI_API_KEY"]

def get_env_constants():
    LOCAL_LOGS = os.environ.get("LOCAL_LOGS", "False").lower() == "true"
    USE_ANTHROPIC = os.environ.get("USE_ANTHROPIC", "False").lower() == "true"
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    USE_EXPERIENCES = os.environ.get("USE_EXPERIENCES", "True").lower() == "true"

    return {
        "LOCAL_LOGS": LOCAL_LOGS,
        "USE_ANTHROPIC": USE_ANTHROPIC,
        "DEBUG": DEBUG,
        "USE_EXPERIENCES": USE_EXPERIENCES
    }
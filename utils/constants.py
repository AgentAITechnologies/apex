import os
import dotenv

dotenv.load_dotenv()


CLIENT_VERSION = "0.1"

FRIENDLY_COLOR = "deep_sky_blue1"

REQUIRED_SETUP_KEYS = ["EULA",
                       "NICKNAME",
                       "CRASH_INFO_LEVEL",
                       "PROVIDE_FEEDBACK",
                       "AGENTAI_API_KEY"]

LOCAL_LOGS = os.environ.get("LOCAL_LOGS") == "True"
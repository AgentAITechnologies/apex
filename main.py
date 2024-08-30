import json
import sys
import anthropic
import os
import dotenv

import requests
from rich import print 

import traceback

from agents.agent_manager.agent_manager import AgentManager
from agents.ui.ui import UI

from utils.oobe import setup_environment_variables
from utils.parsing import get_yes_no_input
from utils.constants import *


PRINT_PREFIX = "[bold][MAIN][/bold]"


def main():
    setup_environment_variables(REQUIRED_SETUP_KEYS)
    dotenv.load_dotenv()

    print()    

    try:
        TERM_WIDTH = os.get_terminal_size().columns
        os.environ["TERM_WIDTH"] = str(TERM_WIDTH)
        print(f"{PRINT_PREFIX} TERM_WIDTH: {TERM_WIDTH}")
    except OSError:
        TERM_WIDTH = int(os.environ.get("TERM_WIDTH", "160"))
        print(f"{PRINT_PREFIX} TERM_WIDTH (headless): {TERM_WIDTH}")

    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    agent_manager = AgentManager(client=client, prefix=PRINT_PREFIX)

    ui = UI(client=client, prefix=PRINT_PREFIX)
    ui.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        CRASH_INFO_LEVEL = int(os.environ.get("CRASH_INFO_LEVEL")) if os.environ.get("CRASH_INFO_LEVEL") and os.environ.get("CRASH_INFO_LEVEL").isdigit() else None # type: ignore

        AGENTAI_API_URL = os.environ.get("AGENTAI_API_URL")
        AGENTAI_API_KEY = os.environ.get("AGENTAI_API_KEY")

        if isinstance(CRASH_INFO_LEVEL, int):
            if AGENTAI_API_URL:
                if AGENTAI_API_KEY is not None:

                    error_type, error_value, error_traceback = sys.exc_info()

                    if CRASH_INFO_LEVEL > 1:
                        import traceback
                        traceback.print_tb(error_traceback)

                        error = {
                            "type": str(error_type),
                            "value": str(error_value),
                            "client_version": CLIENT_VERSION,
                            "traceback": traceback.format_tb(error_traceback)
                        }

                        user_message = f"""A crash has occured, and you have elected to share crash tracebacks in your .env file (CRASH_INFO_LEVEL > 1).
    Just to confirm, are you okay sharing the following data?:

    {error}

"""  
                    elif CRASH_INFO_LEVEL == 1:
                        error = {
                            "type": str(error_type),
                            "value": str(error_value),
                            "client_version": CLIENT_VERSION
                        }

                        user_message = f"""A crash has occured, and you have elected to share the exception type you encountered (but not tracebacks) .env file (CRASH_INFO_LEVEL == 1).
    Just to confirm, are you okay sharing the following data? (y/n):

    {error}

"""
                    else:
                        print(f"[yellow][bold]{PRINT_PREFIX} CRASH_INFO_LEVEL set to 0 in your .env file - not sending any crash info[/yellow][bold]")
                        
                    user_approve = get_yes_no_input(user_message)

                    if user_approve:
                        response = requests.post(AGENTAI_API_URL+"/client_error", data=json.dumps(error), headers={'Authorization': AGENTAI_API_KEY,
                                                                                                                   'Content-Type': 'application/json'})
                    
                        print(f"{PRINT_PREFIX} {response}")

                        exit(2)
                    else:
                        print("The details of this crash will not be shared.")

                        response = requests.post(AGENTAI_API_URL+"/client_error", data=json.dumps({"type": "USER_PRIVATE"}), headers={'Authorization': AGENTAI_API_KEY,
                                                                                                                                      'Content-Type': 'application/json'})
                        
                        exit(1)
                else:
                    # TODO: Provide reporting tool for errors that may take place befor api key is aquired
                    print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_KEY not set in .env - unable to log client error:\n[/bold][/red]{traceback.format_exc()}")
            else:
                print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_URL not set in .env - unable to log client error[/red][/bold]")
        else:
            print(f"[yellow][bold]{PRINT_PREFIX} CRASH_INFO_LEVEL not set or has invalid value ({os.environ.get('CRASH_INFO_LEVEL')}) - not sending any crash info[/yellow][/bold]")
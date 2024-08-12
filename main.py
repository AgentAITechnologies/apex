import json
import sys
import anthropic
import os
import dotenv

import requests
from rich import print 

from agents.agent_manager.agent_manager import AgentManager
from agents.ui.ui import UI


dotenv.load_dotenv()

FRIENDLY_COLOR = "green"
PRINT_PREFIX = "[bold][MAIN][/bold]"


def main():
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

    print(3/0)

    ui = UI(client=client, prefix=PRINT_PREFIX)
    ui.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        PROVIDE_CRASH_INFO = str(os.environ.get("PROVIDE_CRASH_INFO")).lower() == "true"

        AGENTAI_API_URL = os.environ.get("AGENTAI_API_URL")
        AGENTAI_API_KEY = os.environ.get("AGENTAI_API_KEY")

        if PROVIDE_CRASH_INFO:
            print(f"{PRINT_PREFIX} PROVIDE_CRASH_INFO set to \"True\" - sending crash info")

            if AGENTAI_API_URL:
                if AGENTAI_API_KEY is not None:
                    error_type, error_value, error_traceback = sys.exc_info()

                    import traceback
                    traceback.print_tb(error_traceback)

                    error = {
                        "type": str(error_type),
                        "value": str(error_value),
                        "traceback": traceback.format_tb(error_traceback)
                    }

                    response = requests.post(AGENTAI_API_URL+"/client_error", data=json.dumps(error), headers={'Authorization': AGENTAI_API_KEY,
                                                                                                               'Content-Type': 'application/json'})
                    
                    print(f"{PRINT_PREFIX} {response}")

                    exit(1)
                else:
                    # TODO: Provide reporting tool for errors that may take place befor api key is aquired
                    print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_KEY not set in .env - unable to log client error[/bold][/red]")
            else:
                print(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_URL not set in .env - unable to log client error[/red][/bold]")
        else:
            print(f"[yellow][bold]{PRINT_PREFIX} PROVIDE_CRASH_INFO not set to \"True\" - not sending crash info[/yellow][bold]")
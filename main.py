PRINT_PREFIX = "[bold][MAIN][/bold]"

import json
import sys
import os
import dotenv
import httpx
from openai import OpenAI

import requests
from rich import print as rprint

import traceback

from utils.console_io import debug_print as dprint
from utils.oobe import setup_environment_variables, template2env

template2env()

# Test the debugger:
# dprint(f"{PRINT_PREFIX} dotenv.load_dotenv(override=True): {dotenv.load_dotenv(override=True)}", force_debug_mode=True)

from utils.parsing import get_yes_no_input
from utils.constants import *

from agents.agent_manager.agent_manager import AgentManager
from agents.ui.ui import UI


def main():
    setup_environment_variables(REQUIRED_SETUP_KEYS)
    
    dotenv.load_dotenv()

    rprint()    

    try:
        TERM_WIDTH = os.get_terminal_size().columns
        os.environ["TERM_WIDTH"] = str(TERM_WIDTH)
        dprint(f"{PRINT_PREFIX} TERM_WIDTH: {TERM_WIDTH}")
    except OSError:
        TERM_WIDTH = int(os.environ.get("TERM_WIDTH", "160"))
        dprint(f"{PRINT_PREFIX} TERM_WIDTH (headless): {TERM_WIDTH}")

    # Custom HTTP client configured to trust your shared DGX Spark CA certificate
    ca_cert_path = os.environ.get("CUSTOM_SSL_CERT")
    
    http_client = httpx.Client(
        verify=ca_cert_path if ca_cert_path and os.path.exists(ca_cert_path) else True
    )

    client = OpenAI(
        base_url="https://192.168.1.214:8000/v1",
        api_key=os.environ.get("OPENAI_API_KEY", "no-key"),
        http_client=http_client,
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
                        rprint(f"[yellow][bold]{PRINT_PREFIX} CRASH_INFO_LEVEL set to 0 in your .env file - not sending any crash info[/yellow][/bold]")
                        sys.exit(1)
                        
                    user_approve = get_yes_no_input(user_message)

                    if user_approve:
                        try:
                            response = requests.post(
                                AGENTAI_API_URL + "/client_error",
                                data=json.dumps(error),
                                headers={
                                    'Authorization': AGENTAI_API_KEY,
                                    'Content-Type': 'application/json'
                                },
                                timeout=5
                            )
                            dprint(f"{PRINT_PREFIX} {response}")
                        except Exception as req_err:
                            rprint(f"[yellow]{PRINT_PREFIX} Unable to send crash telemetry: {req_err}[/yellow]")

                        exit(2)
                    else:
                        rprint("The details of this crash will not be shared.")

                        try:
                            response = requests.post(
                                AGENTAI_API_URL + "/client_error",
                                data=json.dumps({"type": "USER_PRIVATE"}),
                                headers={
                                    'Authorization': AGENTAI_API_KEY,
                                    'Content-Type': 'application/json'
                                },
                                timeout=5
                            )
                        except Exception as req_err:
                            dprint(f"{PRINT_PREFIX} Unable to send telemetry: {req_err}")

                        exit(1)
                else:
                    # TODO: Provide reporting tool for errors that may take place befor api key is aquired
                    rprint(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_KEY not set in .env - unable to log client error:\n[/bold][/red]{traceback.format_exc()}")
            else:
                rprint(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_URL not set in .env - unable to log client error[/red][/bold]")
        else:
            rprint(f"[yellow][bold]{PRINT_PREFIX} CRASH_INFO_LEVEL not set or has invalid value ({os.environ.get('CRASH_INFO_LEVEL')}) - not sending any crash info[/yellow][/bold]")
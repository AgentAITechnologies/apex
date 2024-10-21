import json
import os
import shutil
from dotenv import load_dotenv, set_key

from playwright.sync_api import sync_playwright

from rich import print as rprint
from utils.console_io import debug_print as dprint

from utils.custom_exceptions import APIKeyError, AuthError
from utils.parsing import get_yes_no_input
from utils.constants import get_env_constants


PRINT_PREFIX = "[bold][OOBE][/bold]"

AUTH_TIMEOUT_MS = 90000 * 2


def get_token():
    load_dotenv()
    
    PROVIDE_FEEDBACK = os.environ.get("PROVIDE_FEEDBACK") == "True"
    CRASH_INFO_LEVEL = int(os.environ.get("CRASH_INFO_LEVEL")) if os.environ.get("CRASH_INFO_LEVEL") and os.environ.get("CRASH_INFO_LEVEL").isdigit() else None
    AGENTAI_API_URL = os.environ.get("AGENTAI_API_URL")
    
    needs_api_access = PROVIDE_FEEDBACK or (isinstance(CRASH_INFO_LEVEL, int) and CRASH_INFO_LEVEL > 0)

    if not AGENTAI_API_URL and needs_api_access:
        rprint(f"[red][bold]{PRINT_PREFIX} AGENTAI_API_URL not set but needed due to CRASH_INFO_LEVEL > 0 or PROVIDE_FEEDBACK != True[/bold][/red]")

        raise Exception(f"{PRINT_PREFIX} AGENTAI_API_URL not set but needed due to CRASH_INFO_LEVEL > 0 or PROVIDE_FEEDBACK != True")
    else:
        AUTH_URL = f"{AGENTAI_API_URL}/register"
        REDIRECT_URL = f"{AGENTAI_API_URL}/callback"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            dprint("Opening Discord authorization page...")
            page.goto(AUTH_URL)
            
            dprint("Waiting for authorization and redirect...")
            with page.expect_response(lambda response: REDIRECT_URL in response.url, timeout=AUTH_TIMEOUT_MS) as response_info:
                response = response_info.value
            
            content = response.text()
            browser.close()
            
            try:
                json_data = json.loads(content)
                api_token = json_data.get('api_token')
                if api_token:
                    dprint("Successfully retrieved API token.")
                    return api_token
                else:
                    error_message = "[red][bold]Failed to parse JSON response from API."
                    rprint(f"[red][bold]{PRINT_PREFIX} {error_message}[/bold][/red]")
                    raise AuthError(error_message)
            except json.JSONDecodeError as e:
                error_message = "Failed to parse JSON response from API."
                rprint(f"[red][bold]{PRINT_PREFIX} {error_message}[/bold][/red]")
                raise json.JSONDecodeError(msg=error_message, doc=e.doc, pos=e.pos)
            
def eula_decline():
    rprint("[yellow][bold]Please accept the End User License Agreement to launch the tool[/bold][/yellow]")
    exit(0)

def template2env(template_file=None, env_file=None):
    if template_file is None:
        template_file = os.path.join('.', '.env.template')
    if env_file is None:
        env_file = os.path.join('.', '.env')

    if os.path.exists(template_file) and not os.path.exists(env_file):
        try:
            with open(template_file, 'r') as source, open(env_file, 'w') as destination:
                destination.write(source.read())
            dprint(f"{PRINT_PREFIX} Copied {template_file} to {env_file}", force_debug_mode=False)
        except IOError as e:
            rprint(f"[red][bold]{PRINT_PREFIX} Error copying file: {e}[/red][/bold]")
    elif os.path.exists(env_file):
        dprint(f"{PRINT_PREFIX} {env_file} already exists. No action taken.", force_debug_mode=False)
    else:
        dprint(f"[yellow][bold]{PRINT_PREFIX} {template_file} not found. No action taken.[/yellow][/bold]", force_debug_mode=False)

def setup_environment_variables(required_keys, env_file='.env'):
    load_dotenv()

    USE_ANTHROPIC = get_env_constants()['USE_ANTHROPIC']

    if USE_ANTHROPIC:
        if os.getenv('ANTHROPIC_API_KEY') == "YOUR_API_KEY_HERE":
            rprint(f"[yellow]{PRINT_PREFIX} Your Anthropic API key is not set.[/yellow]")
            rprint(f"[yellow]{PRINT_PREFIX} Please enter your Anthropic API key:[/yellow]")
            new_api_key = input().strip()
            
            set_key(env_file, 'ANTHROPIC_API_KEY', new_api_key)
            
            rprint(f"[green]{PRINT_PREFIX} API key has been updated in the .env file.[/green]")
            
            load_dotenv(override=True)
        else:
            dprint(f"{PRINT_PREFIX} Anthropic API key is already set.")

    if not os.path.exists(env_file):
        rprint(f"[red][bold]{PRINT_PREFIX} Cound't find env file '{env_file}'![/bold][red]")
        raise FileNotFoundError(f"{PRINT_PREFIX} Cound't find .env!")
    else:
        for key in required_keys:
            if not os.getenv(key) or (key == "EULA" and os.environ.get(key) != "True"):
                match key:
                    case "EULA":
                        value = get_yes_no_input(prompt="EULA", rich_open="[bold]", rich_close="[/bold]")

                        if not value:
                            eula_decline()

                        value = str(value)

                    case "NICKNAME":
                        rprint("[italic]How should I refer to you? > [/italic]", end='')
                        value = input().strip()

                    case "PROVIDE_FEEDBACK":
                        rprint("""
[deep_sky_blue1][bold]Your feedback on the performance of this virtual assistant is instrumental in advancing its capabilities for all of its users.[/bold]
By sharing your insights, you're directly shaping the future of open conversational AI technology.[/deep_sky_blue1]
                              
Would you like to share performance feedback?
[italic]You will have the opportunity to review any and all information before it is shared[/italic]""")
                        
                        value = str(get_yes_no_input())

                    case "CRASH_INFO_LEVEL":
                        rprint("""
[deep_sky_blue1][bold]Crash telemetry is criticial to the development of a seamless user experience.[/bold][/deep_sky_blue1]
                              
Please select your level of crash telemetry:
0. No telemetry
1. Exception type info only
2. Exception type and traceback
                              
[italic]You will have the opportunity to review any and all information before it is shared[/italic]

 > """, end='')
                        while value not in [str(i) for i in range(3)]:
                            value = input().strip()

                    case "AGENTAI_API_KEY":
                        value = get_token()
                        if not value:
                            error_message = "Failed to obtain AgentAI API key"
                            rprint(f"[red][bold]{PRINT_PREFIX} {error_message}[/bold][/red]")
                            raise APIKeyError(error_message)
                        
                    case _:
                        error_message = "Unhandled OOBE environment variable setting requirement in REQUIRED_SETUP_KEYS"
                        rprint(f"[red][bold]{PRINT_PREFIX} {error_message}[/bold][/red]")
                        raise ValueError(error_message)
                
                set_key(env_file, key, value)
                os.environ[key] = value

                dprint(f"{PRINT_PREFIX} Set {key} = \"{value}\" in {env_file}")

        dprint(f"{PRINT_PREFIX} Environment variables have been set up successfully.")
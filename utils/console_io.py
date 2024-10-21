from rich import print as rprint

from utils.constants import get_env_constants

def debug_print(debug_message, debug_override=False):
    if get_env_constants()["DEBUG"] or debug_override:
        rprint(debug_message)
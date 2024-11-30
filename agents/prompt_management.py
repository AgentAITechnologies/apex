import os
from typing import Optional
import dotenv

from rich import print

from utils.enums import Role
from utils.custom_types import Message
from utils.stt import STT


dotenv.load_dotenv()


PRINT_PREFIX = "[bold][PROMPT_MGMT][/bold]"
FILE_EXT = ".xml"


def load_user_prompt(state_path: str, environ_path_key: str, dynamic_metaprompt: Optional[str], frmt: dict[str, str]) -> str:
    if dynamic_metaprompt:
        use_stt = os.environ.get("USE_STT") == "True"

        if not use_stt:
            print(dynamic_metaprompt, end="")
            user_input = input()

            return "<input>" + user_input + "</input>"

        else:
            stt = STT()

            print(dynamic_metaprompt, end="")
            user_input = stt.transcribe_speech()

            print(user_input)

            return "<input>" + user_input + "</input>"

    else:
        environ_path = os.environ.get(environ_path_key)
        if not environ_path:
            error_message = f"{PRINT_PREFIX} {environ_path_key} not set"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)
        INPUT_DIR = os.environ.get("INPUT_DIR")
        if not INPUT_DIR:
            error_message = f"{PRINT_PREFIX} INPUT_DIR not set"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)
        USR_PRMPT_DIR = os.environ.get("USR_PRMPT_DIR")
        if not USR_PRMPT_DIR:
            error_message = f"{PRINT_PREFIX} USR_PRMPT_DIR not set"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)
            
        user_prompt_dir = os.path.join(environ_path, INPUT_DIR, USR_PRMPT_DIR)
        
        if not os.path.exists(os.path.join(user_prompt_dir, state_path+FILE_EXT)):
            error_message = f"{PRINT_PREFIX} user prompt file does not exist, and no prompt was provided as arg: {state_path+FILE_EXT}"
            print(f"[red][bold]{error_message}[/red][/bold]")
            raise FileNotFoundError(error_message)

        else:
            with open(os.path.join(user_prompt_dir, state_path+FILE_EXT), 'r', encoding="utf-8", errors='replace') as f:
                user_prompt = f.read()

            if frmt:
                user_prompt = user_prompt.format(**frmt)
                    
            return user_prompt

def load_system_prompt(state_path: str, environ_path_key: str, frmt: dict[str, str]) -> str:
    environ_path = os.environ.get(environ_path_key)
    if not environ_path:
        error_message = f"{PRINT_PREFIX} {environ_path_key} not set"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)

    INPUT_DIR = os.environ.get("INPUT_DIR")
    if not INPUT_DIR:
        error_message = f"{PRINT_PREFIX} INPUT_DIR not set"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)

    SYS_PRMPT_DIR = os.environ.get("SYS_PRMPT_DIR")
    if not SYS_PRMPT_DIR:
        error_message = f"{PRINT_PREFIX} SYS_PRMPT_DIR not set"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)

    sys_prompt_dir = os.path.join(environ_path, INPUT_DIR, SYS_PRMPT_DIR)

    with open(os.path.join(sys_prompt_dir, state_path+FILE_EXT), 'r', encoding="utf-8", errors='replace') as f:
        sys_prompt = f.read()

    if frmt:
        sys_prompt = sys_prompt.format(**frmt)

    return sys_prompt

def get_message(role: Role, content: str) -> Message:
    msg: Message = {
        "role": role.value,
        "content": content
    }

    return msg

def load_assistant_prefill(prefill: str) -> Message:
    msg = get_message(Role.ASSISTANT, prefill)
    return msg

def load_all_prompts(state_path: str, environ_path_key: str, dynamic_metaprompt: Optional[str] = None, system_frmt: dict[str, str] = {}, user_frmt: dict[str, str] = {}, start_seq: str = "<output>") -> dict:
    system_prompt = load_system_prompt(state_path, environ_path_key, system_frmt)

    user_prompt_text = load_user_prompt(state_path, environ_path_key, dynamic_metaprompt, user_frmt)
    user_prompt = get_message(Role.USER, user_prompt_text)

    assistant_prefill = load_assistant_prefill(start_seq)

    return {"system": system_prompt, "user": user_prompt, "assistant": assistant_prefill}
import os
import keyboard
from typing import Optional
import dotenv

from rich import print

from anthropic.types.message import Message

from utils.enums import Role
from utils.stt import transcribe_speech, REC_KEY


dotenv.load_dotenv()


PRINT_PREFIX = "[bold][PROMPT_MGMT][/bold]"
FILE_EXT = ".xml"

def load_user_prompt(state_path: str, environ_path_key: str, dynamic_metaprompt: Optional[str], frmt: dict[str, str]) -> str:
    if dynamic_metaprompt:
        use_stt = os.environ.get("USE_STT") == "True"

        if not use_stt:
            print(dynamic_metaprompt, end="")
            user_prompt = "<input>" + input() + "</input>"

        else:
            print(dynamic_metaprompt, end="")

            while True:
                if keyboard.is_pressed(REC_KEY):
                    user_input = transcribe_speech()
                    break
            
            print(user_input)
            user_prompt = "<input>" + user_input + "</input>"
    
    else:
        user_prompt_dir = os.path.join(os.environ.get(environ_path_key), os.environ.get("INPUT_DIR"), os.environ.get("USR_PRMPT_DIR"))
        
        if not os.path.exists(os.path.join(user_prompt_dir, state_path+FILE_EXT)):
            print(f"[red][bold]{PRINT_PREFIX} user prompt file does not exist, and no prompt was provided as arg: {state_path+FILE_EXT}[/red][/bold]")
            exit(1)

        else:
            with open(os.path.join(user_prompt_dir, state_path+FILE_EXT), 'r') as f:
                user_prompt = f.read()

    if frmt:
        user_prompt = user_prompt.format(**frmt)
            
    return user_prompt

def load_system_prompt(state_path: str, environ_path_key: str, frmt: dict[str, str]):
    sys_prompt_dir = os.path.join(os.environ.get(environ_path_key), os.environ.get("INPUT_DIR"), os.environ.get("SYS_PRMPT_DIR"))

    with open(os.path.join(sys_prompt_dir, state_path+FILE_EXT), 'r') as f:
        sys_prompt = f.read()

    if frmt:
        sys_prompt = sys_prompt.format(**frmt)

    return sys_prompt

def load_assistant_prefill(prefill: str):
    msg = get_msg(Role.ASSISTANT, prefill)
    return msg

def load_all_prompts(state_path: str, environ_path_key: str, dynamic_metaprompt: str = None, system_frmt: dict[str, str] = {}, user_frmt: dict[str, str] = {}, start_seq: str = "<output>") -> dict:
    system_prompt = load_system_prompt(state_path, environ_path_key, system_frmt)

    user_prompt_text = load_user_prompt(state_path, environ_path_key, dynamic_metaprompt, user_frmt)
    user_prompt = get_msg(Role.USER, user_prompt_text)

    assistant_prefill = load_assistant_prefill(start_seq)

    return {"system": system_prompt, "user": user_prompt, "assistant": assistant_prefill}

def get_msg(role: Role, content: str) -> dict[str, str]:
    msg = {
        "role": role.value,
        "content": content
    }

    return msg
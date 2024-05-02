import os
import sys
import keyboard
import glob
from typing import Optional
import dotenv

from rich import print

from anthropic.types.message import Message

from utils.stt import transcribe_speech, REC_KEY


dotenv.load_dotenv()


class Memory:
    PRINT_PREFIX = "[bold][MEMORY][/bold]"
    def __init__(self, file_ext: str = ".xml", prefix: str | None = None):
        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

        self.file_ext = file_ext

        self.conversation_history: list[dict] = []
        self.sys_prompt_history: list[str] = []

        self.global_frmt: dict = self.files2dict(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), os.environ.get("GLOBAL_FRMT_DIR")), file_ext)
        self.persistence: dict = self.files2dict(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), os.environ.get("PERSISTENCE_DIR")), file_ext)

        self.results: dict[int, dict] = {}

    def files2dict(self, path, extension: str) -> dict[str, str]:
        retval = {}

        source_files = glob.glob(os.path.join(path, f'*{extension}'))

        for source_file in source_files:
            with open(source_file, 'r') as f:
                retval[os.path.basename(source_file).replace(extension, "")] = f.read()

        return retval
    
    def load_user_prompt(self, state_path: str, environ_path_key: str, dynamic_metaprompt: str, frmt: dict[str, str]) -> None:
        if dynamic_metaprompt:
            use_stt = os.environ.get("USE_STT").lower() in ('true', '1', 't')

            if not use_stt:
                print(dynamic_metaprompt, end="")
                user_prompt = "<input>" + input() + "</input>"
                self.add_msg(user_prompt, "user", frmt)
            else:
                print(dynamic_metaprompt, end="")

                while True:
                    if keyboard.is_pressed(REC_KEY):
                        user_input = transcribe_speech()
                        break
                
                print(user_input)
                user_prompt = "<input>" + user_input + "</input>"
                self.add_msg(user_prompt, "user", frmt)
        
        else:
            user_prompt_dir = os.path.join(os.environ.get(environ_path_key), os.environ.get("INPUT_DIR"), os.environ.get("USR_PRMPT_DIR"))
            
            if not os.path.exists(os.path.join(user_prompt_dir, state_path+self.file_ext)):
                print(f"[red][bold]{self.PRINT_PREFIX} user prompt file does not exist, and no prompt was provided as arg: {state_path+self.file_ext}[/red][/bold]")
            else:
                with open(os.path.join(user_prompt_dir, state_path+self.file_ext), 'r') as f:
                    user_prompt = f.read()
                    self.add_msg(user_prompt, "user", frmt)

        return user_prompt

    def load_sys_prompt(self, state_path: str, environ_path_key: str, frmt: dict[str, str]):
        sys_prompt_dir = os.path.join(os.environ.get(environ_path_key), os.environ.get("INPUT_DIR"), os.environ.get("SYS_PRMPT_DIR"))

        with open(os.path.join(sys_prompt_dir, state_path+self.file_ext), 'r') as f:
            sys_prompt = f.read()

        if frmt:
            sys_prompt = sys_prompt.format(**frmt)
            
        self.sys_prompt_history.append(sys_prompt)

        return sys_prompt

    def load_assistant_prefill(self):
        assistant_prefill = "<output>"
        self.add_msg(assistant_prefill, "assistant", {})

    def load_all_prompts(self, state_path: str, environ_path_key: str, dynamic_user_metaprompt: str, frmt: dict[str, str]) -> dict:
        system = self.load_sys_prompt(state_path, environ_path_key, frmt)
        
        self.load_user_prompt(state_path, environ_path_key, dynamic_user_metaprompt, frmt)
        self.load_assistant_prefill()

        return {"system": system, "messages": self.conversation_history}

    def store_llm_response(self, result: str):
        if self.conversation_history[-1]["role"] == "assistant":
            self.conversation_history[-1]["content"] = result
        else:
            print(f"[red][bold]{self.PRINT_PREFIX} Unexpected role at end of conversation: {self.conversation_history[-1]['role']}[/bold][/red]")

    def add_msg(self, msg: str, role: str, frmt: dict[str, str]):
        if frmt:
            msg = msg.format(**frmt)

        msg_item = {
            "role": role,
            "content": msg
        }

        self.conversation_history.append(msg_item)

    def add_msg_obj(self, msg_obj: Message, frmt: dict[str, str]):
        msg = "".join([content_item.text for content_item in msg_obj.content])

        if frmt:
            msg = msg.format(**frmt)

        msg_item = {
            "role": msg_obj.role,
            "content": msg
        }

        self.conversation_history.append(msg_item)

    def add_result(self, result: dict):
        self.results[len(self.conversation_history)] = result

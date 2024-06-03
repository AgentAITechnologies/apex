import os
import keyboard
from typing import Optional
import dotenv

from rich import print

from anthropic.types.message import Message as AnthropicMessage

from agents.prompt_management import load_all_prompts, load_system_prompt, load_user_prompt, load_assistant_prefill, get_msg

from utils.types import Message
from utils.enums import Role
from utils.parsing import files2dict
from utils.stt import transcribe_speech, REC_KEY


class Memory:
    PRINT_PREFIX = "[bold][MEMORY][/bold]"
    def __init__(self, environ_path_key: Optional[str] = None, file_ext: str = ".xml", prefix: Optional[str] = None):
        dotenv.load_dotenv()

        if prefix:
            self.PRINT_PREFIX = f"{self.PRINT_PREFIX} {prefix}"

        self.file_ext = file_ext

        self.system_prompt: Optional[str] = None

        self.conversation_history: list[dict] = []
        self.system_prompt_history: list[str] = []

        if environ_path_key:
            self.global_frmt: dict = files2dict(os.path.join(os.environ.get(environ_path_key), os.environ.get("INPUT_DIR"), os.environ.get("GLOBAL_FRMT_DIR")), file_ext)
            self.persistence: dict = files2dict(os.path.join(os.environ.get(environ_path_key), os.environ.get("INPUT_DIR"), os.environ.get("PERSISTENCE_DIR")), file_ext)

        self.results: dict[int, dict] = {}
    
    def prime_user_prompt(self, state_path: str, environ_path_key: str, dynamic_metaprompt: str, frmt: dict[str, str]) -> None:
        user_prompt_text = load_user_prompt(state_path, environ_path_key, dynamic_metaprompt, frmt)
        user_prompt_msg = get_msg(Role.USER, user_prompt_text)

        self.add_msg(user_prompt_msg)

    def prime_system_prompt(self, state_path: str, environ_path_key: str, frmt: dict[str, str]):
        self.system_prompt = load_system_prompt(state_path, environ_path_key, frmt)

        self.system_prompt_history.append(self.system_prompt)
        
    def prime_assistant_prefill(self, prefill):
        self.add_msg(load_assistant_prefill(prefill))

    def prime_all_prompts(self, state_path: str, environ_path_key: str, dynamic_metaprompt: str = None, system_frmt: dict[str, str] = {}, user_frmt: dict[str, str] = {}, start_seq: str = "<output>") -> None:
        self.prime_system_prompt(state_path, environ_path_key, system_frmt)
        self.prime_user_prompt(state_path, environ_path_key, dynamic_metaprompt, user_frmt)
        self.prime_assistant_prefill(start_seq)

    def store_llm_response(self, result: str):
        if self.conversation_history[-1]["role"] == Role.ASSISTANT.value:
            self.conversation_history[-1]["content"] = result
        else:
            print(f"[red][bold]{self.PRINT_PREFIX} Unexpected role at end of conversation: {self.conversation_history[-1]['role']}[/bold][/red]")

    def add_msg(self, msg: Message) -> None:
        self.conversation_history.append(msg)

    def add_msg_obj(self, msg_obj: AnthropicMessage, frmt: dict[str, str]):
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

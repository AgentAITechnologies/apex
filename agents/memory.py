import os
from typing import Optional
import dotenv

from rich import print

from anthropic.types.message import Message as AnthropicMessage
from anthropic.types import TextBlock

from agents.prompt_management import load_system_prompt, load_user_prompt, load_assistant_prefill, get_msg

from utils.custom_types import Message
from utils.enums import Role
from utils.parsing import files2dict

class Memory:
    PRINT_PREFIX = "[bold][MEMORY][/bold]"

    def __init__(self, environ_path_key: Optional[str] = None, file_ext: str = ".xml", prefix: Optional[str] = None) -> None:
        dotenv.load_dotenv()

        if prefix:
            self.PRINT_PREFIX = f"{self.PRINT_PREFIX} {prefix}"

        self.file_ext = file_ext

        self.system_prompt: Optional[str] = None

        self.conversation_history: list[Message] = []
        self.system_prompt_history: list[str] = []

        if environ_path_key:
            environ_path = os.environ.get(environ_path_key)
            input_path = os.environ.get("INPUT_DIR")
            global_frmt_dir = os.environ.get("GLOBAL_FRMT_DIR")
            persistence_dir = os.environ.get("PERSISTENCE_DIR")

            if environ_path and input_path:
                if global_frmt_dir:
                    self.global_frmt: dict = files2dict(os.path.join(environ_path, input_path, global_frmt_dir), file_ext)
                else:
                    print(f"[red][bold]{self.PRINT_PREFIX} GLOBAL_FRMT_DIR not set[/bold][/red]")
                    exit(1)
                if persistence_dir:
                    self.persistence: dict = files2dict(os.path.join(environ_path, input_path, persistence_dir), file_ext)
                else:
                    print(f"[red][bold]{self.PRINT_PREFIX} PERSISTENCE_DIR not set[/bold][/red]")
                    exit(1)
            else:
                print(f"[red][bold]{self.PRINT_PREFIX} invalid environ_path_key or INPUT_DIR not set:\nenviron_path_key: {environ_path_key}\ninput_path:{input_path}[/bold][/red]")
                exit(1)

        self.results: dict[int, dict] = {}
    
    def prime_user_prompt(self, state_path: str, environ_path_key: str, dynamic_metaprompt: Optional[str], frmt: dict[str, str]) -> None:
        user_prompt_text = load_user_prompt(state_path, environ_path_key, dynamic_metaprompt, frmt)
        user_prompt_msg = get_msg(Role.USER, user_prompt_text)

        self.add_msg(user_prompt_msg)

    def prime_system_prompt(self, state_path: str, environ_path_key: str, frmt: dict[str, str]) -> None:
        self.system_prompt = load_system_prompt(state_path, environ_path_key, frmt)
        self.system_prompt_history.append(self.system_prompt)

    def prime_assistant_prefill(self, prefill: str) -> None:
        self.add_msg(load_assistant_prefill(prefill))

    def prime_all_prompts(self, state_path: str, environ_path_key: str, dynamic_metaprompt: Optional[str] = None, system_frmt: dict[str, str] = {}, user_frmt: dict[str, str] = {}, start_seq: str = "<output>") -> None:
        self.prime_system_prompt(state_path, environ_path_key, system_frmt)
        self.prime_user_prompt(state_path, environ_path_key, dynamic_metaprompt, user_frmt)
        self.prime_assistant_prefill(start_seq)

    def get_system_prompt(self) -> str:
        if self.system_prompt:
            return self.system_prompt
        else:
            print(f"[red][bold]{self.PRINT_PREFIX} unprimed system prompt[/bold][/red]")
            exit(1)
    
    def get_messages(self) -> list[Message]:
        if len(self.conversation_history) > 0:
            return self.conversation_history
        else:
            print(f"[red][bold]{self.PRINT_PREFIX} unprimed conversation history[/bold][/red]")
            exit(1)

    def store_llm_response(self, result: str) -> None:
        if self.conversation_history[-1]["role"] == Role.ASSISTANT.value:
            self.conversation_history[-1]["content"] = result
        else:
            print(f"[red][bold]{self.PRINT_PREFIX} Unexpected role at end of conversation: {self.conversation_history[-1]['role']}[/bold][/red]")

    def add_msg(self, msg: Message) -> None:
        self.conversation_history.append(msg)

    def add_msg_obj(self, msg_obj: AnthropicMessage, frmt: dict[str, str]):
        msg: str = ""

        for content_item in msg_obj.content:
            if isinstance(content_item, TextBlock):
                msg += content_item.text

        if frmt:
            msg = msg.format(**frmt)

        msg_item: Message = {
            'role': msg_obj.role,
            'content': msg
        }

        self.conversation_history.append(msg_item)

    def add_result(self, result: dict):
        self.results[len(self.conversation_history)] = result

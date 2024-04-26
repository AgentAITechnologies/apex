import os
import glob
from typing import Optional
import dotenv

from rich import print

from anthropic.types.message import Message


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
    
    def load_user_prompt(self, state_path: str, dynamic_metaprompt: str):
        if dynamic_metaprompt:
            print(dynamic_metaprompt, end="")
            user_prompt = "<input>" + input() + "</input>"
            self.add_msg(user_prompt, "user")
        
        else:
            user_prompt_dir = os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), os.environ.get("USR_PRMPT_DIR"))
            
            if not os.path.exists(os.path.join(user_prompt_dir, state_path+self.file_ext)):
                print(f"[red][bold]{self.PRINT_PREFIX} user prompt file does not exist, and no prompt was provided as arg: {state_path+self.file_ext}[/red][/bold]")
            else:
                with open(os.path.join(user_prompt_dir, state_path+self.file_ext), 'r') as f:
                    user_prompt = f.read()
                    self.add_msg(user_prompt, "user")

    def load_sys_prompt(self, state_path: str):
        sys_prompt_dir = os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), os.environ.get("SYS_PRMPT_DIR"))

        with open(os.path.join(sys_prompt_dir, state_path+self.file_ext), 'r') as f:
            sys_prompt = f.read()
            self.sys_prompt_history.append(sys_prompt)

    def load_assistant_prefill(self):
        assistant_prefill = "<output>"
        self.add_msg(assistant_prefill, "assistant")

    def load_all_prompts(self, state_path: str, dynamic_user_metaprompt: str = ""):
        self.load_sys_prompt(state_path)
        self.load_user_prompt(state_path, dynamic_user_metaprompt)
        self.load_assistant_prefill()

    def store_llm_response(self, result: str):
        if self.conversation_history[-1]["role"] == "assistant":
            self.conversation_history[-1]["content"] = result
        else:
            print(f"[red][bold]{self.PRINT_PREFIX} Unexpected role at end of conversation: {self.conversation_history[-1]['role']}[/bold][/red]")

    def add_msg(self, msg: str, role: str):
        msg_item = {
            "role": role,
            "content": msg
        }

        self.conversation_history.append(msg_item)

    def add_msg_obj(self, msg_obj: Message):
        msg_item = {
            "role": msg_obj.role,
            "content": "".join([content_item.text for content_item in msg_obj.content])
        }
        self.conversation_history.append(msg_item)

    def add_result(self, result: dict):
        self.results[len(self.conversation_history)] = result

    def get_formatted_messages(self, dynamic_frmt={}) -> list[dict]:
        formatted_messages = []

        # Should never happen
        if "result" in dynamic_frmt:
            print(f"[red]{self.PRINT_PREFIX} Unexpected result in dynamic_frmt: {dynamic_frmt['result']}[/red]")
            del dynamic_frmt["result"]

        frmt = self.global_frmt.copy()
        frmt.update(dynamic_frmt)
        
        for i, message in enumerate(self.conversation_history):

            if isinstance(message["content"], dict):

                if "{result}" in message["content"][0]["text"]:
                    frmt.update({"result": str(self.results[i])})  # TODO: Parse the XML

                new_msg_content = []

                for content in message["content"]:
                    new_msg_content_text = content["text"].format(**frmt)

                    new_msg_content.append({
                            "type": content["type"],
                            "text": new_msg_content_text
                    })

                formatted_messages.append({
                    "role":  message["role"],
                    "content": new_msg_content
                })
            
            else:
                if "{result}" in message["content"] and not ("```" in message["content"]):
                    frmt.update({"result": str(self.results[i])})  # TODO: Parse the XML

                # Only format the message if it does not contain a code block
                if not ("```" in message["content"]):
                    formatted_messages.append({
                        "role":  message["role"],
                        "content": message["content"].format(**frmt)
                    })
                else:
                    formatted_messages.append({
                        "role":  message["role"],
                        "content": message["content"]
                    })
        
        return formatted_messages

    def get_formatted_system(self, dynamic_frmt: Optional[dict] = {}) -> str:
        frmt = self.global_frmt.copy()

        if dynamic_frmt:
            frmt.update(dynamic_frmt)
        
        if "state_log" in frmt:
            frmt["state_log"] = frmt["state_log"].strip()

        return self.sys_prompt_history[-1].format(**frmt)

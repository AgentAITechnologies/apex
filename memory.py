import os
import platform
import datetime

import glob

from anthropic.types.message import Message

import dotenv


dotenv.load_dotenv()


class Memory:
    def __init__(self):
        self.conversation_history: list[dict] = []
        self.sys_prompt_history: list[str] = []

        self.global_frmt: dict = self.files2dict(os.path.join(os.environ.get("INPUT_DIR"), os.environ.get("GLOBAL_FRMT_DIR")), ".md")
        self.persistence: dict = self.files2dict(os.path.join(os.environ.get("INPUT_DIR"), os.environ.get("PERSISTENCE_DIR")), ".md")

        self.results = []

    def build_general_ctxt(self) -> dict:
        ctxt_str = f"""Here is some general information about your system and your environment:
current time: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
username: {os.getlogin()}
platform: {platform.system()} {platform.release()} ({platform.machine()})
working directory: {os.getcwd()}"""
        
        general_ctxt = {
            "general_context": ctxt_str,
        }

        return general_ctxt


    def files2dict(self, path, extension) -> dict:
        retval = {}

        md_files = glob.glob(os.path.join(path, f'*{extension}'))

        for md_file in md_files:
            with open(md_file, 'r') as f:
                retval[os.path.basename(md_file).replace(extension, "")] = f.read()

        return retval
    
    def load_state_prompts(self, state_path: str):
        user_prompt_dir = os.path.join(os.environ.get("INPUT_DIR"), os.environ.get("USR_PRMPT_DIR"))
        sys_prompt_dir = os.path.join(os.environ.get("INPUT_DIR"), os.environ.get("SYS_PRMPT_DIR"))

        with open(os.path.join(user_prompt_dir, state_path+".md"), 'r') as f:
            user_prompt = f.read()
            self.add_msg(user_prompt, "user")

        with open(os.path.join(sys_prompt_dir, state_path+".md"), 'r') as f:
            sys_prompt = f.read()
            self.sys_prompt_history.append(sys_prompt)

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

    def get_formatted_messages(self, dynamic_frmt={}) -> list[dict]:
        formatted_messages = []

        # assumes that every time a result is generated, it is passed via dynamic_frmt
        if "result" in dynamic_frmt:
            self.results.append(dynamic_frmt["result"])
            del dynamic_frmt["result"]

        frmt = self.global_frmt.copy()
        frmt.update(dynamic_frmt)

        result_ptr = 0
        
        for message in self.conversation_history:

            if isinstance(message["content"], dict):

                # Do we expect a result here? 
                # If so, fill it in with the appropriate instance and increment the result pointer for the next result
                if "{result}" in message["content"][0]["text"]:
                    frmt.update({"result": self.results[result_ptr]})
                    result_ptr += 1

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

                # Do we expect a result here? 
                # If so, fill it in with the appropriate instance and increment the result pointer for the next result
                if "{result}" in message["content"]:
                    frmt.update({"result": self.results[result_ptr]})
                    result_ptr += 1

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

    def get_formatted_system(self, dynamic_frmt) -> str:
        frmt = self.global_frmt.copy()
        frmt.update(dynamic_frmt)
        
        if "state_log" in frmt:
            frmt["state_log"] = frmt["state_log"].strip()

        return self.sys_prompt_history[-1].format(**frmt)

# %%
import json

import os
import dotenv

from pprint import pprint
from rich import print

from agents.ui.state_management import ConversationStateMachine
from agents.ui.memory import Memory
from agents.ui.parsing import parse_xml


class UI:
    PRINT_PREFIX = "[bold][UI][/bold]"

    def __init__(self, term_width: int, prefix: str = ""):
        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

        self.term_width = term_width

        print(f"{self.PRINT_PREFIX} dotenv.load_dotenv(): {dotenv.load_dotenv()}")

        with open(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), "states.json")) as file:
            state_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), "transitions.json")) as file:
            transition_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='PrintUIMessage', prefix=self.PRINT_PREFIX)

        self.csm.print_state_hierarchy()
        self.csm.visualize()
        self.csm.print_current_state()

        self.memory = Memory(prefix=self.PRINT_PREFIX)
    
    def run(self, client):
        print("[green]Welcome to [italic]Jarvis[/italic][/green]")

        i = 0
        while self.csm.current_state.get_hpath() != "Exit":
            print("-"*self.term_width)
            print(f"{self.PRINT_PREFIX} Iteration {i}")
            print(f"{self.PRINT_PREFIX} self.csm.current_state.get_hpath()")

            self.memory.load_all_prompts(self.csm.current_state.get_hpath(), dynamic_user_metaprompt="[italic]How can I help?[/italic] > ")

            llm_response = self.csm.current_state.llm_call(client=client,
                                            formatted_system=self.memory.get_formatted_system(),
                                            formatted_messages=self.memory.get_formatted_messages(),
                                            stop_sequences=["</output>"])
            
            parsed_response = parse_xml(llm_response.content[0].text)
            print(f"{self.PRINT_PREFIX} parsed_response:")
            print(parsed_response)

            return 

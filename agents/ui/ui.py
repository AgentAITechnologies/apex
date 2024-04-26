# %%
from __future__ import annotations

import json

import os

from typing import Optional

from rich import print

from agents.agent import Agent
from agents.state_management import ConversationStateMachine
from agents.ui.memory import Memory
from agents.agent_manager.agent_manager import AgentManager
from agents.parsing import parse_xml


class UI(Agent):
    def __init__(self, term_width: int, prefix: str = "", name: str = "UI"):
        super().__init__(term_width, prefix=prefix, name=name)

        with open(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), "states.json")) as file:
            state_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), "transitions.json")) as file:
            transition_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='PrintUIMessage', prefix=self.PRINT_PREFIX, owner_name="UI")

        self.memory = Memory(prefix=self.PRINT_PREFIX)
        self.agent_manager = AgentManager()
        self.agent_manager.register_agent(self)
    
    def run(self, client):
        print("[bold][green]Welcome to [italic]Jarvis[/italic][/green][/bold]")

        i = 0
        while self.csm.current_state.get_hpath() != "Exit":
            print(f"{self.PRINT_PREFIX} Iteration {i}")
            print(f"{self.PRINT_PREFIX} self.csm.current_state.get_hpath(): {self.csm.current_state.get_hpath()}")

            self.memory.load_all_prompts(self.csm.current_state.get_hpath(), dynamic_user_metaprompt=" > ")

            llm_response = self.csm.current_state.llm_call(client=client,
                                            formatted_system=self.memory.get_formatted_system(),
                                            formatted_messages=self.memory.get_formatted_messages(),
                                            stop_sequences=["</output>"])
            
            self.memory.store_llm_response("<output>" + llm_response.content[0].text + "</output>")
    
            parsed_response = parse_xml(llm_response.content[0].text)
            print(f"{self.PRINT_PREFIX} parsed_response:")
            print(parsed_response)

            trigger, action = self.match_trigger(parsed_response)
            print(f"{self.PRINT_PREFIX} trigger: {trigger}")
            print(f"{self.PRINT_PREFIX} action: {action}")

            self.csm.current_state.action = action
            self.csm.transition(trigger, locals())

            i += 1
        
    def match_trigger(self, parsed_response: dict[str, Optional[str]]) -> str:
        if parsed_response["action"]:
            return "actionNotNone", parsed_response["action"]
        else:
            return "actionNone", None

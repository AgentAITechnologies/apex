# %%
from __future__ import annotations

import json

import os
import sys

from typing import Optional

from rich import print

from agents.agent import Agent
from agents.state_management import ConversationStateMachine
from agents.memory import Memory
from agents.agent_manager.agent_manager import AgentManager
from utils.parsing import xmlstr2dict


class UI(Agent):
    def __init__(self, term_width: int, prefix: str = "",
                 name: str = "UI",
                 description: str = 'Continually manages the interaction bewteen the user and yourself, the "Agent Manager". If you ever need to message the user, this agent will help you do so.',
                 tasks: list[dict] = [{"task": 'Communicate with the user'}]):
        
        super().__init__(term_width, prefix=prefix, name=name, description=description, tasks=tasks)

        with open(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), "states.json")) as file:
            state_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(os.environ.get("UI_DIR"), os.environ.get("INPUT_DIR"), "transitions.json")) as file:
            transition_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='Start', prefix=self.PRINT_PREFIX, owner_class_name="UI")

        self.memory = Memory(prefix=self.PRINT_PREFIX)
        self.agent_manager = AgentManager()
        self.agent_manager.register_agent(self)

        self.parsed_response = None
    
    def run(self, client):
        print("[bold][green]Welcome to [italic]Jarvis[/italic][/green][/bold]")

        i = 0
        while self.csm.current_state.get_hpath() != "Exit":
            print(f"{self.PRINT_PREFIX} Iteration {i}")
            print(f"{self.PRINT_PREFIX} self.csm.current_state.get_hpath(): {self.csm.current_state.get_hpath()}")

            if i == 0: # here only to ensure printing can happen in a sensible order
                self.csm.transition("start", locals())

            trigger, result = self.match_trigger() # consumes self.parsed_response
            print(f"{self.PRINT_PREFIX} trigger: {trigger}")
            print(f"{self.PRINT_PREFIX} result: {result}")

            self.csm.current_state.result = result
            self.csm.transition(trigger, locals())

            i += 1
        
    def match_trigger(self) -> tuple[str, Optional[dict]]:
        if not self.parsed_response:
            print(f"[red][bold]{self.PRINT_PREFIX} parsed_response is empty[/bold][/red]")
            sys.exit(1)
        else:
            parsed_response = self.parsed_response
            self.parsed_response = None

            if parsed_response["action"]:
                return "actionNotNone", {"action": parsed_response["action"]}
            else:
                return "actionNone", None

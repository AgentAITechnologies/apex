from __future__ import annotations

import json

import os
import sounddevice as sd

from rich import print as rprint
from utils.console_io import debug_print as dprint

from agents.agent import Agent
from agents.memory import Memory
from agents.agent_manager.agent_manager import AgentManager
from agents.state_management import ConversationStateMachine

from utils.custom_exceptions import UIError
from utils.constants import FRIENDLY_COLOR

from utils.parsing import xmlstr2dict
from utils.tts import tts
from utils.llm import llm_turn

from anthropic import Anthropic


class UI(Agent):
    def __init__(self,
                 client: Anthropic,
                 prefix: str = "",
                 name: str = "UI",
                 description: str = 'Continually manages the interaction bewteen the user and yourself, the "Agent Manager". If you ever need to message the user, this agent will help you do so.',
                 tasks: list[dict] = [{"task": 'Communicate with the user'}]) -> None:
        
        super().__init__(client=client,
                         prefix=prefix,
                         name=name,
                         description=description,
                         tasks=tasks)

        UI_DIR = os.environ.get("UI_DIR")
        if not UI_DIR:
            error_message = f"{self.PRINT_PREFIX} UI_DIR not set"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)

        INPUT_DIR = os.environ.get("INPUT_DIR")
        if not INPUT_DIR:
            error_message = f"{self.PRINT_PREFIX} INPUT_DIR not set"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)

        state_file_path = os.path.join(UI_DIR, INPUT_DIR, "states.json")

        try:
            with open(state_file_path) as file:
                state_data = json.load(file)
            dprint(f"{self.PRINT_PREFIX} loaded state_data")
        except FileNotFoundError:
            error_message = f"{self.PRINT_PREFIX} states.json not found at {state_file_path}"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise
        except json.JSONDecodeError:
            error_message = f"{self.PRINT_PREFIX} Error decoding JSON in states.json"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise

        transition_file_path = os.path.join(UI_DIR, INPUT_DIR, "transitions.json")

        try:
            with open(transition_file_path) as file:
                transition_data = json.load(file)
            dprint(f"{self.PRINT_PREFIX} loaded transition_data")
        except FileNotFoundError:
            error_message = f"{self.PRINT_PREFIX} transitions.json not found at {transition_file_path}"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise
        except json.JSONDecodeError:
            error_message = f"{self.PRINT_PREFIX} Error decoding JSON in transitions.json"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='Start', prefix=self.PRINT_PREFIX, owner_class_name="UI")

        self.memory = Memory(environ_path_key="UI_DIR", prefix=self.PRINT_PREFIX)
        self.agent_manager = AgentManager()
        self.agent_manager.register_agent(self)

        self.parsed_response = None
    
    def run(self):
        rprint(f"[bold][{FRIENDLY_COLOR}]Welcome to [italic]APEX[/italic][/{FRIENDLY_COLOR}][/bold]\n")

        while self.csm.current_state.get_hpath() != "Exit":
            dprint(f"{self.PRINT_PREFIX} At: {self.csm.current_state.get_hpath()}")
                
            match self.csm.current_state.get_hpath():

                case "Start":
                    self.csm.transition("PrintUIMessage", locals())

                case "PrintUIMessage":
                    self.memory.prime_all_prompts(self.csm.current_state.get_hpath(), "UI_DIR", dynamic_metaprompt=" > ")

                    text = llm_turn(client=self.client,
                                    prompts={'system': self.memory.get_system_prompt(),
                                             'messages': self.memory.get_messages()},
                                    stop_sequences=["</output>"],
                                    temperature=0.7)
                    
                    self.memory.store_llm_response("<output>" + text + "</output>")

                    parsed_response = xmlstr2dict(text, self.client)
                    dprint(f"{self.PRINT_PREFIX} parsed_response:")
                    dprint(parsed_response)

                    rprint("\n[bold]" + parsed_response["response"] + "[/bold]\n")

                    if os.environ.get("USE_TTS") == "True":
                        tts(parsed_response["response"])

                    if "action" in parsed_response and parsed_response["action"]:
                        action = parsed_response["action"]

                        if action == "REST":
                            rprint(f"Exiting...")
                            sd.wait()
                            exit(0)
                        else:
                            self.csm.transition("AssignAction", locals())

                case "AssignAction":
                    if action:
                        dprint(f"{self.PRINT_PREFIX} action: {action}")

                        self.agent_manager.ipc("RouteAction", {"action": action})
                        self.csm.transition("PrintUIMessage", locals)
                    else:
                        error_message = f"{self.PRINT_PREFIX} no action to assign"
                        rprint(f"[red][bold]{error_message}[/bold][/red]")
                        raise UIError(error_message)

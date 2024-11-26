from __future__ import annotations

import json

import os
from typing import cast
import sounddevice as sd

from rich import print as rprint
from utils.console_io import debug_print as dprint

from agents.agent import Agent
from agents.memory import Memory
from agents.agent_manager.agent_manager import AgentManager
from agents.state_management import ConversationStateMachine

from utils.custom_exceptions import UIError
from utils.constants import FRIENDLY_COLOR

from utils.files import read_persistent_notes, write_persistent_note
from utils.parsing import dict2xml, xml2xmlstr, xmlstr2dict
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

        parsed_response = None

        while self.csm.current_state.get_hpath() != "Exit":
            dprint(f"{self.PRINT_PREFIX} At: {self.csm.current_state.get_hpath()}")

            persistent_notes = read_persistent_notes()
                
            match self.csm.current_state.get_hpath():

                case "Start":
                    self.csm.transition("PrintUIMessage", locals())

                case "PrintUIMessage":
                    self.memory.prime_all_prompts(self.csm.current_state.get_hpath(),
                                                  "UI_DIR",
                                                  dynamic_metaprompt=" > ",
                                                  system_frmt={"persistent_notes": persistent_notes})

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

                    if "notes" in parsed_response and parsed_response["notes"]:
                        self.csm.transition("TakeNote", locals())
                    elif "action" in parsed_response and parsed_response["action"]:
                        self.csm.transition("AssignAction", locals())
                    else:
                        continue
                
                case "TakeNote":
                    if parsed_response and "notes" in parsed_response and parsed_response["notes"]:
                        dprint(f"{self.PRINT_PREFIX} note: {parsed_response['notes']}")
                        write_persistent_note(xml2xmlstr(dict2xml(parsed_response["notes"])))
                    else:
                        error_message = f"{self.PRINT_PREFIX} no notes in parsed_response, despite being in {self.csm.current_state.get_hpath()}"
                        rprint(f"[red][bold]{error_message}[/bold][/red]")
                        raise UIError(error_message)
                        
                    if "action" in parsed_response and parsed_response["action"]:
                        self.csm.transition("AssignAction", locals())
                    else:
                        self.csm.transition("PrintUIMessage", locals())

                case "AssignAction":
                    if parsed_response and "action" in parsed_response and parsed_response["action"]:
                        dprint(f"{self.PRINT_PREFIX} action: {parsed_response['action']}")
                        action = parsed_response["action"]

                        if action == "REST":
                            rprint(f"Exiting...")
                            sd.wait()
                            exit(0)

                        self.agent_manager.ipc("RouteAction", {"action": action})
                        self.csm.transition("PrintUIMessage", locals)
                    else:
                        error_message = f"{self.PRINT_PREFIX} no action in parsed_response, despite being in {self.csm.current_state.get_hpath()}"
                        rprint(f"[red][bold]{error_message}[/bold][/red]")
                        raise UIError(error_message)

                case _:
                    error_message = f"{self.PRINT_PREFIX} unhandled state: {self.csm.current_state.get_hpath()}"
                    rprint(f"[red][bold]{error_message}[/bold][/red]")
                    raise UIError(error_message)

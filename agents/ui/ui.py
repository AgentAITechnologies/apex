from __future__ import annotations

import json

import os
import sys
import sounddevice as sd

from rich import print

from agents.agent import Agent
from agents.memory import Memory
from agents.agent_manager.agent_manager import AgentManager
from agents.state_management import ConversationStateMachine

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

        with open(os.path.join(os.environ.get("UI_DIR", "NO_PATH_SET"), os.environ.get("INPUT_DIR", "NO_PATH_SET"), "states.json")) as file:
            state_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(os.environ.get("UI_DIR", "NO_PATH_SET"), os.environ.get("INPUT_DIR", "NO_PATH_SET"), "transitions.json")) as file:
            transition_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='Start', prefix=self.PRINT_PREFIX, owner_class_name="UI")

        self.memory = Memory(environ_path_key="UI_DIR", prefix=self.PRINT_PREFIX)
        self.agent_manager = AgentManager()
        self.agent_manager.register_agent(self)

        self.parsed_response = None
    
    def run(self):
        print("[bold][deep_sky_blue1]Welcome to [italic]Jarvis[/italic][/deep_sky_blue1][/bold]")

        while self.csm.current_state.get_hpath() != "Exit":
            print(f"{self.PRINT_PREFIX} self.csm.current_state.get_hpath(): {self.csm.current_state.get_hpath()}")
                
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
                    print(f"{self.PRINT_PREFIX} parsed_response:")
                    print(parsed_response)

                    if os.environ.get("USE_TTS") == "True":
                        tts(parsed_response["response"])

                    if "action" in parsed_response and parsed_response["action"]:
                        action = parsed_response["action"]

                        if action == "REST":
                            print(f"{self.PRINT_PREFIX} Exiting...")
                            sd.wait()
                            exit(0)
                        else:
                            self.csm.transition("AssignAction", locals())

                case "AssignAction":
                    if action:
                        print(f"{self.PRINT_PREFIX} action: {action}")
                        self.agent_manager.ipc("RouteAction", {"action": action})
                        self.csm.transition("PrintUIMessage", locals)
                    else:
                        print(f"[red][bold]{self.PRINT_PREFIX} no action to assign[/bold][/red]")
                        sys.exit(1)

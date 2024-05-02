import json
import os
import sys
import dotenv

from typing import Optional

from rich import print

from agents.agent import Agent
from agents.state_management import ConversationStateMachine
from agents.memory import Memory
from agents.tot.tot import ToT

from anthropic import Anthropic

from utils.parsing import dict2xml, xml2xmlstr, xmlstr2dict

class AgentManager():
    PRINT_PREFIX = "[bold][AgentMgr][/bold]"

    _instance = None

    def __new__(cls, *args, **kwargs):
        if "client" in kwargs:
            cls.client: Anthropic = kwargs['client']

        if "prefix" in kwargs:
            cls.PRINT_PREFIX = f"{kwargs['prefix']} {cls.PRINT_PREFIX}"

        if cls._instance is None:
            print(f"{cls.PRINT_PREFIX} Creating a singleton AgentManager")
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance.__initialized = False

        return cls._instance
    
    def __init__(self, client=None, prefix: str = ""):
        if not self.__initialized:
            dotenv.load_dotenv()

            self.agents: list[Agent] = []

            with open(os.path.join(os.environ.get("AGTMGR_DIR"), os.environ.get("INPUT_DIR"), "states.json")) as file:
                state_data = json.load(file)
                print(f"{self.PRINT_PREFIX} loaded state_data")

            with open(os.path.join(os.environ.get("AGTMGR_DIR"), os.environ.get("INPUT_DIR"), "transitions.json")) as file:
                transition_data = json.load(file)
                print(f"{self.PRINT_PREFIX} loaded transition_data")

            self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='AwaitIPC', prefix=self.PRINT_PREFIX, owner_class_name="AgentManager")
            self.memory = Memory(prefix=self.PRINT_PREFIX)

            self.parsed_response = None

            self.__initialized = True
            print(f"{self.PRINT_PREFIX} Initialized the instance")

    def create_agent(self, name: str, description: str, tasks: list[dict]):
        agent = ToT(name=name, description=description, tasks=tasks)
        self.register_agent(agent)

    def register_agent(self, agent: Agent):
        print(f"{self.PRINT_PREFIX} Registering agent: {agent.name}")
        self.agents.append(agent)

    def ipc(self, trigger: str, result: dict):
        self.csm.transition(trigger, locals()) # sets self.parsed_response

        trigger, result = self.match_trigger()

        self.csm.transition(trigger, locals()) # sets self.parsed_response

    def match_trigger(self, no_response=False) -> tuple[str, Optional[dict]]:  # consumes self.parsed_response
        if not no_response and not self.parsed_response:
            print(f"[red][bold]{self.PRINT_PREFIX} parsed_response is empty when no_response was {no_response}[/bold][/red]")
            sys.exit(1)
        else:
            parsed_response = self.parsed_response
            self.parsed_response = None

            if not parsed_response["name"]:
                return "createAgent", None
            else:
                return "assignAgent", {"agent_name": parsed_response["name"]}





import json
import os
import dotenv

from rich import print

from agents.agent import Agent
from agents.state_management import ConversationStateMachine

class AgentManager():
    PRINT_PREFIX = "[bold][AgentMgr][/bold]"

    _instance = None

    def __new__(cls, *args, **kwargs):
        if "prefix" in kwargs:
            cls.PRINT_PREFIX = f"{kwargs['prefix']} {cls.PRINT_PREFIX}"

        if cls._instance is None:
            print(f"{cls.PRINT_PREFIX} Creating a singleton AgentManager")
            cls._instance = super(AgentManager, cls).__new__(cls)
            cls._instance.__initialized = False

        return cls._instance
    
    def __init__(self, prefix: str = ""):
        if not self.__initialized:
            dotenv.load_dotenv()

            self.agents: list[Agent] = []

            with open(os.path.join(os.environ.get("AGTMGR_DIR"), os.environ.get("INPUT_DIR"), "states.json")) as file:
                state_data = json.load(file)
                print(f"{self.PRINT_PREFIX} loaded state_data")

            with open(os.path.join(os.environ.get("AGTMGR_DIR"), os.environ.get("INPUT_DIR"), "transitions.json")) as file:
                transition_data = json.load(file)
                print(f"{self.PRINT_PREFIX} loaded transition_data")

            self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='AwaitIPC', prefix=self.PRINT_PREFIX, owner_name="AgentManager")

            self.__initialized = True
            print(f"{self.PRINT_PREFIX} Initialized the instance")

    def register_agent(self, agent: Agent):
        print(f"{self.PRINT_PREFIX} Registering agent: {agent.name}")
        self.agents.append(agent)

    # TODO: choose appropriate agent to send message to
    # For now, just spawn a new agent
    def route_action(self, action: dict):
        self.csm.transition("routeAction", locals())
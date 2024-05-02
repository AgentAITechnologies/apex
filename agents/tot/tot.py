import os
import json

from rich import print

from agents.state_management import ConversationStateMachine
from agents.memory import Memory

class ToT():
    PRINT_PREFIX = "[blue][bold][ToT][/bold][/blue]"

    def __init__(self, name, description, tasks):
        self.name = name
        self.description = description
        self.tasks = tasks

        with open(os.path.join(os.environ.get("TOT_DIR"), os.environ.get("INPUT_DIR"), "states.json")) as file:
            state_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(os.environ.get("TOT_DIR"), os.environ.get("INPUT_DIR"), "transitions.json")) as file:
            transition_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='Plan', prefix=self.PRINT_PREFIX, owner_class_name="ToT")

        self.memory = Memory()
    
    def run(self, client):
        pass
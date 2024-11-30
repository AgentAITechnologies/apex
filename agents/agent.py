
from typing import Optional

import dotenv
from anthropic import Anthropic

from rich import print as rprint
from utils.console_io import debug_print as dprint

class Agent():
    def __init__(self, client: Anthropic, prefix: Optional[str], name: str, description: str, tasks: list[dict], agent_manager):
        dotenv.load_dotenv()

        self.client = client

        self.PRINT_PREFIX = f"[bold][{name}][/bold]"
        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

        self.name = name
        self.description = description
        self.tasks = tasks

        dprint(f"{self.PRINT_PREFIX} dotenv.load_dotenv(): {dotenv.load_dotenv()}")

    def add_task(self, task: dict):
        self.tasks.append(task)

    def handle_message(self):
        rprint(f"[red][bold]{self.PRINT_PREFIX} handle_msg() unimplemented for agent: {self.name}")
        pass

    def run(self):
        pass
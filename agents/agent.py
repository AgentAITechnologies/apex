from typing import Optional, Any
from datetime import datetime

import dotenv
from anthropic import Anthropic

from utils.console_io import debug_print as dprint

class Agent():
    def __init__(self, client: Anthropic, prefix: Optional[str], name: str, description: str, tasks: list[dict], created_at: Optional[str] = None, updated_at: Optional[str] = None):
        dotenv.load_dotenv()

        self.client = client

        self.PRINT_PREFIX = f"[bold][{name}][/bold]"
        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

        self.name = name
        self.description = description
        self.tasks = tasks
        self.last_output: str = ""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created_at: str = created_at or now_str
        self.updated_at: str = updated_at or now_str

        dprint(f"{self.PRINT_PREFIX} dotenv.load_dotenv(): {dotenv.load_dotenv()}")

    def add_task(self, task: dict):
        self.tasks.append(task)
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_last_output(self) -> str:
        return self.last_output

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "tasks": self.tasks,
            "last_output": self.last_output,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "class": self.__class__.__name__
        }

    def run(self):
        pass
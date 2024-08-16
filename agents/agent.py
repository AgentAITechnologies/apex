
from anthropic import Anthropic
import dotenv

from rich import print

class Agent():
    def __init__(self, client: Anthropic, prefix, name: str, description: str, tasks: list[dict]):
        dotenv.load_dotenv()

        self.client = client

        self.PRINT_PREFIX = f"[bold][{name}][/bold]"
        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

        self.name = name
        self.description = description
        self.tasks = tasks

        print(f"{self.PRINT_PREFIX} dotenv.load_dotenv(): {dotenv.load_dotenv()}")

    def add_task(self, task: dict):
        self.tasks.append(task)

    def run(self):
        pass
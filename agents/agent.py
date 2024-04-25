from typing import Optional

import dotenv

from rich import print

class Agent():
    def __init__(self, term_width: int, prefix: str = "", name: str = "UI"):
        self.term_width = term_width

        self.PRINT_PREFIX = f"[bold][{name}][/bold]"
        if prefix:
            self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

        self.name = name

        print(f"{self.PRINT_PREFIX} dotenv.load_dotenv(): {dotenv.load_dotenv()}")

    def run(self, client):
        pass

    def match_trigger(self, parsed_response: dict[str, Optional[str]]) -> str:
        pass
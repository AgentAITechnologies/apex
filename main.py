import anthropic
import os
import dotenv

from rich import print 

from agents.agent_manager.agent_manager import AgentManager
from agents.ui.ui import UI


dotenv.load_dotenv()

FRIENDLY_COLOR = "green"
PRINT_PREFIX = "[bold][MAIN][/bold]"


def main():
    print()

    try:
        TERM_WIDTH = os.get_terminal_size().columns
        print(f"{PRINT_PREFIX} TERM_WIDTH: {TERM_WIDTH}")
    except OSError:
        TERM_WIDTH = os.environ.get("HEADLESS_TERM_WIDTH")
        print(f"{PRINT_PREFIX} TERM_WIDTH (headless): {TERM_WIDTH}")

    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    agent_manager = AgentManager(client=client, prefix=PRINT_PREFIX)

    ui = UI(term_width=TERM_WIDTH, prefix=PRINT_PREFIX, name="UI")
    ui.run(client)


if __name__ == "__main__":
    main()
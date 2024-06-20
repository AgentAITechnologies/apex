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
        os.environ["TERM_WIDTH"] = str(TERM_WIDTH)
        print(f"{PRINT_PREFIX} TERM_WIDTH: {TERM_WIDTH}")
    except OSError:
        TERM_WIDTH = int(os.environ.get("TERM_WIDTH", "160"))
        print(f"{PRINT_PREFIX} TERM_WIDTH (headless): {TERM_WIDTH}")

    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    agent_manager = AgentManager(client=client, prefix=PRINT_PREFIX)

    ui = UI(client=client, prefix=PRINT_PREFIX)
    ui.run()


if __name__ == "__main__":
    main()
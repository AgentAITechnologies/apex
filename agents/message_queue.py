from typing import Optional, Type
from typing_extensions import Self

from anthropic import Anthropic

from rich import print as rprint
from utils.console_io import debug_print as dprint


class MessageQueue():
    PRINT_PREFIX = "[bold][MsgQ][/bold]"

    _instance = None

    def __new__(cls: Type[Self], *args, **kwargs) -> Self:
        if cls._instance is None:
            dprint(f"{cls.PRINT_PREFIX} Creating a singleton MessageQueue")
            cls._instance = super(MessageQueue, cls).__new__(cls)
            cls._instance.__initialized = False

        return cls._instance
    
    def __init__(self, client: Optional[Anthropic] = None, prefix = "") -> None:
        if not self.__initialized:
            if prefix:
                self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

            self.mailboxes: dict[str, list[dict[str, str]]] = {} # TODO: define a custom type

            self.__initialized = True
            dprint(f"{self.PRINT_PREFIX} Initialized the instance")

    def register_mailbox(self, agent_name: str):
        self.mailboxes[agent_name] = []
        dprint(f"{self.PRINT_PREFIX} Registered mailbox for agent: {agent_name}")

    def push(self, src_agent_name: str, dest_agent_name: str, text: str) -> None:
        if dest_agent_name in self.mailboxes:
            self.mailboxes[dest_agent_name].append({"src_agent_name": src_agent_name, "text": text})
        else:
            rprint(f"[red][bold]Tried to send a message to an agent with no mailbox: {dest_agent_name}")

    def pop(self, agent_name: str) -> Optional[str]:
        if agent_name in self.mailboxes:
            messages = self.mailboxes[agent_name]
            
            if len(messages) > 0:
                return messages.pop(0)
            else:
                return None
        else:
            rprint(f"[red][bold]Tried to read a message for an agent that has no mailbox: {agent_name}[/bold][/red]")
            exit(1)

    def has_message(self, agent_name: str) -> bool:
        return agent_name in self.mailboxes and len(self.mailboxes[agent_name]) > 0
        
    

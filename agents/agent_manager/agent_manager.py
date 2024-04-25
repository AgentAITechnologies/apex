from rich import print

from agents.agent import Agent

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
            self.agents: list[Agent] = []

            self.__initialized = True
            print(f"{self.PRINT_PREFIX} Initialized the instance")

    def register(self, agent: Agent):
        print(f"{self.PRINT_PREFIX} Registering agent: {agent.name}")
        self.agents.append(agent)

    def task2xml(self, task: str) -> str:
        pass

class StateCallback:
    PRINT_PREFIX = "[bold][Callback][/bold]"

    def __init__(self, prefix: str) -> None:
        self.PRINT_PREFIX = f"{prefix} {self.PRINT_PREFIX}"

    def on_enter(self, csm, locals: dict):
        pass

    def on_exit(self, csm, locals: dict):
        pass

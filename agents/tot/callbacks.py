from utils.console_io import debug_print as dprint

import dotenv
dotenv.load_dotenv()

from agents.state_callback import StateCallback


class root_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering root")
        # Perform actions when entering root
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting root")
        # Perform actions when exiting root
        pass

class HighLevel_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering HighLevel")
        # Perform actions when entering HighLevel
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting HighLevel")
        # Perform actions when exiting HighLevel
        pass

class HighLevel_Plan_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering HighLevel_Plan")
        # Perform actions when entering HighLevel_Plan
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting HighLevel_Plan")
        # Perform actions when exiting HighLevel_Plan
        pass

class HighLevel_PlanVote_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering HighLevel_PlanVote")
        # Perform actions when entering HighLevel_PlanVote
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting HighLevel_PlanVote")
        # Perform actions when exiting HighLevel_PlanVote
        pass

class HighLevel_SumPlanVotes_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering HighLevel_SumPlanVotes")
        # Perform actions when entering HighLevel_SumPlanVotes
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting HighLevel_SumPlanVotes")
        # Perform actions when exiting HighLevel_SumPlanVotes
        pass

class HighLevel_ChoosePlan_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering HighLevel_ChoosePlan")
        # Perform actions when entering HighLevel_ChoosePlan
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting HighLevel_ChoosePlan")
        # Perform actions when exiting HighLevel_ChoosePlan
        pass

class Plan_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering Plan")
        # Perform actions when entering Plan
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting Plan")
        # Perform actions when exiting Plan
        pass

class PlanVote_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering PlanVote")
        # Perform actions when entering PlanVote
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting PlanVote")
        # Perform actions when exiting PlanVote
        pass

class SumPlanVotes_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering SumPlanVotes")
        # Perform actions when entering SumPlanVotes
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting SumPlanVotes")
        # Perform actions when exiting SumPlanVotes
        pass

class ChoosePlan_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering ChoosePlan")
        # Perform actions when entering ChoosePlan
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting ChoosePlan")
        # Perform actions when exiting ChoosePlan
        pass

class Propose_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering Propose")
        # Perform actions when entering Propose
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting Propose")
        # Perform actions when exiting Propose
        pass

class ProposeVote_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering ProposeVote")
        # Perform actions when entering ProposeVote
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting ProposeVote")
        # Perform actions when exiting ProposeVote
        pass

class SumProposeVotes_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering SumProposeVotes")
        # Perform actions when entering SumProposeVotes
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting SumProposeVotes")
        # Perform actions when exiting SumProposeVotes
        pass

class ChooseProposition_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering ChooseProposition")
        # Perform actions when entering ChooseProposition
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting ChooseProposition")
        # Perform actions when exiting ChooseProposition
        pass

class Exec_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering Exec")
        # Perform actions when entering Exec
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting Exec")
        # Perform actions when exiting Exec
        pass

class ExecVote_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering ExecVote")
        # Perform actions when entering ExecVote
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting ExecVote")
        # Perform actions when exiting ExecVote
        pass

class PlanErrorFix_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering PlanErrorFix")
        # Perform actions when entering PlanErrorFix
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting PlanErrorFix")
        # Perform actions when exiting PlanErrorFix
        pass

class SumExecVote_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering SumExecVote")
        # Perform actions when entering SumExecVote
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting SumExecVote")
        # Perform actions when exiting SumExecVote
        pass

class Done_Callback(StateCallback):
    def on_enter(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Entering Done")
        # Perform actions when entering Done
        pass

    def on_exit(self, csm, locals):
        dprint(f"{self.PRINT_PREFIX} Exiting Done")
        # Perform actions when exiting Done
        pass


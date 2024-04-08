import json
import inspect
import os
import dotenv
import datetime

import traceback

from execution_management import exec_python, capture_python_output


dotenv.load_dotenv()





class StateCallback:
    def on_enter(self, csm, locals: dict):
        pass

    def on_exit(self, csm, locals: dict):
        pass


## Begin code generated by meta_tools/update_callbacks.py

class Root_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Root")
        # Perform actions when entering Root
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Root")
        # Perform actions when exiting Root
        pass

class Start_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Start")
        # Perform actions when entering Start
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Start")
        # Perform actions when exiting Start
        pass

class Start_SelectReady_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Start_SelectReady")
        # Perform actions when entering Start_SelectReady
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Start_SelectReady")
        # Perform actions when exiting Start_SelectReady
        pass

class Notready_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready")
        # Perform actions when entering Notready
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready")
        # Perform actions when exiting Notready
        pass

class Notready_SelectGetSetState_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState")
        # Perform actions when entering Notready_SelectGetSetState
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState")
        # Perform actions when exiting Notready_SelectGetSetState
        pass

class Notready_SelectGetSetState_GetState_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_GetState")
        # Perform actions when entering Notready_SelectGetSetState_GetState
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_GetState")
        # Perform actions when exiting Notready_SelectGetSetState_GetState
        pass

class Notready_SelectGetSetState_GetState_SelectTool_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_GetState_SelectTool")
        # Perform actions when entering Notready_SelectGetSetState_GetState_SelectTool
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_GetState_SelectTool")
        # Perform actions when exiting Notready_SelectGetSetState_GetState_SelectTool
        pass

class Notready_SelectGetSetState_GetState_SelectTool_ComposeQuestion_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_GetState_SelectTool_ComposeQuestion")
        # Perform actions when entering Notready_SelectGetSetState_GetState_SelectTool_ComposeQuestion
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_GetState_SelectTool_ComposeQuestion")
        # Perform actions when exiting Notready_SelectGetSetState_GetState_SelectTool_ComposeQuestion
        pass

class Notready_SelectGetSetState_GetState_SelectTool_ComposePython_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_GetState_SelectTool_ComposePython")
        # Perform actions when entering Notready_SelectGetSetState_GetState_SelectTool_ComposePython
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_GetState_SelectTool_ComposePython")
        # Perform actions when exiting Notready_SelectGetSetState_GetState_SelectTool_ComposePython

        # run and capture output
        # store in csm.current_state.frmt
        capture_python_output(csm, locals)

class Notready_SelectGetSetState_GetState_SelectTool_ComposePowershell_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_GetState_SelectTool_ComposePowershell")
        # Perform actions when entering Notready_SelectGetSetState_GetState_SelectTool_ComposePowershell
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_GetState_SelectTool_ComposePowershell")
        # Perform actions when exiting Notready_SelectGetSetState_GetState_SelectTool_ComposePowershell
        pass

class Notready_SelectGetSetState_GetState_SelectTool_ComposeScreenshot_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_GetState_SelectTool_ComposeScreenshot")
        # Perform actions when entering Notready_SelectGetSetState_GetState_SelectTool_ComposeScreenshot
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_GetState_SelectTool_ComposeScreenshot")
        # Perform actions when exiting Notready_SelectGetSetState_GetState_SelectTool_ComposeScreenshot
        pass

class Notready_SelectGetSetState_SetState_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_SetState")
        # Perform actions when entering Notready_SelectGetSetState_SetState
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_SetState")
        # Perform actions when exiting Notready_SelectGetSetState_SetState
        pass

class Notready_SelectGetSetState_SetState_SelectTool_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_SetState_SelectTool")
        # Perform actions when entering Notready_SelectGetSetState_SetState_SelectTool
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_SetState_SelectTool")
        # Perform actions when exiting Notready_SelectGetSetState_SetState_SelectTool
        pass

class Notready_SelectGetSetState_SetState_SelectTool_ComposeMessage_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_SetState_SelectTool_ComposeMessage")
        # Perform actions when entering Notready_SelectGetSetState_SetState_SelectTool_ComposeMessage
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_SetState_SelectTool_ComposeMessage")
        # Perform actions when exiting Notready_SelectGetSetState_SetState_SelectTool_ComposeMessage
        pass

class Notready_SelectGetSetState_SetState_SelectTool_ComposePython_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_SetState_SelectTool_ComposePython")
        # Perform actions when entering Notready_SelectGetSetState_SetState_SelectTool_ComposePython
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_SetState_SelectTool_ComposePython")
        # Perform actions when exiting Notready_SelectGetSetState_SetState_SelectTool_ComposePython
        capture_python_output(csm, locals)

class Notready_SelectGetSetState_SetState_SelectTool_ComposePowershell_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_SetState_SelectTool_ComposePowershell")
        # Perform actions when entering Notready_SelectGetSetState_SetState_SelectTool_ComposePowershell
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_SetState_SelectTool_ComposePowershell")
        # Perform actions when exiting Notready_SelectGetSetState_SetState_SelectTool_ComposePowershell
        pass

class Notready_SelectGetSetState_SetState_SelectTool_ComposeScreenshot_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_SetState_SelectTool_ComposeScreenshot")
        # Perform actions when entering Notready_SelectGetSetState_SetState_SelectTool_ComposeScreenshot
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_SetState_SelectTool_ComposeScreenshot")
        # Perform actions when exiting Notready_SelectGetSetState_SetState_SelectTool_ComposeScreenshot
        pass

class Notready_SelectReady_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectReady")
        # Perform actions when entering Notready_SelectReady
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectReady")
        # Perform actions when exiting Notready_SelectReady
        pass

class Ready_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Ready")
        # Perform actions when entering Ready
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Ready")
        # Perform actions when exiting Ready
        pass

class Ready_SelectTool_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Ready_SelectTool")
        # Perform actions when entering Ready_SelectTool
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Ready_SelectTool")
        # Perform actions when exiting Ready_SelectTool
        pass

class Ready_SelectTool_ComposeMessage_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Ready_SelectTool_ComposeMessage")
        # Perform actions when entering Ready_SelectTool_ComposeMessage
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Ready_SelectTool_ComposeMessage")
        # Perform actions when exiting Ready_SelectTool_ComposeMessage
        pass

class Ready_SelectTool_ComposePython_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Ready_SelectTool_ComposePython")
        # Perform actions when entering Ready_SelectTool_ComposePython
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Ready_SelectTool_ComposePython")
        # Perform actions when exiting Ready_SelectTool_ComposePython

        # run and capture output
        # store in csm.current_state.frmt
        capture_python_output(csm, locals)


class Ready_SelectTool_ComposePowershell_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Ready_SelectTool_ComposePowershell")
        # Perform actions when entering Ready_SelectTool_ComposePowershell
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Ready_SelectTool_ComposePowershell")
        # Perform actions when exiting Ready_SelectTool_ComposePowershell
        pass

class Ready_SelectTool_ComposeScreenshot_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Ready_SelectTool_ComposeScreenshot")
        # Perform actions when entering Ready_SelectTool_ComposeScreenshot
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Ready_SelectTool_ComposeScreenshot")
        # Perform actions when exiting Ready_SelectTool_ComposeScreenshot
        pass

class Ready_SelectDone_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Ready_SelectDone")
        # Perform actions when entering Ready_SelectDone
        pass
        
    def on_exit(self, csm, locals):
        print(f"Exiting Ready_SelectDone")
        # Perform actions when exiting Ready_SelectDone
        pass

class Failure_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Failure")
        # Perform actions when entering Failure
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Failure")
        # Perform actions when exiting Failure
        pass

class Failure_IdentifyProblems_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Failure_IdentifyProblems")
        # Perform actions when entering Failure_IdentifyProblems
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Failure_IdentifyProblems")
        # Perform actions when exiting Failure_IdentifyProblems
        pass

class Failure_SelectReady_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Failure_SelectReady")
        # Perform actions when entering Failure_SelectReady
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Failure_SelectReady")
        # Perform actions when exiting Failure_SelectReady
        pass

class Notready_SelectGetSetState_SetState_SelectTool_InputEmulation_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectGetSetState_SetState_SelectTool_InputEmulation")
        # Perform actions when entering Notready_SelectGetSetState_SetState_SelectTool_InputEmulation
        pass
    
    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectGetSetState_SetState_SelectTool_InputEmulation")
        # Perform actions when exiting Notready_SelectGetSetState_SetState_SelectTool_InputEmulation
        pass

class LogDone_Callback(StateCallback):
    def __init__(self) -> None:
        super().__init__()
        self.prepped = False

    def prep_log(self):
        # Read the file's content
        with open(os.path.join(os.environ.get("INPUT_DIR"), os.environ.get("PERSISTENCE_DIR"), os.environ.get("LOG_FILE")), 'r') as file:
            lines = file.readlines()

        # Filter out the unwanted line
        filtered_lines = [line for line in lines if not ("*Nothing here yet*" in line.strip())]

        # Write the modified content back to the file
        with open(os.path.join(os.environ.get("INPUT_DIR"), os.environ.get("PERSISTENCE_DIR"), os.environ.get("LOG_FILE")), 'w') as file:
            file.writelines(filtered_lines)

        return True

    def on_enter(self, csm, locals):
        print(f"Entering LogDone")
        # Perform actions when entering Done
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting LogDone")
        # Perform actions when exiting Done

        # Remove "*Nothing here yet*" if not already done
        if not self.prepped and locals.get("parsed_response")["action"]["_content"].lower().capitalize() == "Log":
            self.prepped = self.prep_log()

        if locals.get("parsed_response")["action"]["_content"].lower().capitalize() == "Log":
            with open(os.path.join(os.environ.get("INPUT_DIR"), os.environ.get("PERSISTENCE_DIR"), os.environ.get("LOG_FILE")), "a") as f:
                f.write(datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]: "))
                f.write(locals.get("parsed_response")["action"]["body"]["_content"] + "\n")

class Done_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Done")
        # Perform actions when entering Done
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Done")
        # Perform actions when exiting Done
        pass


class Notready_SelectDone_Callback(StateCallback):
    def on_enter(self, csm, locals):
        print(f"Entering Notready_SelectDone")
        # Perform actions when entering Done
        pass

    def on_exit(self, csm, locals):
        print(f"Exiting Notready_SelectDone")
        # Perform actions when exiting Done
        pass
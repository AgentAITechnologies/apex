import anthropic
import os
import dotenv
import json
import re
from pprint import pprint
from copy import deepcopy

import inspect

from state_management import ConversationStateMachine
from parsing import *
import callbacks
from memory import Memory


dotenv.load_dotenv()


try:
    TERM_WIDTH = os.get_terminal_size().columns
    print(f"\n[main] TERM_WIDTH: {TERM_WIDTH}")
except OSError:
    TERM_WIDTH = 80
    print(f"\n[main] TERM_WIDTH: {TERM_WIDTH}")


CLI_STRS = {
    "init": "What would you like me to do? > "
}



def main():
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    memory: Memory = Memory()

    with open(os.path.join(os.environ.get("INPUT_DIR"), "states.json")) as file:
        state_data = json.load(file)

    with open(os.path.join(os.environ.get("INPUT_DIR"), "transitions.json")) as file:
        transition_data = json.load(file)

    csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='Start')
    csm.visualize()

    csm.transition("Selectready", locals=locals())

    task = input(CLI_STRS["init"])

    memory.global_frmt.update({"task": task})

    prev_response = {}


    # TODO: Modify to support new Markdown parsing scheme
    i = 0
    while csm.current_state.get_hpath() != "Done":
        print("-"*16)
        print(f"\n[main] state {i}\n")
        csm.print_current_state()

        memory.load_state_prompts(csm.current_state.get_hpath())

        dynamic_frmt = csm.current_state.frmt.copy()
        dynamic_frmt.update(prev_response)
        dynamic_frmt.update(memory.persistence)
        dynamic_frmt.update(memory.build_general_ctxt())

        formatted_system = memory.get_formatted_system(dynamic_frmt=dynamic_frmt)
        formatted_messages = memory.get_formatted_messages(dynamic_frmt=dynamic_frmt)

        print(f"\nformatted_system:\n")
        print(formatted_system)
        print(f"\nformatted_messages:\n")
        pprint(formatted_messages)
        print()
            
        response = csm.current_state.llm_call(client, formatted_system, formatted_messages)

        memory.add_msg_obj(response)

        parsed_response = parse_response(response)
        pprint(parsed_response, width=TERM_WIDTH)

        
        if "action" in parsed_response:
            csm.transition(parsed_response["action"]["_content"].lower().capitalize(), locals())
        elif "code_block" in parsed_response:
            csm.transition("Execute", locals())
        elif "problems" in parsed_response:
            csm.transition("Problemsidentified", locals())

        prev_response = {
            "previous_response": parsed_response,
        }
        
        i += 1



if __name__ == "__main__":
    main()
import anthropic
import os
import dotenv
import json
import re

import inspect

from state_management import ConversationStateMachine

from callbacks import exec_callbacks


dotenv.load_dotenv()



CLI_STRS = {
    "init": "What would you like me to do? > "
}

def parse_response(message):
    if message.content[0].type == "text":
        try:
            return json.loads(message.content[0].text)

        except json.JSONDecodeError as e:
            print("Not JSON")
            return message.content[0].text

    else:
        print(f"[parse_message] message.content[0].type was not text: {message.content[0].type}")
        return None



def main():
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )
    

    with open(os.path.join(os.environ.get("INPUT_DIR"), "states.json")) as file:
        state_data = json.load(file)

    with open(os.path.join(os.environ.get("INPUT_DIR"), "transitions.json")) as file:
        transition_data = json.load(file)

    with open(os.path.join(os.environ.get("INPUT_DIR"), "global_frmt.json")) as file:
        global_frmt = json.load(file)


    csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='start')
    csm.transition("selectready")

    task = input(CLI_STRS["init"])

    global_frmt.update({"task": task})


    i = 0
    while csm.current_state.get_hierarchy_path() != "done":
        print(f"\n[main] state {i}")
        csm.print_current_state()

        exec_callbacks(csm.current_state.get_hpath(), "before", locals=locals())

        csm.current_state.configure_llm_call(frmt_update=global_frmt)
        response = csm.current_state.llm_call(client)

        parsed_response = parse_response(response)
        print(f"parsed_response:\n{parsed_response}")

        # assumes each csm.transition() is called if an after callback is defined
        had_after_callbacks = exec_callbacks(csm.current_state.get_hpath(), "after", locals=locals())

        # default transition 
        if not had_after_callbacks and isinstance(parsed_response, dict):
            if "action" in parsed_response:
                csm.transition(parsed_response["action"].lower()).update_frmt(parsed_response)
        
        i += 1



if __name__ == "__main__":
    main()
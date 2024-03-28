import anthropic
import os
import dotenv
import json
import re

from execution_management import exec_python, extract_python
from state_management import ConversationStateMachine


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

        if csm.current_state.get_hierarchy_path() == "ready_select-done":
            results = csm.build_action_results()

            action_results_str = "You took these actions to accomplish the task:\n"
            action_results_str += json.dumps(results, indent=4)

            csm.current_state.update_frmt({"action_results": results})
            csm.current_state.update_frmt({"action_results_str": action_results_str}, recursive=False)

            print(action_results_str)

        csm.current_state.configure_llm_call(frmt_update=global_frmt)

        response = csm.current_state.llm_call(client)

        parsed_response = parse_response(response)
        print(f"parsed_response:\n{parsed_response}")

        if isinstance(parsed_response, str) and "python" in parsed_response.lower() and "compose-python" in csm.current_state.get_hierarchy_path():
            code = extract_python(parsed_response)
            stdout, stderr = exec_python(code)

            print(f"[main] Python script execution results for task \"{task}\":\nstdout:\n{stdout}\nstderr:\n{stderr}")

            frmt_update = {
                "result": {
                    "action": "execute python",
                    "code": code,
                    "output": {"stdout": stdout, "stderr": stderr}
                }
            }

            csm.transition("execute").update_frmt(frmt_update)

        if isinstance(parsed_response, dict):
            if "action" in parsed_response:
                csm.transition(parsed_response["action"].lower()).update_frmt(parsed_response)
        
        i += 1



if __name__ == "__main__":
    main()
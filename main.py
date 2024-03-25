import anthropic
import os
import dotenv
import json

from state_management import ConversationStateMachine


dotenv.load_dotenv()


CLI_STRS = {
    "init": "What would you like me to do? > "
}

def parse_message(message):
    if message.content[0].type == "text":
        try:
            return json.loads(message.content[0].text)

        except json.JSONDecodeError as e:
            print("Invalid JSON:")
            print(f"Error: {str(e)}")
            return None

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


    csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='start')
    csm.transition("selectready")


    task = input(CLI_STRS["init"])

    common_frmt = {
        "task": task
    }

    i = 0
    done = False

    while not done:
        print(f"\n[main] state {i}")
        csm.print_current_state()

        csm.current_state.frmt = common_frmt

        if "select-tool" in csm.current_state.get_hierarchy_path() and "select-ready" in csm.state_history[-1].get_hierarchy_path():
            csm.current_state.frmt.update({
                "state_history_str": "You have determined that you do not need additional information before completing the task, such as asking the user a question to better understand your task or getting more context about the system's current state, and do not need to configure the system into a specific state to perform the task."
            })

        input_messages = csm.current_state.build_messages()
        system_prompt = csm.current_state.build_system()

        if i >= 2: # debug (this code only handles start -> select-ready -> select-tool -> STOP)
            return
        
        message = client.messages.create(
            model=os.environ.get("MODEL"),
            max_tokens=4000,
            temperature=0,
            system=system_prompt,
            messages=input_messages
        )
        
        message_json = parse_message(message)

        if message_json != None:
            csm.transition(message_json["action"].lower())
        
        i += 1



if __name__ == "__main__":
    main()
import anthropic
import os
import dotenv
import json

from state_management import ConversationState, ConversationStateMachine



dotenv.load_dotenv()


CLI_STRS = {
    "init": "What would you like me to do? > "
}

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

    test_frmt = {
        "task": task
    }

    test_messages = [{
            "role":  csm.current_state.messages[0]["role"],
            "content": [{
                    "type": csm.current_state.messages[0]["content"][0]["type"],
                    "text": csm.current_state.messages[0]["content"][0]["text"].format(**test_frmt)
                }]
        }]
    
    test_system = csm.current_state.system.format(**test_frmt)

    message = client.messages.create(
        model=os.environ.get("MODEL"),
        max_tokens=4000,
        temperature=0,
        system=test_system,
        messages=test_messages
    )

    if message.content[0].type == "text":
        try:
            data = json.loads(message.content[0].text)
            print(data)
        except json.JSONDecodeError as e:
            print("Invalid JSON:")
            print(f"Error: {str(e)}")



if __name__ == "__main__":
    main()
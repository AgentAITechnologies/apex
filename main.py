import anthropic
import os
import dotenv


dotenv.load_dotenv()

CLI_ASKTASK_STR = "What would you like me to do? > "


task = input(CLI_ASKTASK_STR)

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

message = client.messages.create(
    model=os.environ.get("MODEL"),
    max_tokens=4000,
    temperature=0,
    system="You are a helpful agent that controls a desktop PC who takes actions on behalf of the computer's user. You have access to a Python interpreter, a shell for the underlying system, the screen (by taking and viewing screenshots), and a keyboard and mouse emulator (via the Python interpreter). You may determine the current state of the system programmatically and/or by viewing a screenshot. A user is now asking you to take action on their behalf. It is now your job to determine if you need additional information to complete the task. If you need to ask the user a question to better understand your task, respond with a JSON object containing the property \"question\" that contains a sub-property \"reason\" that contains the reason why asking the user a question would be most helpful. If you need more context about the system's current state and it can best be attained programmatically through the Python interpreter, respond with a JSON object containing the property \"python\" that contains a sub-property \"reason\" that contains the reason why executing Python code to get the required state information would be most helpful, and another sub-property \"privileged\" set to \"true\" for scripts that require privilege execution and set to \"false\" otherwise. If a PowerShell command would be most effective to get the required state, respond with a JSON object containing the property \"powershell\" that contains a sub-property \"reason\" that contains the reason why executing a PowerShell script to get the required state information would be most helpful, and another sub-property \"privileged\" set to \"true\" for scripts that require privilege execution and set to \"false\" otherwise. If a current screenshot would be most effective to get the required state, respond with a JSON object containing the property \"screenshot\" that contains a sub-property \"reason\" that contains the reason getting a screenshot would be most helpful. If you believe action may be taken to accomplish the user's goal without needing to know anything additional from the user or the system, where that action may be taken by either executing a Python script, PwoerShell script, or mouse and keyboard emulation, respond with a JSON object containing the property \"ready\" that contains a sub-property \"reason\" that contains the reason you feel ready to perform the action.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": task
                }
            ]
        }
    ]
)

print(message.content)
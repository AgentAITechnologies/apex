from anthropic import Anthropic
import os

from rich import print

def llm_call(client: Anthropic, formatted_system, formatted_messages, stop_sequences, temperature):
    message = client.messages.create(
        model=os.environ.get("MODEL"),
        max_tokens=4000,
        temperature=temperature,
        system=formatted_system,
        messages=formatted_messages,
        stop_sequences=stop_sequences,
    )
    
    return message

def llm_turn(client: Anthropic, prompts, stop_sequences, temperature):
    llm_response = llm_call(client, prompts['system'], prompts['messages'], stop_sequences, temperature)
    print(f"llm_response: {llm_response}")

    return llm_response.content[0].text
from typing import Iterable, Optional

import os
import backoff

from utils.custom_types import Message, PromptsDict

from anthropic import Anthropic
from anthropic.types import Message as AnthropicMessage
from anthropic.types import ContentBlock as AnthropicContentBlock
from anthropic.types import TextBlock as AnthropicTextBlock
from anthropic.types import MessageParam as AnthropicMessageParam
from anthropic import RateLimitError, InternalServerError

from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion as OpenAIChatCompletion
from openai.types.chat.chat_completion_message import ChatCompletionMessage as OpenAIChatCompletionMessage
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_user_message_param import ChatCompletionUserMessageParam
from openai.types.chat.chat_completion_assistant_message_param import ChatCompletionAssistantMessageParam
from openai.types.chat.chat_completion_system_message_param import ChatCompletionSystemMessageParam
from openai.types.chat.chat_completion import Choice

from rich import print

from utils.enums import Role


PRINT_PREFIX = "[bold][LLM][/bold]"


def cast_messages_anthropic(messages: Iterable[Message]) -> list[AnthropicMessageParam]:
    casted_messages = []
    for message in messages:
        if message['role'] == 'user' or message['role'] == 'assistant':
            casted_messages.append(AnthropicMessageParam(role=message['role'], content=message['content']))
        else:
            print(f"[red][bold]{PRINT_PREFIX} invalid message role: {message['role']}[/red][/bold]")
            exit(1)

    return casted_messages

def on_backoff_anthropic(details):
    print(f"[red][bold]{PRINT_PREFIX} Anthropic API error - backing off {details['wait']:0.1f} seconds after {details['tries']} tries\n{details['exception']}[/bold][/red]")

@backoff.on_exception(backoff.expo,
                      (RateLimitError, InternalServerError),
                      max_tries=5,
                      on_backoff=on_backoff_anthropic)
def llm_call_anthropic(client: Anthropic, system: str, messages: list[Message], stop_sequences: list[str], temperature: float) -> AnthropicMessage:
    model = os.environ.get("ANTHROPIC_MODEL")
    if model is None:
        print(f"[red][bold]{PRINT_PREFIX} ANTHROPIC_MODEL not set[/bold][/red]")
        exit(1)
    
    anthropic_messages = cast_messages_anthropic(messages)
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=temperature,
            system=system,
            messages=anthropic_messages,
            stop_sequences=stop_sequences,
        )
    except RateLimitError as e:
        print(f"[red][bold]{PRINT_PREFIX} Anthropic RateLimitError: {e}[/red][/bold]")
        exit(1)
    except InternalServerError as e:
        print(f"[red][bold]{PRINT_PREFIX} Anthropic InternalServerError: {e}[/red][/bold]")
        exit(1)
    
    return message

def cast_messages_openai(messages: Iterable[Message]) -> list[ChatCompletionMessageParam]:
    casted_messages = []
    for message in messages:
        if message['role'] == 'user':
            casted_messages.append(ChatCompletionUserMessageParam(role='user', content=message['content']))
        elif message['role'] == 'assistant':
            casted_messages.append(ChatCompletionAssistantMessageParam(role='assistant', content=message['content']))
        elif message['role'] == 'system':
            casted_messages.append(ChatCompletionSystemMessageParam(role='system', content=message['content']))
        else:
            print(f"[red][bold]{PRINT_PREFIX} invalid message role: {message['role']}[/red][/bold]")
            exit(1)

    return casted_messages

def llm_call_openai(client: OpenAI, system: str, messages: list[Message], stop_sequences: list[str], temperature: float, n: int) -> OpenAIChatCompletion:
    model = os.environ.get("OPENAI_MODEL")
    if model is None:
        print(f"[red][bold]{PRINT_PREFIX} OPENAI_MODEL not set[/bold][/red]")
        exit(1)
    
    openai_system: Message = {'role': Role.SYSTEM.value, 'content': system}
    openai_messages: list[Message] = [openai_system] + messages

    casted_messages = cast_messages_openai(openai_messages)

    response = client.chat.completions.create(
        model=model,
        messages=casted_messages,
        stop=stop_sequences,
        temperature=temperature,
        n=n
    )

    return response

def llm_turn(client: Anthropic | OpenAI, prompts: PromptsDict, stop_sequences: list[str], temperature: float) -> str:
    return llm_turns(client, prompts, stop_sequences, temperature, n=1)[0]

def llm_turns(client: Anthropic | OpenAI, prompts: PromptsDict, stop_sequences: list[str], temperature: float, n) -> list[str]:
    if isinstance(prompts['system'], str) and isinstance(prompts['messages'], list):
        texts: list[str] = []

        if isinstance(client, Anthropic):
            for i in range(n):
                llm_response = llm_call_anthropic(client, prompts['system'], prompts['messages'], stop_sequences, temperature)

                print(f"{PRINT_PREFIX} llm_response[{i}]: {llm_response}")

                anthropic_content: AnthropicContentBlock = llm_response.content[0]

                if isinstance(anthropic_content, AnthropicTextBlock):
                    text: str = anthropic_content.text
                    texts.append(text)

        elif isinstance(client, OpenAI):
            llm_response = llm_call_openai(client, prompts['system'], prompts['messages'], stop_sequences, temperature, n)

            print(f"{PRINT_PREFIX} llm_response[0:{n}]: {llm_response}")

            choices: list[Choice] = llm_response.choices

            for choice in choices:
                message: OpenAIChatCompletionMessage = choice.message
                openai_content: Optional[str] = message.content
                
                if openai_content is not None:
                    texts.append(openai_content)
                else:
                    print(f"[red][bold]{PRINT_PREFIX} empty openai_content: {llm_response}[/bold][/red]")
                    exit(1)    

        return texts
    
    else:
        print(f"""[red][bold]{PRINT_PREFIX} expexted prompts['system'] to be str and prompts['messages'] to be list,
got {type(prompts['system'])} and {type(prompts['messages'])} respectively instead[/bold][/red]""")
        exit(1)
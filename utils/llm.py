import time
from typing import Iterable, Optional

import os
import backoff

import concurrent.futures

from utils.constants import CLIENT_VERSION
from utils.custom_exceptions import LLMAPIInternalServerError, LLMAPIRateLimitError
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
            error_message = f"{PRINT_PREFIX} invalid message role: {message['role']}"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)

    return casted_messages

def on_backoff_anthropic(details):
    print(f"[red][bold]{PRINT_PREFIX} Anthropic API error - backing off {details['wait']:0.1f} seconds after {details['tries']} tries\n{details['exception']}[/bold][/red]")

@backoff.on_exception(backoff.expo,
                      (RateLimitError, InternalServerError),
                      max_tries=10,
                      on_backoff=on_backoff_anthropic)
def llm_call_anthropic(client: Anthropic, system: str, messages: list[Message], stop_sequences: list[str], temperature: float, max_tokens: int) -> AnthropicMessage:
    model = os.environ.get("ANTHROPIC_MODEL")
    if model is None:
        error_message = f"{PRINT_PREFIX} ANTHROPIC_MODEL not set"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)
    
    anthropic_messages = cast_messages_anthropic(messages)
    
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=anthropic_messages,
            stop_sequences=stop_sequences,
        )
    except RateLimitError as e:
        error_message = f"{PRINT_PREFIX} Anthropic RateLimitError: {e}"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise LLMAPIRateLimitError(error_message)
    except InternalServerError as e:
        error_message = f"{PRINT_PREFIX} Anthropic InternalServerError: {e}"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise LLMAPIInternalServerError(error_message)
    
    return message

def llm_call_anthropic_futures_to_texts(texts, futures):
    for i, future in enumerate(futures):
        try:
            llm_response = future.result()
            print(f"{PRINT_PREFIX} llm_response[{i}]: {llm_response}")

            anthropic_content: AnthropicContentBlock = llm_response.content[0]
            if isinstance(anthropic_content, AnthropicTextBlock):
                text: str = anthropic_content.text
                texts[i] = text
            else:
                texts[i] = None
                                
        except Exception as exc:
            print(f"{PRINT_PREFIX} Error obtaining future result: {exc}")
            texts[i] = None

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
            error_message = f"{PRINT_PREFIX} invalid message role: {message['role']}"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)

    return casted_messages

def llm_call_openai(client: OpenAI, system: str, messages: list[Message], stop_sequences: list[str], temperature: float, n: int, max_tokens: int) -> OpenAIChatCompletion:
    model = os.environ.get("OPENAI_MODEL")
    if model is None:
        error_message = f"{PRINT_PREFIX} OPENAI_MODEL not set"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)
    
    openai_system: Message = {'role': Role.SYSTEM.value, 'content': system}
    openai_messages: list[Message] = [openai_system] + messages

    casted_messages = cast_messages_openai(openai_messages)

    response = client.chat.completions.create(
        model=model,
        messages=casted_messages,
        stop=stop_sequences,
        temperature=temperature,
        n=n,
        max_tokens=max_tokens
    )

    return response

def llm_turn(client: Anthropic | OpenAI, prompts: PromptsDict, stop_sequences: list[str], temperature: float, max_tokens: int = 4000) -> str:
    return llm_turns(client, prompts, stop_sequences, temperature, n=1, max_tokens=max_tokens)[0]

def llm_turns(client: Anthropic | OpenAI, prompts: PromptsDict | list[PromptsDict], stop_sequences: list[str], temperature: float, n: Optional[int], max_tokens: int = 4000) -> list[str]:    
    if isinstance(prompts, dict):
        if not isinstance(n, int) or n < 1:
            error_message = f"{PRINT_PREFIX} n must be a positive integer if prompts is a dictionary"
            print(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)
        
        if isinstance(prompts['system'], str) and isinstance(prompts['messages'], list):
            texts: list[Optional[str]] = [None] * n

            if isinstance(client, Anthropic):
                with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
                    futures = []

                    for i in range(n):
                        futures.append(
                            executor.submit(
                                llm_call_anthropic, 
                                client, 
                                prompts['system'], 
                                prompts['messages'], 
                                stop_sequences, 
                                temperature,
                                max_tokens=max_tokens
                            )
                        )

                        # if i < n - 1:  # Don't delay after the last submission
                            # time.sleep(0.1)
                    
                    concurrent.futures.wait(futures)

                    llm_call_anthropic_futures_to_texts(texts, futures)

            elif isinstance(client, OpenAI):
                llm_response = llm_call_openai(client, prompts['system'], prompts['messages'], stop_sequences, temperature, n, max_tokens)

                print(f"{PRINT_PREFIX} llm_response[0:{n}]: {llm_response}")

                choices: list[Choice] = llm_response.choices

                for choice in choices:
                    message: OpenAIChatCompletionMessage = choice.message
                    openai_content: Optional[str] = message.content
                    
                    if openai_content is not None:
                        texts.append(openai_content)
                    else:
                        error_message = f"{PRINT_PREFIX} empty openai_content: {llm_response}"
                        print(f"[red][bold]{error_message}[/bold][/red]")
                        raise ValueError(error_message)

            result = [text for text in texts if text is not None]
            return result
            
        else:
            error_message = f"""
    {PRINT_PREFIX} expected prompts['system'] to be str and prompts['messages'] to be list,
    got {type(prompts['system'])} and {type(prompts['messages'])} respectively instead
    """.strip()

            print(f"[red][bold]{error_message}[/bold][/red]")
            raise TypeError(error_message)
        
    elif isinstance(prompts, list):
        n = len(prompts)

        for prompt in prompts:
            if not (isinstance(prompt['system'], str) and isinstance(prompt['messages'], list)):
                error_message = f"""
{PRINT_PREFIX} expected prompt['system'] to be str and prompt['messages'] to be list,
got {type(prompt['system'])} and {type(prompt['messages'])} respectively instead
""".strip()
                print(f"[red][bold]{error_message}[/bold][/red]")
                raise TypeError(error_message)
            
        texts: list[Optional[str]] = [None] * n

        if isinstance(client, Anthropic):
            with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:

                futures = []
                for i in range(n):
                    future = executor.submit(
                        llm_call_anthropic,
                        client,
                        prompts[i]['system'],  # type: ignore
                        prompts[i]['messages'],  # type: ignore
                        stop_sequences,
                        temperature,
                        max_tokens=max_tokens
                    )
                    futures.append(future)
                    
                    # if i < n - 1:  # Don't delay after the last submission
                        # time.sleep(0.1)
                    
                concurrent.futures.wait(futures)
                llm_call_anthropic_futures_to_texts(texts, futures)

        elif isinstance(client, OpenAI):
            raise NotImplementedError(f"OpenAI not supported for prompt list paralellization in this version ({CLIENT_VERSION})")

        result = [text for text in texts if text is not None]
        return result
            
    else:
        error_message = f"{PRINT_PREFIX} expected prompts to be dict or list, got {type(prompts)} instead"
        print(f"[red][bold]{error_message}[/bold][/red]")
        raise TypeError(error_message)
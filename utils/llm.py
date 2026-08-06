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

from rich import print as rprint
from utils.console_io import debug_print as dprint

from utils.enums import Role


PRINT_PREFIX = "[bold][LLM][/bold]"


def cast_messages_anthropic(messages: Iterable[Message]) -> list[AnthropicMessageParam]:
    casted_messages = []
    for message in messages:
        if message['role'] == 'user' or message['role'] == 'assistant':
            casted_messages.append(AnthropicMessageParam(role=message['role'], content=message['content']))
        else:
            error_message = f"{PRINT_PREFIX} invalid message role: {message['role']}"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)

    return casted_messages

def on_backoff_anthropic(details):
    rprint(f"[red][bold]{PRINT_PREFIX} Anthropic API error - backing off {details['wait']:0.1f} seconds after {details['tries']} tries\n{details['exception']}[/bold][/red]")

@backoff.on_exception(backoff.expo,
                      (RateLimitError, InternalServerError),
                      max_tries=10,
                      on_backoff=on_backoff_anthropic)
def llm_call_anthropic(client: Anthropic, system: str, messages: list[Message], stop_sequences: list[str], temperature: float, max_tokens: Optional[int] = 8192) -> AnthropicMessage:
    model = os.environ.get("ANTHROPIC_MODEL")
    if model is None:
        error_message = f"{PRINT_PREFIX} ANTHROPIC_MODEL not set"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)
    
    anthropic_messages = cast_messages_anthropic(messages)
    
    effective_max_tokens = max_tokens if max_tokens is not None else 8192

    try:
        message = client.messages.create(
            model=model,
            max_tokens=effective_max_tokens,
            temperature=temperature,
            system=system,
            messages=anthropic_messages,
            stop_sequences=stop_sequences,
        )
    except RateLimitError as e:
        error_message = f"{PRINT_PREFIX} Anthropic RateLimitError: {e}"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise LLMAPIRateLimitError(error_message)
    except InternalServerError as e:
        error_message = f"{PRINT_PREFIX} Anthropic InternalServerError: {e}"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise LLMAPIInternalServerError(error_message)
    
    return message

def llm_call_anthropic_futures_to_texts(texts, futures):
    for i, future in enumerate(futures):
        try:
            llm_response = future.result()
            dprint(f"{PRINT_PREFIX} llm_response[{i}]: {llm_response}")

            anthropic_content: AnthropicContentBlock = llm_response.content[0]
            if isinstance(anthropic_content, AnthropicTextBlock):
                text: str = anthropic_content.text
                texts[i] = text
            else:
                texts[i] = None
                                
        except Exception as exc:
            rprint(f"{PRINT_PREFIX} [red][bold]Error obtaining future result: {exc}[/bold][/red]")
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
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)

    return casted_messages

def llm_call_openai(client: OpenAI, system: str, messages: list[Message], stop_sequences: list[str], temperature: float, n: int, max_tokens: Optional[int] = None) -> OpenAIChatCompletion:
    model = os.environ.get("OPENAI_MODEL")
    if model is None:
        error_message = f"{PRINT_PREFIX} OPENAI_MODEL not set"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise KeyError(error_message)
    
    openai_system: Message = {'role': Role.SYSTEM.value, 'content': system}
    openai_messages: list[Message] = [openai_system] + messages

    casted_messages = cast_messages_openai(openai_messages)

    kwargs = {
        "model": model,
        "messages": casted_messages,
        "stop": stop_sequences,
        "temperature": temperature,
        "n": n,
    }

    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    response = client.chat.completions.create(**kwargs)

    return response

def llm_turn(client: Anthropic | OpenAI, prompts: PromptsDict, stop_sequences: list[str], temperature: float, max_tokens: Optional[int] = None) -> str:
    return llm_turns(client, prompts, stop_sequences, temperature, n=1, max_tokens=max_tokens)[0]

def llm_turns(client: Anthropic | OpenAI, prompts: PromptsDict | list[PromptsDict], stop_sequences: list[str], temperature: float, n: Optional[int], max_tokens: Optional[int] = None) -> list[str]:    
    if isinstance(prompts, dict):
        if not isinstance(n, int) or n < 1:
            error_message = f"{PRINT_PREFIX} n must be a positive integer if prompts is a dictionary"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)
        
        if isinstance(prompts['system'], str) and isinstance(prompts['messages'], list):
            texts: list[Optional[str]] = []

            if isinstance(client, Anthropic):
                texts = [None] * n
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

                    concurrent.futures.wait(futures)

                    llm_call_anthropic_futures_to_texts(texts, futures)

            elif isinstance(client, OpenAI):
                max_n = int(os.environ.get("OPENAI_MAX_N", "1"))

                # Split N into sequential chunks of size <= MAX_N (e.g. N=5, MAX_N=4 -> [4, 1])
                chunks = []
                remaining = n
                while remaining > 0:
                    current_chunk = min(remaining, max_n)
                    chunks.append(current_chunk)
                    remaining -= current_chunk

                # Sequentially make requests for each chunk size
                for chunk_n in chunks:
                    try:
                        llm_response = llm_call_openai(
                            client,
                            prompts['system'],  # type: ignore
                            prompts['messages'],  # type: ignore
                            stop_sequences,
                            temperature,
                            chunk_n,
                            max_tokens
                        )
                        dprint(f"{PRINT_PREFIX} llm_response (n={chunk_n}): {llm_response}")
                        if llm_response.choices:
                            for choice in llm_response.choices:
                                if choice.message.content is not None:
                                    texts.append(choice.message.content)
                                else:
                                    error_message = f"{PRINT_PREFIX} empty openai_content: {llm_response}"
                                    rprint(f"[red][bold]{error_message}[/bold][/red]")
                        else:
                            error_message = f"{PRINT_PREFIX} empty openai choices: {llm_response}"
                            rprint(f"[red][bold]{error_message}[/bold][/red]")
                    except Exception as exc:
                        rprint(f"{PRINT_PREFIX} [red][bold]Error during API call for chunk n={chunk_n}: {exc}[/bold][/red]")

            result = [text for text in texts if text is not None]
            return result
            
        else:
            error_message = f"""
    {PRINT_PREFIX} expected prompts['system'] to be str and prompts['messages'] to be list,
    got {type(prompts['system'])} and {type(prompts['messages'])} respectively instead
    """.strip()

            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise TypeError(error_message)
        
    elif isinstance(prompts, list):
        n = len(prompts)

        for prompt in prompts:
            if not (isinstance(prompt['system'], str) and isinstance(prompt['messages'], list)):
                error_message = f"""
{PRINT_PREFIX} expected prompt['system'] to be str and prompt['messages'] to be list,
got {type(prompt['system'])} and {type(prompt['messages'])} respectively instead
""".strip()
                rprint(f"[red][bold]{error_message}[/bold][/red]")
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
                    
                concurrent.futures.wait(futures)
                llm_call_anthropic_futures_to_texts(texts, futures)

        elif isinstance(client, OpenAI):
            with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
                futures = []
                for i in range(n):
                    future = executor.submit(
                        llm_call_openai,
                        client,
                        prompts[i]['system'],  # type: ignore
                        prompts[i]['messages'],  # type: ignore
                        stop_sequences,
                        temperature,
                        1,
                        max_tokens
                    )
                    futures.append(future)

                concurrent.futures.wait(futures)

                for i, future in enumerate(futures):
                    try:
                        llm_response = future.result()
                        dprint(f"{PRINT_PREFIX} llm_response[{i}]: {llm_response}")
                        texts[i] = llm_response.choices[0].message.content
                    except Exception as exc:
                        rprint(f"{PRINT_PREFIX} [red][bold]Error obtaining future result: {exc}[/bold][/red]")
                        texts[i] = None

        result = [text for text in texts if text is not None]
        return result
            
    else:
        error_message = f"{PRINT_PREFIX} expected prompts to be dict or list, got {type(prompts)} instead"
        rprint(f"[red][bold]{error_message}[/bold][/red]")
        raise TypeError(error_message)
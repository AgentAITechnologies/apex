from __future__ import annotations

import json

import os
import sounddevice as sd

from rich import print as rprint
from agents.message_queue import MessageQueue
from utils.console_io import debug_print as dprint

from agents.agent import Agent
from agents.memory import Memory
from agents.agent_manager.agent_manager import AgentManager
from agents.prompt_management import get_message, load_assistant_prefill, load_system_prompt
from agents.state_management import ConversationStateMachine

from utils.custom_exceptions import UIError
from utils.constants import DEFAULT_TEMP, FRIENDLY_COLOR
from utils.enums import Role
from utils.parsing import xmlstr2dict
from utils.tts import tts
from utils.llm import llm_turn

from anthropic import Anthropic


class UI(Agent):
    def __init__(self,
                 client: Anthropic,
                 prefix: str = "",
                 name: str = "UI",
                 description: str = 'Continually manages the interaction bewteen the user and yourself, the "Agent Manager". If you ever need to message the user, this agent will help you do so.',
                 tasks: list[dict] = [{"task": 'Communicate with the user'}],
                 agent_manager = None) -> None:
        
        if not agent_manager:
            error_message = f"{self.PRINT_PREFIX} AgentManager not provided"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise ValueError(error_message)
        
        super().__init__(client=client,
                         prefix=prefix,
                         name=name,
                         description=description,
                         tasks=tasks,
                         agent_manager=agent_manager)

        UI_DIR = os.environ.get("UI_DIR")
        if not UI_DIR:
            error_message = f"{self.PRINT_PREFIX} UI_DIR not set"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)

        INPUT_DIR = os.environ.get("INPUT_DIR")
        if not INPUT_DIR:
            error_message = f"{self.PRINT_PREFIX} INPUT_DIR not set"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)

        state_file_path = os.path.join(UI_DIR, INPUT_DIR, "states.json")

        try:
            with open(state_file_path) as file:
                state_data = json.load(file)
            dprint(f"{self.PRINT_PREFIX} loaded state_data")
        except FileNotFoundError:
            error_message = f"{self.PRINT_PREFIX} states.json not found at {state_file_path}"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise
        except json.JSONDecodeError:
            error_message = f"{self.PRINT_PREFIX} Error decoding JSON in states.json"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise

        transition_file_path = os.path.join(UI_DIR, INPUT_DIR, "transitions.json")

        try:
            with open(transition_file_path) as file:
                transition_data = json.load(file)
            dprint(f"{self.PRINT_PREFIX} loaded transition_data")
        except FileNotFoundError:
            error_message = f"{self.PRINT_PREFIX} transitions.json not found at {transition_file_path}"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise
        except json.JSONDecodeError:
            error_message = f"{self.PRINT_PREFIX} Error decoding JSON in transitions.json"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='Start', prefix=self.PRINT_PREFIX, owner_class_name="UI")

        self.memory = Memory(environ_path_key="UI_DIR", prefix=self.PRINT_PREFIX)
        self.message_queue = MessageQueue()
        self.agent_manager = AgentManager()
        self.agent_manager.register_agent(self)

        self.parsed_response = None
    
    # TODO: invoke ToT agents as separate threads/processes
    def run(self):
        rprint(f"[bold][{FRIENDLY_COLOR}]Welcome to [italic]APEX[/italic][/{FRIENDLY_COLOR}][/bold]\n")

        while self.csm.current_state.get_hpath() != "Exit":
            dprint(f"{self.PRINT_PREFIX} At: {self.csm.current_state.get_hpath()}")
                
            match self.csm.current_state.get_hpath():

                case "Start":
                    self.csm.transition("PrintUIMessage", locals())

                case "PrintUIMessage":
                    self.memory.prime_all_prompts(self.csm.current_state.get_hpath(), "UI_DIR", dynamic_metaprompt=" > ")

                    text = llm_turn(client=self.client,
                                    prompts={'system': self.memory.get_system_prompt(),
                                             'messages': self.memory.get_messages()},
                                    stop_sequences=["</output>"],
                                    temperature=0.7)
                    
                    self.memory.store_llm_response("<output>" + text + "</output>")

                    parsed_response = xmlstr2dict(text, self.client)
                    dprint(f"{self.PRINT_PREFIX} parsed_response:")
                    dprint(parsed_response)

                    rprint("\n[bold]" + parsed_response["response"] + "[/bold]\n")

                    if os.environ.get("USE_TTS") == "True":
                        tts(parsed_response["response"])

                    if "action" in parsed_response and parsed_response["action"]:
                        action = parsed_response["action"]

                        if action == "REST":
                            rprint(f"Exiting...")
                            sd.wait()
                            exit(0)
                        else:
                            self.csm.transition("AssignAction", locals())

                case "AssignAction":
                    if action:
                        dprint(f"{self.PRINT_PREFIX} action: {action}")

                        self.agent_manager.ipc("RouteAction", {"action": action})
                        self.csm.transition("PrintUIMessage", locals)
                    else:
                        error_message = f"{self.PRINT_PREFIX} no action to assign"
                        rprint(f"[red][bold]{error_message}[/bold][/red]")
                        raise UIError(error_message)

    # TODO: refactor into the event handling switch
    # TODO: generalize LLM interaction with
    #   structured_output = structured_llm_turn(client, memory, prompts, stop_seqs, temp)
    def handle_message(self):
        message = self.message_queue.pop(self.name)
        src_agent_name = message["src_agent_name"]
        message_text = message["text"]

        user_prompt_text = f"""
You have received a message from the agent: {src_agent_name}
<message>
{message_text}
</message>
If you can respond to the agent yourself without interacting with the user, say:
<output>
<agent_response>
{{YOUR_RESPONSE}}
</agent_response>
</output>
If you need to ask the user for some info before you can respond to the agent, say:
<output>
<user_message>
{{YOUR_MESSAGE_TO_THE_USER}}
</user_message>
</output>
If the request is not something the user would know, or is most appropriately handled by the agent itself (like asking for the current mouse pointer location, etc.), say:
<agent_response>
{{As the user's representative, this seems like a request best handled yourself.}}
</agent_response>
No matter what, don't give instructions, just respond to the request.
"""
        
        system_prompt = load_system_prompt("PrintUIMessage", "UI_DIR", {})
        user_prompt = get_message(Role.USER, user_prompt_text)
        assistant_prefill = load_assistant_prefill("<output>")

        text = llm_turn(client=self.client,
                        prompts={'system': system_prompt,
                                 'messages': self.memory.get_messages() + [user_prompt, assistant_prefill]},
                        stop_sequences=["</output>"],
                        temperature=DEFAULT_TEMP)
        
        self.memory.add_msg(user_prompt)
        self.memory.add_msg(assistant_prefill)
        self.memory.store_llm_response("<output>" + text + "</output>")  # Overwrites assistant_prefill

        parsed_response = xmlstr2dict(text, self.client)
        dprint(f"{self.PRINT_PREFIX} parsed_response:")
        dprint(parsed_response)

        if "agent_response" in parsed_response:
            self.agent_manager.ipc("RouteMessage", {"src_agent_name": self.name,
                                                    "dest_agent_name": src_agent_name,
                                                    "text": parsed_response["agent_response"]})
        elif "user_message" in parsed_response:
            rprint("\n[bold]" + parsed_response["user_message"] + "[/bold]", end="")
            user_response = input(" > ")
            rprint()

            self.memory.add_msg(get_message(Role.USER, user_response))
            self.memory.add_msg(get_message(Role.ASSISTANT, "Got it. I'll forward this to the source agent."))

            self.agent_manager.ipc("RouteMessage", {"src_agent_name": self.name,
                                                    "dest_agent_name": src_agent_name,
                                                    "text": user_response})



import os
import json
import platform
import random
from typing import Optional

from pynput import keyboard

import dotenv

from rich import print as rprint
import numpy as np

from agents.agent import Agent
from agents.state_management import ConversationStateMachine
from agents.execution_management.execution_management import CodeExecutor
from agents.prompt_management import load_system_prompt, load_user_prompt, get_msg

from agents.memory import Memory

from remote.experience import get_remote_experiences, stage_experience
from utils.context import get_platform_details
from utils.custom_exceptions import ExecError
from utils.enums import Role
from utils.custom_types import FeedbackDict, PromptsDict
from utils.parsing import dict2xml, xml2xmlstr, xmlstr2dict, extract_language_and_code, get_yes_no_input, remove_escape_key, format_nested_dict
from utils.llm import llm_turns
from utils.files import create_incrementing_directory
from utils.constants import CLIENT_VERSION, FRIENDLY_COLOR, get_env_constants
from utils.console_io import ProgressIndicator, debug_print as dprint

from anthropic import Anthropic


PLAN_COUNT = int(os.environ.get("PLAN_COUNT", "5"))
VOTER_COUNT = int(os.environ.get("VOTER_COUNT", "5"))
PROPOSAL_COUNT = int(os.environ.get("PROPOSAL_COUNT", "5"))

REMOTE_EXAMPLE_COUNT = int(os.environ.get("REMOTE_EXAMPLE_COUNT", "4"))

EVAL_CATEGORIES = ["correctness", "elegance", "understandability", "specificity", "overall"]

RESULT_FILENAME = "run_results.txt"

TEMP = 0.7


class ToT(Agent):
    PRINT_PREFIX = "[blue][bold][ToT][/bold][/blue]"

    def __init__(self, client: Anthropic, name: str, description: str, tasks: list[dict]) -> None:
        dotenv.load_dotenv()

        super().__init__(client=client,
                         prefix=self.PRINT_PREFIX,
                         name=name,
                         description=description,
                         tasks=tasks)

        self.client = client

        tot_dir, input_dir, output_dir = os.environ.get("TOT_DIR"), os.environ.get("INPUT_DIR"), os.environ.get("OUTPUT_DIR")
        if tot_dir is None:
            error_message = f"{self.PRINT_PREFIX} TOT_DIR environment variable not set (check .env)"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)
        if input_dir is None:
            error_message = f"{self.PRINT_PREFIX} INPUT_DIR environment variable not set (check .env)"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)
        if output_dir is None:
            error_message = f"{self.PRINT_PREFIX} OUTPUT_DIR environment variable not set (check .env)"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise KeyError(error_message)

        self.output_dir = os.path.join(tot_dir, output_dir)

        with open(os.path.join(tot_dir, input_dir, "states.json")) as file:
            state_data = json.load(file)
            dprint(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(tot_dir, input_dir, "transitions.json")) as file:
            transition_data = json.load(file)
            dprint(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path="Plan", prefix=self.PRINT_PREFIX, owner_class_name="ToT")

        self.code_executor = CodeExecutor(prefix=self.PRINT_PREFIX, owner_name=self.name)

        self.unified_memory = Memory(prefix=self.PRINT_PREFIX)
        self.unified_steps = []

        self.interrupt_listener = keyboard.Listener(on_press=self.on_press)
        self.interrupt_listener.start()

    def on_press(self, key):
        if key == keyboard.Key.esc:
            self.interrupted = True

    def check_interrupt(self):
        if self.interrupted:
            raise KeyboardInterrupt

    def run(self) -> None:
        self.trace = ""
        self.interrupted = False

        try:
            self.current_task: Optional[str] = xml2xmlstr(dict2xml(self.tasks[-1]))

            rprint(f"[yellow][bold]Press the escape key at any time to stop the agent[/bold][/yellow]")

            dprint(f"{self.PRINT_PREFIX} task:\n{self.current_task}")

            rprint(f"getting remote experiences", end="")
            with ProgressIndicator() as PI:
                REMOTE_EXPERIENCES = get_remote_experiences(target_vector_name="task",
                                                            target_vector_query=self.current_task,
                                                            limit=REMOTE_EXAMPLE_COUNT)
            
            # TODO: log this as an error depending on telemetry level
            if REMOTE_EXPERIENCES:
                rprint(f"[green]done[/green]")
            else:
                rprint(f"[red][bold]No remote examples found for the current task... this is suspicious.[/bold][/red]")

            self.log_dir = create_incrementing_directory(self.output_dir, f"{self.name}_")

            with open(os.path.join(self.log_dir, RESULT_FILENAME), 'w', errors="replace") as logfile:
                logfile.write(self.current_task + "\n")

            if self.csm.current_state.name == "Done":
                self.csm.transition("Plan", locals())

            # TODO: Use code from prior tasks assigned to this agent
            # A "here's what you've done so far" prompt section
            # (execution state should already be preserved in execution_context dict)

            self.step_num = 1
            self.open_step_tag = f"<step_{self.step_num}>"
            self.close_step_tag = f"</step_{self.step_num}>"

            self.unified_step: dict = {}

            while self.csm.current_state.name != "Done":
                self.check_interrupt()
                
                state_path = self.csm.current_state.get_hpath()
                                            
                match state_path:
                    
                    case "Plan":                        
                        system_prompt = load_system_prompt(state_path, "TOT_DIR", {"step_num": str(self.step_num),
                                                                                   "task": self.current_task,
                                                                                   "remote_examples": REMOTE_EXPERIENCES if REMOTE_EXPERIENCES else ""})
                        
                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                        "task": self.current_task,
                                                                                                        "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                        
                        start_seq = self.open_step_tag + "<plan>"
                        assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                        # re-implement set() optimizaiton after verifying it doesn't interfere with shuffling logic
                        rprint(f"planning", end="")
                        with ProgressIndicator() as PI:               
                            plan_candidates: list[str] = llm_turns(client=self.client,
                                                                    prompts={"system": system_prompt,
                                                                             "messages": messages},
                                                                    stop_sequences=["</plan>"],
                                                                    temperature=TEMP,
                                                                    n=PLAN_COUNT)
                        rprint(f"[green]done[/green]")
                        
                        self.unified_step['plan_candidates'] = plan_candidates

                        if len(self.unified_step['plan_candidates']) != 1:
                            self.csm.transition("PlanVote", locals())
                        else:
                            self.unified_step['best_plan'] = next(iter(self.unified_step['plan_candidates']))
                            self.csm.transition("Propose", locals())

                    case "PlanVote":
                        system_prompt = load_system_prompt(state_path, "TOT_DIR", {"step_num": str(self.step_num),
                                                                                   "task": self.current_task})
                        
                        start_seq = self.open_step_tag + "<evaluation>"
                        assistant_prompt = get_msg(Role.ASSISTANT, start_seq)
                        
                        plan_index_maps: list[list[int]] = []
                        prompts: list[PromptsDict] = []

                        for _ in range(VOTER_COUNT):
                            self.check_interrupt()

                            shuffled_indices, plan_candidates_str = self.format_candidates(plan_candidates)

                            user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                            "task": self.current_task,
                                                                                                            "plan_candidates_str": plan_candidates_str,
                                                                                                            "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                            messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                            prompts.append({"system": system_prompt,
                                            "messages": messages})
                            plan_index_maps.append(shuffled_indices)

                        rprint(f"voting", end="")
                        with ProgressIndicator() as PI:
                            plan_votes = llm_turns(client=self.client,
                                                    prompts=prompts,
                                                    stop_sequences=["</evaluation>"],
                                                    temperature=TEMP,
                                                    n=None)                
                        rprint(f"[green]done[/green]")

                        self.csm.transition("SumPlanVotes", locals())

                    case "SumPlanVotes":
                        plan_scores = self.reduce_scores(plan_candidates,
                                                         plan_votes,
                                                         plan_index_maps)
                        
                        self.csm.transition("ChoosePlan", locals())

                    case "ChoosePlan":
                        best_plan = self.choose(plan_candidates, plan_scores)
                        self.unified_step['best_plan'] = best_plan

                        self.csm.transition("Propose", locals())

                    case "Propose":
                        system_prompt = load_system_prompt(state_path, "TOT_DIR", {"task": self.current_task,
                                                                                   "remote_examples": REMOTE_EXPERIENCES if REMOTE_EXPERIENCES else ""})

                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                        "task": self.current_task,
                                                                                                        "plan": self.unified_step['best_plan'],
                                                                                                        "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                        
                        start_seq = self.open_step_tag + "<implementation>" + "\n" + "```python"
                        assistant_prompt = get_msg(Role.ASSISTANT, start_seq)
                        
                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                        # re-implement set() optimizaiton after verifying it doesn't interfere with shuffling logic
                        rprint(f"proposing implementations", end="")
                        with ProgressIndicator() as PI:
                            raw_proposals: list[str] = llm_turns(client=self.client,
                                                             prompts={"system": system_prompt,
                                                                      "messages": messages},
                                                             stop_sequences=["```"],
                                                             temperature=TEMP,
                                                             n=PROPOSAL_COUNT)
                        rprint(f"[green]done[/green]")
                            
                        proposal_candidates = ["```python" + raw_proposal + "```" for raw_proposal in raw_proposals]
                        
                        if len(proposal_candidates) != 1:
                            self.csm.transition("ProposeVote", locals())
                        else:
                            self.unified_step['best_proposition'] = next(iter(proposal_candidates))
                            self.csm.transition("Exec", locals())

                    case "ProposeVote":
                        system_prompt = load_system_prompt(state_path, "TOT_DIR", {"step_num": str(self.step_num),
                                                                                   "task": self.current_task})
                        
                        start_seq = self.open_step_tag + "<evaluation>"
                        assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                        proposal_index_maps: list[list[int]] = []
                        prompts: list[PromptsDict] = []
                        
                        for _ in range(VOTER_COUNT):
                            self.check_interrupt()

                            shuffled_indices, proposal_candidates_str = self.format_candidates(proposal_candidates)

                            user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                            "task": self.current_task,
                                                                                                            "plan": self.unified_step['best_plan'],
                                                                                                            "proposal_candidates_str": proposal_candidates_str,
                                                                                                            "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                            
                            messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]
                            
                            prompts.append({"system": system_prompt,
                                            "messages": messages})
                            proposal_index_maps.append(shuffled_indices)

                        rprint(f"voting on implementations", end="")
                        with ProgressIndicator() as PI:
                            proposal_votes = llm_turns(client=self.client,
                                                    prompts=prompts,
                                                    stop_sequences=["</evaluation>"],
                                                    temperature=TEMP,
                                                    n=None)
                        rprint(f"[green]done[/green]")

                        self.csm.transition("SumProposeVotes", locals())

                    case "SumProposeVotes":
                        proposal_scores = self.reduce_scores(proposal_candidates,
                                                             proposal_votes,
                                                             proposal_index_maps)

                        self.csm.transition("ChooseProposition", locals())

                    case "ChooseProposition":
                        best_proposition = self.choose(proposal_candidates, proposal_scores)
                        self.unified_step['best_proposition'] = best_proposition

                        self.csm.transition("Exec", locals())

                    case "Exec":
                        fenced_code = self.unified_step['best_proposition']
                        
                        parsed_code = extract_language_and_code(fenced_code)
                        if not parsed_code:
                            error_message = f"{self.PRINT_PREFIX} code not parsable:\n{fenced_code}"
                            rprint(f"[red][bold]{error_message}[/bold][/red]")
                            raise SyntaxError(error_message)
                        
                        language, code = parsed_code

                        rprint(f"Proposed code to execute:\n")
                        rprint(code.strip())

                        execute_code = get_yes_no_input(f"\nDo you want to execute this code?")

                        if execute_code:
                            self.code_executor.write_code_step_file(code, self.step_num)

                            stdout, stderr = self.code_executor.execute_code_step(self.step_num)

                            dprint(f"{self.PRINT_PREFIX} stdout:")
                            dprint(stdout)
                            dprint(f"{self.PRINT_PREFIX} stderr:")
                            dprint(stderr)

                            self.unified_step['output'] = stdout
                            self.unified_step['error'] = stderr
                        else:
                            rprint(f"{self.PRINT_PREFIX} Code execution skipped.")
                            self.unified_step['output'] = "Code execution skipped by user."
                            self.unified_step['error'] = ""

                        self.csm.transition("ExecVote", locals())

                    case "PlanErrorFix":
                        previous_step = self.unified_steps[-1]

                        frmt = {"step_num": str(self.step_num), "task": self.current_task, "error": previous_step['error'], "output": previous_step['output']}

                        system_prompt = load_system_prompt(state_path, "TOT_DIR", frmt)      
                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, frmt))
                        
                        start_seq = self.open_step_tag + "<plan>"
                        assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                        rprint(f"planning a fix", end="")
                        with ProgressIndicator() as PI:                   
                            plan_candidates: list[str] = llm_turns(client=self.client,
                                                            prompts={"system": system_prompt,
                                                                    "messages": messages},
                                                            stop_sequences=["</plan>"],
                                                            temperature=TEMP,
                                                            n=PLAN_COUNT)
                        rprint(f"[green]done[/green]")
                        
                        self.unified_step['plan_candidates'] = plan_candidates

                        if len(self.unified_step['plan_candidates']) != 1:
                            self.csm.transition("PlanVote", locals())
                        else:
                            self.unified_step['best_plan'] = next(iter(self.unified_step['plan_candidates']))
                            self.csm.transition("Propose", locals())

                    case "ExecVote":
                        system_prompt = load_system_prompt(state_path, "TOT_DIR", {"task": self.current_task})
                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                        "task": self.current_task,
                                                                                                        "plan": self.unified_step['best_plan'],
                                                                                                        "implementation": self.unified_step['best_proposition'],
                                                                                                        "output": self.unified_step['output'],
                                                                                                        "error": self.unified_step['error']}))
                        
                        start_seq = self.open_step_tag + "<evaluation>"
                        assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]
                        
                        rprint(f"voting on completion status", end="")
                        with ProgressIndicator() as PI:
                            exec_votes: list[str] = llm_turns(client=self.client,
                                                          prompts={"system": system_prompt,
                                                                   "messages": messages},
                                                          stop_sequences=["</evaluation>"],
                                                          temperature=TEMP,
                                                          n=VOTER_COUNT)
                        rprint(f"[green]done[/green]")
                        
                        self.unified_step['exec_vote_strs'] = exec_votes

                        self.csm.transition("SumExecVote", locals())

                    case "SumExecVote":
                        avg_yes_votes, avg_error_votes = self.reduce_scores_exec(self.unified_step)

                        self.next_step()

                        if avg_yes_votes > 0.5:
                            self.finalize_task()
                            self.csm.transition("Done", locals())
                        elif avg_error_votes > 0.5:
                            self.csm.transition("PlanErrorFix", locals())
                        else:
                            self.csm.transition("Plan", locals())

        except KeyboardInterrupt as e:
            rprint(f"{self.PRINT_PREFIX}[yellow][bold] Escape key pressed. Stopping the agent[/bold][/yellow]")
            self.finalize_task()

    def finalize_task(self) -> None:
        if self.current_task:
            self.code_executor.condense_code_files(self.current_task)
            
            PROVIDE_FEEDBACK = os.environ.get("PROVIDE_FEEDBACK") == "True"
            if PROVIDE_FEEDBACK:
                feedback = self.get_feedback()
                if feedback:
                    self.log_feedback(feedback)
                else:
                    rprint(f"[yellow][bold]{self.PRINT_PREFIX} No feedback to log[/bold][/yellow]")
            else:
                rprint(f"[yellow][bold]{self.PRINT_PREFIX} PROVIDE_FEEDBACK not set to \"True\" in .env - not collecting performance feedback[/bold][/yellow]")

            self.trace = ""
            self.current_task = None

            rprint(f"\n[green]task complete[/green]\n")
        else:
            error_message = f"{self.PRINT_PREFIX} Fatal: no task to finalize! Was run() invoked without assigning a task?"
            rprint(f"[red][bold]{error_message}[/bold][/red]")
            raise ExecError(error_message)   
    
    def next_step(self) -> None:
        unified_user_str, unified_assistant_str = self.step2str()
        self.log_step(unified_user_str, unified_assistant_str)

        unified_user_msg = get_msg(Role.USER, unified_user_str)
        unified_assistant_msg = get_msg(Role.ASSISTANT, unified_assistant_str)

        self.unified_memory.add_msg(unified_user_msg)
        self.unified_memory.add_msg(unified_assistant_msg)

        self.step_num += 1
        self.unified_steps.append(self.unified_step)
        self.unified_step: dict = {}
        self.open_step_tag = f"<step_{self.step_num}>"
        self.close_step_tag = f"</step_{self.step_num}>"

    def log_step(self, unified_user_str, unified_assistant_str) -> None:
        step_trace = ""

        step_trace += "\n"
        step_trace += self.open_step_tag + "\n"
        step_trace += "<user>"
        step_trace += unified_user_str + "</user>\n\n"
        step_trace += "<assistant>\n"
        step_trace += unified_assistant_str + "\n</assistant>\n"
        step_trace += self.close_step_tag + "\n"

        with open(os.path.join(self.log_dir, RESULT_FILENAME), 'a') as logfile:
            logfile.write(step_trace)

        self.trace += step_trace
    
    def log_feedback(self, feedback: FeedbackDict) -> None:
        LOGFILE_PATH = os.path.join(self.log_dir, RESULT_FILENAME)

        with open(LOGFILE_PATH, 'a') as logfile:
            logfile.write("\n")

            logfile.write("<human_feedback>\n")
            logfile.write(f"<success>{feedback['success']}</success>\n")
            logfile.write(f"<details>{feedback['details']}</details>\n")
            logfile.write(f"<elaboration>{feedback['elaboration']}</elaboration>\n")
            logfile.write("</human_feedback>\n")

        PROVIDE_FEEDBACK = os.environ.get("PROVIDE_FEEDBACK") == "True"
        if PROVIDE_FEEDBACK:

            rprint(f"\nsending feedback to experience platform", end="")
            with ProgressIndicator() as PI:

                with open(LOGFILE_PATH, 'r') as logfile:
                    logfile_text = logfile.read()

                raw_log: dict = xmlstr2dict(logfile_text, self.client)

                if "details" in raw_log:
                    details_str = f"<details>{raw_log['details']}</details>"
                else:
                    details_str = ""

                log = {
                    "agent_name": self.name,
                    "task": f"<task><description>{raw_log['task']}</description>{details_str}</task>",
                    "trace": self.trace,
                    "success": feedback['success'],
                    "feedback": feedback['details'],
                    "elaboration": feedback['elaboration'],
                    "client_version": CLIENT_VERSION,
                    "platform_details": get_platform_details(),
                    "os_family": platform.system()
                }

                dprint(log)

                response = stage_experience(log)

                if response:
                    dprint(f"{self.PRINT_PREFIX} response: {response.text}")
                else:
                    rprint(f"[red][bold]{self.PRINT_PREFIX} no response from experience submission![/bold][/red]")
        else:
            rprint(f"[yellow][bold]{self.PRINT_PREFIX} PROVIDE_FEEDBACK not set to \"True\" in .env - not sending feedback[/bold][/yellow]")

        if not get_env_constants()["LOCAL_LOGS"]:
            rprint(f"[yellow][bold]{self.PRINT_PREFIX} LOCAL_LOGS not set to \"True\" in .env - removing local log cache[/bold][/yellow]")
            os.remove(LOGFILE_PATH)

    # TODO: Summarize steps for easy human evaluation and pretty print the task
    def get_feedback(self) -> Optional[FeedbackDict]:
        feedback_intro = f"\n\nThe task:\n[white][bold]{format_nested_dict(xmlstr2dict(xml_string=self.current_task, client=self.client, depth=6), indent=4)}[/bold][/white]\n\n"
        
        rprint()
        
        if not self.interrupted:
            feedback_intro += "is believed to be complete according to your specifications, however this determination may have been in error.\n"
        else:
            feedback_intro += "was interrupted and will be classified as a failure.\n"

        feedback_intro += f"""
[{FRIENDLY_COLOR}][bold]Thank you again for providing feedback about the performance of this program.
Your contributions make this tool more effective for everyone.[/bold][/{FRIENDLY_COLOR}]
[{FRIENDLY_COLOR}]If you do not wish to be prompted for feedback in the future, simply disable this feature in your .env file.
[italic]You may also type 'c' at this prompt to not provide feedback for this particular task.[/italic][/{FRIENDLY_COLOR}]
"""
        rprint(feedback_intro)
        
        # TODO: implement one-off bypass ('c' for cancel)
        if not self.interrupted:
            success_prompt = "Was the task completed correctly, even if it took a while or involved self-correcting errors?"
            success = get_yes_no_input(success_prompt, with_cancel=True)
        else:
            success = False

        if success is None:
            rprint("[yellow][bold]Not profiving feedback for this task.[/bold][/yellow]")
            return None

        if success:
            details_prompt = """\nHow could future completions of this task be better?\n(e.g., more efficient, having fewer side effects, or being more closely aligned with your intentions)?
If you believe it was optimal, please indicate this."""
        else:
            details_prompt = "\nHow would you characterize this failure? Please be as specific as possible to help us be more helpful to you in the future."

        rprint(details_prompt, end=" > ")

        details = input()

        if self.interrupted:
            details = remove_escape_key(details)

        feedback: FeedbackDict = {
            "success": success,
            "details": details,
        }

        feedback['elaboration'] = self.clarify_feedback(feedback)

        return feedback
    
    # TODO: return the LLM's self-commentary
    def clarify_feedback(self, feedback: dict) -> Optional[str]:
        if self.current_task:
            with open(os.path.join(self.log_dir, RESULT_FILENAME), 'r') as logfile:
                system_prompt = load_system_prompt("ClarifyFeedback", "TOT_DIR", {'task': self.current_task,
                                                                                  'logfile': logfile.read()})
        else:
            error_message = "No task to clarify feedback for!"
            rprint(f"[red][bold]{self.PRINT_PREFIX} {error_message}[/bold][/red]")
            raise ValueError(error_message)
        
        user_prompt = get_msg(Role.USER, load_user_prompt("ClarifyFeedback", "TOT_DIR", None, {'success': feedback['success'],
                                                                                               'details': feedback['details']}))
        
        assistant_prompt = get_msg(Role.ASSISTANT, "<reflection>")
        
        messages = [user_prompt, assistant_prompt]
        
        llm_response = llm_turns(self.client, {'system': system_prompt, 'messages': messages}, ["</reflection>"], TEMP, 1)[0]

        correct_interpretation = get_yes_no_input(f"""\n[{FRIENDLY_COLOR}][bold]Before your feedback is submitted, let's make sure the LLM understands your intentions.[/bold]
Here's how it interprets your feedback on the last run:[/{FRIENDLY_COLOR}]
{llm_response}
[bold]Is this an accurate reflection of the meaning you intended?[/bold]""")
        
        if correct_interpretation:
            return llm_response
        else:
            while not correct_interpretation:
                messages[-1] = get_msg(Role.ASSISTANT, llm_response)

                correction = input("What was incorrect or missing? (type 'c' to exit this loop) > ")
                if correction.lower() == "c":
                    return None

                messages.append(get_msg(Role.USER, "<correction>" + correction + "</correction>"))
                messages.append(get_msg(Role.ASSISTANT, """Here's a revised interpretation of your feedback based on your correction:
<revised_reflection>"""))
                
                llm_response = llm_turns(self.client, {'system': system_prompt, 'messages': messages}, ["</revised_reflection>"], TEMP, 1)[0]

                correct_interpretation = get_yes_no_input(f"""Here's a revised interpetation:
{llm_response}
[bold]Is this an accurate reflection of the meaning you intended?[/bold]""")
            
            return llm_response


    def step2str(self) -> tuple[str, str]:
        if self.step_num > 1:
            suffix = ", taking into consideration the results of what you have already done in prior steps:"
        else:
            suffix = ":"
        
        unified_user_str = f"Plan and implement step {self.step_num}" + suffix

        unified_assistant_str = f"""<plan>{self.unified_step['best_plan']}</plan>
<implementation>
{self.unified_step['best_proposition']}
</implementation>
<stdout>
{self.unified_step['output']}
</stdout>
<stderr>
{self.unified_step['error']}
</stderr>"""

        return unified_user_str, unified_assistant_str

    def format_candidates(self, candidates: list[str]):
        shuffled_indices = [i for i in range(len(candidates))]
        random.shuffle(shuffled_indices)

        formatted_candidates: str = "<candidates>\n"

        for i, shuffled_i in enumerate(shuffled_indices):
            formatted_candidates += f"<candidate_{i+1}>\n"
            formatted_candidates += f"{candidates[shuffled_i]}"
            formatted_candidates += f"</candidate_{i+1}>\n"

        formatted_candidates += "</candidates>\n"

        return shuffled_indices, formatted_candidates
    
    def choose(self, candidates: list[str], scores: list[int]) -> str:
        best_plan = candidates[np.argmax(scores)]
        dprint(f"{self.PRINT_PREFIX} best_plan:\n{best_plan}")

        return best_plan
    
    def reduce_scores(self, plan_candidates: list[str], candidate_votes: list[str], index_maps: list[list[int]]) -> list[int]:
        scores = [0] * len(plan_candidates)

        assert len(candidate_votes) == len(index_maps)

        for vote_i, vote in enumerate(candidate_votes):
            parsed_scores = xmlstr2dict(vote, self.client)

            best_candidate_shuffled_idx = int(parsed_scores['best_candidate'])
            worst_candidate_shuffled_idx = int(parsed_scores['worst_candidate'])

            index_map = index_maps[vote_i]

            best_candidate_abs_idx = index_map[best_candidate_shuffled_idx-1]
            worst_candidate_abs_idx = index_map[worst_candidate_shuffled_idx-1]

            scores[best_candidate_abs_idx] += 1
            scores[worst_candidate_abs_idx] -= 1

        dprint(f"{self.PRINT_PREFIX} scores: {scores}")

        return scores

    def reduce_scores_exec(self, unified_step: dict[str, str | list[str]]) -> tuple[float, float]:
        sum_yes_votes = 0
        avg_yes_votes = 0

        sum_error_votes = 0
        avg_error_votes = 0

        for exec_vote_str in unified_step['exec_vote_strs']:
            parsed_scores = xmlstr2dict(exec_vote_str, self.client)

            if parsed_scores['complete'] == "yes":
                sum_yes_votes += 1

            if parsed_scores['error'] == "yes":
                sum_error_votes += 1

        avg_yes_votes = sum_yes_votes / VOTER_COUNT
        avg_error_votes = sum_error_votes / VOTER_COUNT
        
        dprint(f"{self.PRINT_PREFIX} sum_yes_votes: {sum_yes_votes}")
        dprint(f"{self.PRINT_PREFIX} avg_yes_votes: {avg_yes_votes}")

        dprint(f"{self.PRINT_PREFIX} sum_error_votes: {sum_error_votes}")
        dprint(f"{self.PRINT_PREFIX} avg_error_votes: {avg_error_votes}")
        
        return avg_yes_votes, avg_error_votes
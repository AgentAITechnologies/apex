import os
import json
import random

from typing import Literal, Optional

import dotenv

from rich import print as rprint
import numpy as np

from agents.agent import Agent
from agents.state_management import ConversationStateMachine
from agents.execution_management.execution_management import CodeExecutor
from agents.prompt_management import load_system_prompt, load_user_prompt, get_msg

from agents.memory import Memory

from utils.enums import Role
from utils.custom_types import FeedbackDict, ScoresList, StrScoresDict, NumScoresDict
from utils.parsing import dict2xml, xml2xmlstr, xmlstr2dict, extract_language_and_code, get_yes_no_input, strip_step_tags
from utils.llm import llm_turns
from utils.files import create_incrementing_directory

from anthropic import Anthropic


# PLAN_COUNT_HL = int(os.environ.get("PLAN_COUNT_HL", "3"))
PLAN_COUNT = int(os.environ.get("PLAN_COUNT", "3"))

VOTER_COUNT = int(os.environ.get("VOTER_COUNT", "3"))
PROPOSAL_COUNT = int(os.environ.get("PROPOSAL_COUNT", "3"))

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
            print(f"[red][bold]{self.PRINT_PREFIX} TOT_DIR environment variable not set (check .env)[/bold][/red]")
            exit(1)
        if input_dir is None:
            print(f"[red][bold]{self.PRINT_PREFIX} INPUT_DIR environment variable not set (check .env)[/bold][/red]")
            exit(1)
        if output_dir is None:
            print(f"[red][bold]{self.PRINT_PREFIX} OUTPUT_DIR environment variable not set (check .env)[/bold][/red]")
            exit(1)

        self.output_dir = os.path.join(tot_dir, output_dir)

        with open(os.path.join(tot_dir, input_dir, "states.json")) as file:
            state_data = json.load(file)
            rprint(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(tot_dir, input_dir, "transitions.json")) as file:
            transition_data = json.load(file)
            rprint(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path="Plan", prefix=self.PRINT_PREFIX, owner_class_name="ToT")

        self.code_executor = CodeExecutor(prefix=self.PRINT_PREFIX, owner_name=self.name)

        self.unified_memory = Memory(prefix=self.PRINT_PREFIX)
        self.unified_steps = []
    
    def run(self) -> None:
        task_dict = self.tasks[-1]
        task = xml2xmlstr(dict2xml(task_dict))

        rprint(f"{self.PRINT_PREFIX} task:\n{task}")

        self.log_dir = create_incrementing_directory(self.output_dir, f"{self.name}_")

        with open(os.path.join(self.log_dir, RESULT_FILENAME), 'w') as logfile:
            logfile.write(task + "\n")

        if self.csm.current_state.name == "Done":
            self.csm.transition("Plan", locals())

        self.step_num = 1
        self.open_step_tag = f"<step_{self.step_num}>"
        self.close_step_tag = f"</step_{self.step_num}>"

        self.unified_step: dict = {}

        while self.csm.current_state.name != "Done":
            state_path = self.csm.current_state.get_hpath()
                                           
            match state_path:
                
                case "Plan":
                    system_prompt = load_system_prompt(state_path, "TOT_DIR", {"step_num": str(self.step_num),
                                                                               "task": task})
                    
                    user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                    "task": task,
                                                                                                    "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                    
                    start_seq = self.open_step_tag + "<plan>"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                    messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]
                                                 
                    plan_candidates: list[str] = list(set(llm_turns(client=self.client,
                                                              prompts={"system": system_prompt,
                                                                       "messages": messages},
                                                              stop_sequences=["</plan>"],
                                                              temperature=TEMP,
                                                              n=PLAN_COUNT)))
                    
                    self.unified_step['plan_candidates'] = plan_candidates

                    if len(self.unified_step['plan_candidates']) != 1:
                        self.csm.transition("PlanVote", locals())
                    else:
                        self.unified_step['best_plan'] = next(iter(self.unified_step['plan_candidates']))
                        self.csm.transition("Propose", locals())

                case "PlanVote":
                    system_prompt = load_system_prompt(state_path, "TOT_DIR", {"step_num": str(self.step_num),
                                                                               "task": task})
                    
                    start_seq = self.open_step_tag + "<evaluation>"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)
                    
                    plan_votes: list[str] = []
                    plan_index_maps: list[list[int]] = []

                    for _ in range(VOTER_COUNT):
                        shuffled_indices, plan_candidates_str = self.format_candidates(plan_candidates)

                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                        "task": task,
                                                                                                        "plan_candidates_str": plan_candidates_str,
                                                                                                        "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))

                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                        plan_votes.append(llm_turns(client=self.client,
                                                    prompts={"system": system_prompt,
                                                             "messages": messages},
                                                    stop_sequences=["</evaluation>"],
                                                    temperature=TEMP,
                                                    n=1)[0])
                        
                        plan_index_maps.append(shuffled_indices)

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
                    system_prompt = load_system_prompt(state_path, "TOT_DIR", {"task": task})

                    user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                    "task": task,
                                                                                                    "plan": self.unified_step['best_plan'],
                                                                                                    "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                    
                    start_seq = self.open_step_tag + "<implementation>" + "\n" + "```python"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)
                    
                    messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                    raw_proposals = llm_turns(client=self.client,
                                              prompts={"system": system_prompt,
                                                       "messages": messages},
                                              stop_sequences=["```"],
                                              temperature=TEMP,
                                              n=PROPOSAL_COUNT)
                        
                    proposal_candidates = list(set(["```python" + raw_proposal + "```" for raw_proposal in raw_proposals]))
                    
                    if len(proposal_candidates) != 1:
                        self.csm.transition("ProposeVote", locals())
                    else:
                        self.unified_step['best_proposition'] = next(iter(proposal_candidates))
                        self.csm.transition("Exec", locals())

                case "ProposeVote":
                    system_prompt = load_system_prompt(state_path, "TOT_DIR", {"step_num": str(self.step_num),
                                                                               "task": task})
                    
                    start_seq = self.open_step_tag + "<evaluation>"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                    proposal_votes: list[str] = []
                    proposal_index_maps: list[list[int]] = []
                    
                    for _ in range(VOTER_COUNT):
                        shuffled_indices, proposal_candidates_str = self.format_candidates(proposal_candidates)

                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                        "task": task,
                                                                                                        "plan": self.unified_step['best_plan'],
                                                                                                        "proposal_candidates_str": proposal_candidates_str,
                                                                                                        "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                        
                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                        proposal_votes.append(llm_turns(client=self.client,
                                                        prompts={"system": system_prompt,
                                                                "messages": messages},
                                                        stop_sequences=["</evaluation>"],
                                                        temperature=TEMP,
                                                        n=1)[0])
                        
                        proposal_index_maps.append(shuffled_indices)

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
                        rprint(f"[red][bold]{self.PRINT_PREFIX} code not parsable:\n{fenced_code}[/bold][/red]")
                        exit(1)
                    
                    language, code = parsed_code

                    rprint(f"{self.PRINT_PREFIX} executing code:")
                    print(code.strip())

                    self.code_executor.write_code_step_file(code, self.step_num)

                    stdout, stderr = self.code_executor.execute_code_step(self.step_num)

                    rprint(f"{self.PRINT_PREFIX} stdout:")
                    print(stdout, end='')
                    rprint(f"{self.PRINT_PREFIX} stderr:")
                    print(stderr, end='')

                    self.unified_step['output'] = stdout
                    self.unified_step['error'] = stderr

                    self.csm.transition("ExecVote", locals())

                case "PlanErrorFix":
                    previous_step = self.unified_steps[-1]

                    frmt = {"step_num": str(self.step_num), "task": task, "error": previous_step['error'], "output": previous_step['output']}

                    system_prompt = load_system_prompt(state_path, "TOT_DIR", frmt)      
                    user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, frmt))
                    
                    start_seq = self.open_step_tag + "<plan>"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                    messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]
                                                 
                    plan_candidates: list[str] = list(set(llm_turns(client=self.client,
                                                                    prompts={"system": system_prompt,
                                                                            "messages": messages},
                                                                    stop_sequences=["</plan>"],
                                                                    temperature=TEMP,
                                                                    n=PLAN_COUNT)))
                    
                    self.unified_step['plan_candidates'] = plan_candidates

                    if len(self.unified_step['plan_candidates']) != 1:
                        self.csm.transition("PlanVote", locals())
                    else:
                        self.unified_step['best_plan'] = next(iter(self.unified_step['plan_candidates']))
                        self.csm.transition("Propose", locals())

                case "ExecVote":
                    system_prompt = load_system_prompt(state_path, "TOT_DIR", {"task": task})
                    user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                    "task": task,
                                                                                                    "plan": self.unified_step['best_plan'],
                                                                                                    "implementation": self.unified_step['best_proposition'],
                                                                                                    "output": self.unified_step['output'],
                                                                                                    "error": self.unified_step['error']}))
                    
                    start_seq = self.open_step_tag + "<evaluation>"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                    messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]
                    
                    exec_votes: list[str] = llm_turns(client=self.client,
                                                      prompts={"system": system_prompt,
                                                            "messages": messages},
                                                      stop_sequences=["</evaluation>"],
                                                      temperature=TEMP,
                                                      n=VOTER_COUNT)
                    
                    self.unified_step['exec_vote_strs'] = exec_votes

                    self.csm.transition("SumExecVote", locals())

                case "SumExecVote":
                    avg_yes_votes, avg_error_votes = self.reduce_scores_exec(self.unified_step)

                    self.next_step()

                    if avg_yes_votes > 0.5:
                        self.csm.transition("Done", locals())
                    elif avg_error_votes > 0.5:
                        self.csm.transition("PlanErrorFix", locals())
                    else:
                        self.csm.transition("Plan", locals())

        self.code_executor.condense_code_files(task)
        
        feedback = self.get_feedback(task, False)
        self.log_feedback(feedback)

        rprint(f"{self.PRINT_PREFIX} done!")

        return
    
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
        with open(os.path.join(self.log_dir, RESULT_FILENAME), 'a') as logfile:
            logfile.write("\n")

            logfile.write("<user>")
            logfile.write(unified_user_str + "</user>\n\n")

            logfile.write("<assistant>\n")
            logfile.write(unified_assistant_str + "\n</assistant>\n")
    
    def log_feedback(self, feedback: FeedbackDict) -> None:
        with open(os.path.join(self.log_dir, RESULT_FILENAME), 'a') as logfile:
            logfile.write("\n")

            logfile.write("<human_feedback>\n")
            logfile.write(f"<success>{feedback['success']}</success>\n")
            logfile.write(f"<details>{feedback['details']}</details>\n")
            logfile.write("</human_feedback>\n")

    # TODO: Summarize steps for easy human evaluation and pretty print the task
    def get_feedback(self, task: str, cutoff: bool) -> FeedbackDict:
        feedback_intro = f"\nThe task:\n{task}\n"
        
        if not cutoff:
            feedback_intro += "is believed to be complete according to your specifications, however this determination may have been in error."
        else:
            feedback_intro += "was interrupted and will be classified as a failure."

        feedback_intro += """
[deep_sky_blue1][bold]Your feedback is instrumental in evolving this virtual assistant.[/bold]
By sharing your insights, you're directly shaping the future of open conversational AI technology.
[italic]If you do not wish to be prompted for feedback in the future, simply disable this feature in your .env file.[/italic][/deep_sky_blue1]
"""
        rprint(feedback_intro)
        
        if not cutoff:
            success_prompt = "Was the task completed correctly, even if it took a while or involved self-correcting errors?"
            success = get_yes_no_input(success_prompt)
        else:
            success = False

        if success:
            details_prompt = "How could future completions of this task be better?\n(e.g., more efficient, having fewer side effects, or being more closely aligned with your intentions)?"
        else:
            details_prompt = "How would you characterize this failure? Please be as specific as possible to help us be more helpful to you in the future."

        
        rprint(details_prompt, end=" ")

        details = input()

        feedback: FeedbackDict = {
            "success": success,
            "details": details
        }

        return feedback

    def step2str(self) -> tuple[str, str]:
        if self.step_num > 1:
            suffix = ", taking into consideration the results of what you have already done in prior steps:"
        else:
            suffix = ":"
        
        unified_user_str = f"Plan and implement step {self.step_num}" + suffix

        unified_assistant_str = f"""{self.open_step_tag}
<plan>{self.unified_step['best_plan']}</plan>
<implementation>
{self.unified_step['best_proposition']}
</implementation>
<stdout>
{self.unified_step['output']}
</stdout>
<stderr>
{self.unified_step['error']}
</stderr>
{self.close_step_tag}"""

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
        rprint(f"{self.PRINT_PREFIX} best_plan:\n{best_plan}")

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

        rprint(f"{self.PRINT_PREFIX} scores: {scores}")

        return scores

    def reduce_scores_exec(self, unified_step: dict[str, set[str] | str | list[str]]) -> tuple[float, float]:
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
        
        rprint(f"{self.PRINT_PREFIX} sum_yes_votes: {sum_yes_votes}")
        rprint(f"{self.PRINT_PREFIX} avg_yes_votes: {avg_yes_votes}")

        rprint(f"{self.PRINT_PREFIX} sum_error_votes: {sum_error_votes}")
        rprint(f"{self.PRINT_PREFIX} avg_error_votes: {avg_error_votes}")
        
        return avg_yes_votes, avg_error_votes
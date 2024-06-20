import os
import json
from typing import Optional


import dotenv

from rich import print as rprint

from agents.agent import Agent
from agents.state_management import ConversationStateMachine
from agents.execution_management.execution_management import CodeExecutor
from agents.prompt_management import load_system_prompt, load_user_prompt, get_msg

from agents.memory import Memory

from utils.enums import Role
from utils.custom_types import ScoresList, StrScoresDict, NumScoresDict
from utils.parsing import dict2xml, xml2xmlstr, xmlstr2dict, extract_language_and_code
from utils.llm import llm_turns

from anthropic import Anthropic


PLAN_COUNT_HL = int(os.environ.get("PLAN_COUNT_HL", "3"))
PLAN_COUNT = int(os.environ.get("PLAN_COUNT", "3"))

VOTER_COUNT = int(os.environ.get("VOTER_COUNT", "3"))
PROPOSAL_COUNT = int(os.environ.get("PROPOSAL_COUNT", "3"))

EVAL_CATEGORIES = ["correctness", "elegance", "understandability", "specificity", "overall"]

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

        with open(os.path.join(os.environ.get("TOT_DIR", "NO_PATH_SET"), os.environ.get("INPUT_DIR", "NO_PATH_SET"), "states.json")) as file:
            state_data = json.load(file)
            rprint(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(os.environ.get("TOT_DIR", "NO_PATH_SET"), os.environ.get("INPUT_DIR", "NO_PATH_SET"), "transitions.json")) as file:
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
                                                 
                    plan_candidates: set[str] = set(llm_turns(client=self.client,
                                                              prompts={"system": system_prompt,
                                                                       "messages": messages},
                                                              stop_sequences=["</plan>"],
                                                              temperature=TEMP,
                                                              n=PLAN_COUNT))
                    
                    self.unified_step['plan_candidates'] = plan_candidates

                    if len(self.unified_step['plan_candidates']) != 1:
                        self.csm.transition("PlanVote", locals())
                    else:
                        self.unified_step['best_plan'] = next(iter(self.unified_step['plan_candidates']))
                        self.csm.transition("Propose", locals())

                case "PlanVote":
                    system_prompt = load_system_prompt(state_path, "TOT_DIR", {"step_num": str(self.step_num),
                                                                               "task": task})
                    
                    plan_vote_strs: dict[str, list[str]] = {}

                    for plan_candidate in plan_candidates:
                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                        "task": task,
                                                                                                        "plan": plan_candidate,
                                                                                                        "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))

                        start_seq = self.open_step_tag + "<evaluation>"
                        assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                        plan_vote_strs[plan_candidate] = llm_turns(client=self.client,
                                                                   prompts={"system": system_prompt,
                                                                            "messages": messages},
                                                                   stop_sequences=["</evaluation>"],
                                                                   temperature=TEMP,
                                                                   n=VOTER_COUNT)
                        
                    self.unified_step['plan_vote_strs'] = plan_vote_strs

                    self.csm.transition("SumPlanVotes", locals())

                case "SumPlanVotes":
                    plan_scores = self.reduce_scores(self.unified_step['plan_vote_strs'])
                    self.unified_step['plan_scores'] = plan_scores

                    self.csm.transition("ChoosePlan", locals())

                case "ChoosePlan":
                    best_plan = self.choose(self.unified_step['plan_scores'])
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
                        
                    proposals = ["```python" + raw_proposal + "```" for raw_proposal in raw_proposals]
                        
                    proposals_map: dict[str, list[str]] = {self.unified_step['best_plan']: proposals}

                    self.unified_step['proposals'] = set(proposals_map[self.unified_step['best_plan']])
                    
                    if len(self.unified_step['proposals']) != 1:
                        self.csm.transition("ProposeVote", locals())
                    else:
                        self.unified_step['best_proposition'] = next(iter(self.unified_step['proposals']))
                        self.csm.transition("Exec", locals())

                case "ProposeVote":
                    system_prompt = load_system_prompt(state_path, "TOT_DIR", {"task": task})
                    
                    start_seq = self.open_step_tag + "<evaluation>"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                    proposal_vote_map: dict[str, list[str]] = {}
                    
                    for proposal in self.unified_step['proposals']:
                        user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, {"step_num": str(self.step_num),
                                                                                                        "task": task,
                                                                                                        "plan": self.unified_step['best_plan'],
                                                                                                        "implementation": proposal,
                                                                                                        "suffix": ", taking into consideration the results of what you have already done in prior steps:" if self.step_num > 1 else ":"}))
                        
                        messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]

                        proposal_vote_map[proposal] = llm_turns(client=self.client,
                                                                prompts={"system": system_prompt,
                                                                         "messages": messages},
                                                                stop_sequences=["</evaluation>"],
                                                                temperature=TEMP,
                                                                n=VOTER_COUNT)

                    self.unified_step['proposal_vote_strs'] = proposal_vote_map

                    self.csm.transition("SumProposeVotes", locals())

                case "SumProposeVotes":
                    proposal_scores = self.reduce_scores(self.unified_step['proposal_vote_strs'], omit_categories=["specificity"])
                    self.unified_step['proposal_scores'] = proposal_scores

                    self.csm.transition("ChooseProposition", locals())

                case "ChooseProposition":
                    best_proposition = self.choose(self.unified_step['proposal_scores'])
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

                    if stderr:
                        self.next_step()
                        self.csm.transition("PlanErrorFix", locals())

                    else:
                        self.csm.transition("ExecVote", locals())

                case "PlanErrorFix":
                    previous_step = self.unified_steps[-1]

                    frmt = {"step_num": str(self.step_num), "task": task, "error": previous_step['error'], "output": previous_step['output']}

                    system_prompt = load_system_prompt(state_path, "TOT_DIR", frmt)      
                    user_prompt = get_msg(Role.USER, load_user_prompt(state_path, "TOT_DIR", None, frmt))
                    
                    start_seq = self.open_step_tag + "<plan>"
                    assistant_prompt = get_msg(Role.ASSISTANT, start_seq)

                    messages = self.unified_memory.conversation_history + [user_prompt, assistant_prompt]
                                                 
                    plan_candidates: set[str] = set(llm_turns(client=self.client,
                                                              prompts={"system": system_prompt,
                                                                       "messages": messages},
                                                              stop_sequences=["</plan>"],
                                                              temperature=TEMP,
                                                              n=PLAN_COUNT))
                    
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
                    avg_yes_votes = self.reduce_scores_exec(self.unified_step)

                    if avg_yes_votes > 0.5:
                        self.csm.transition("Done", locals())
                    else:
                        self.next_step()
                        self.csm.transition("Plan", locals())

        self.code_executor.finalize_task(task)

        rprint(f"{self.PRINT_PREFIX} done!")

        return
    
    def next_step(self) -> None:
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

        unified_user_msg = get_msg(Role.USER, unified_user_str)
        unified_assistant_msg = get_msg(Role.ASSISTANT, unified_assistant_str)

        self.unified_memory.add_msg(unified_user_msg)
        self.unified_memory.add_msg(unified_assistant_msg)

        self.step_num += 1
        self.unified_steps.append(self.unified_step)
        self.unified_step: dict = {}
        self.open_step_tag = f"<step_{self.step_num}>"
        self.close_step_tag = f"</step_{self.step_num}>"
    
    def reduce_scores(self, step_plan_vote_strs: dict[str, list[str]], omit_categories: Optional[list[str]] = None) -> NumScoresDict:
        if not omit_categories:
            omit_categories = []
        
        avg_scores: NumScoresDict = {step_plan: {eval_category: 0.0 for eval_category in EVAL_CATEGORIES if eval_category not in omit_categories}
                                     for step_plan in step_plan_vote_strs.keys()}
 
        scores: dict[str, list[StrScoresDict]] = {}

        for step_plan, vote_strs in step_plan_vote_strs.items():
            for vote_str in vote_strs:
                if step_plan not in scores:
                    scores[step_plan] = []

                parsed_scores: StrScoresDict = xmlstr2dict(vote_str, self.client)
                scores[step_plan].append(parsed_scores)

        for step_plan, scores_list in scores.items():
            for score in scores_list:
                for category in EVAL_CATEGORIES:
                    if category not in omit_categories:
                        avg_scores[step_plan][category] += int(score[category]['score']) / VOTER_COUNT

        rprint(f"{self.PRINT_PREFIX} avg_scores:\n{avg_scores}")
        
        return avg_scores
    
    def reduce_scores_exec(self, unified_step: dict[str, set[str] | str | list[str]]) -> float:
        sum_yes_votes = 0
        avg_yes_votes = 0

        for exec_vote_str in unified_step['exec_vote_strs']:
            parsed_scores = xmlstr2dict(exec_vote_str, self.client)

            if parsed_scores['complete'] == "yes":
                sum_yes_votes += 1

        avg_yes_votes = sum_yes_votes / VOTER_COUNT
        
        rprint(f"{self.PRINT_PREFIX} sum_yes_votes: {sum_yes_votes}")
        rprint(f"{self.PRINT_PREFIX} avg_yes_votes: {avg_yes_votes}")
        
        return avg_yes_votes

    def choose(self, scores: NumScoresDict) -> str:
        def sort_dicts(dicts) -> ScoresList:
            def get_mean_score(item) -> float:
                scores = item[1].values()
                return sum(scores) / len(scores)

            return sorted(dicts.items(), key=get_mean_score, reverse=True)
        
        avg_scores_sorted: ScoresList = sort_dicts(scores)

        best, best_scores = avg_scores_sorted[0]

        rprint(f"{self.PRINT_PREFIX} best:\n{best}")
        rprint(f"{self.PRINT_PREFIX} best_scores:\n{best_scores}")

        return best
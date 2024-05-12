import os
import json

from copy import deepcopy
from typing import Any

from rich import print

from agents.state_management import ConversationStateMachine
from agents.memory import Memory

from utils.parsing import xmlstr2dict, strip_step_tags

from anthropic import Anthropic


PLAN_COUNT_HL = int(os.environ.get("PLAN_COUNT_HL"))
PLAN_COUNT = int(os.environ.get("PLAN_COUNT"))

VOTER_COUNT = int(os.environ.get("VOTER_COUNT"))
PROPOSER_COUNT = int(os.environ.get("PROPOSER_COUNT"))

EVAL_CATEGORIES = ["correctness", "elegance", "understandability", "overall"]


class ToT():
    PRINT_PREFIX = "[blue][bold][ToT][/bold][/blue]"

    def __init__(self, name, description, tasks, client: Anthropic):
        self.name = name
        self.description = description
        self.tasks = tasks
        self.client = client

        with open(os.path.join(os.environ.get("TOT_DIR"), os.environ.get("INPUT_DIR"), "states.json")) as file:
            state_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded state_data")

        with open(os.path.join(os.environ.get("TOT_DIR"), os.environ.get("INPUT_DIR"), "transitions.json")) as file:
            transition_data = json.load(file)
            print(f"{self.PRINT_PREFIX} loaded transition_data")

        self.csm = ConversationStateMachine(state_data=state_data, transition_data=transition_data, init_state_path='Plan', prefix=self.PRINT_PREFIX, owner_class_name="ToT")

        self.memory = Memory(prefix=self.PRINT_PREFIX)

        self.run()
    
    def llm_turn(self, prompts, temperature, stop_sequences) -> str:
        llm_response = self.csm.current_state.llm_call(client=self.client,
                                        formatted_system=prompts["system"],
                                        formatted_messages=prompts["messages"],
                                        stop_sequences=stop_sequences,
                                        temperature=temperature)
        
        print(f"{self.PRINT_PREFIX} llm_response: {llm_response}")
        return llm_response.content[0].text
    
    def run(self):

        step_num = 1

        plan_memories = self.init_plan_memories()

        plan_voter_memories = self.init_voter_memories()
        propose_voter_memories = self.init_voter_memories()

        # TODO: don't plan as a monolith! plan a step, vote, propose the step, vote, execute it, repeat until done 
        while self.csm.current_state.name != "Done":

            START_SEQ = f"<step_{step_num}>"
            STOP_SEQ = f"</step_{step_num}>"

            if self.csm.current_state.get_hpath() == "Plan":
                
                for plan_memory in plan_memories:
                
                    system = plan_memory.load_sys_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", frmt={"task": self.tasks[-1]})

                    plan_memory.load_user_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", dynamic_metaprompt=None, frmt={"step_num": step_num})
                    plan_memory.load_assistant_prefill(START_SEQ)

                    llm_response = self.llm_turn(prompts={"system": system, "messages": plan_memory.conversation_history}, temperature=0.7, stop_sequences=[STOP_SEQ])

                    plan_memory.store_llm_response(START_SEQ + llm_response + STOP_SEQ)

                self.csm.transition("PlanVote", locals())

            elif self.csm.current_state.get_hpath() == "PlanVote":

                for plan in plan_memories:
                    for voter in plan_voter_memories:
                        step = plan.conversation_history[-1]["content"]

                        system = voter.load_sys_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", frmt={"task": self.tasks[-1]})

                        voter.load_user_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", dynamic_metaprompt=None, frmt={"step": step})
                        voter.load_assistant_prefill(START_SEQ)

                        llm_response = self.llm_turn(prompts={"system": system, "messages": voter.conversation_history}, temperature=0.7, stop_sequences=[STOP_SEQ])

                        xml_text = START_SEQ + llm_response + STOP_SEQ
                        voter.store_llm_response(xml_text)

                        vote_result = {"step_num": step_num, "plan_idx": plan.plan_idx, "xml_text": xml_text}
                        voter.vote_results.append(vote_result)

                self.csm.transition("SumPlanVotes", locals())

            elif self.csm.current_state.get_hpath() == "SumPlanVotes":
                sum_scores, avg_scores = self.reduce_scores(plan_voter_memories, step_num)

                print(f"{self.PRINT_PREFIX} sum_scores:\n{sum_scores}")
                print(f"{self.PRINT_PREFIX} avg_scores:\n{avg_scores}")

                self.csm.transition("ChoosePlan", locals())

            elif self.csm.current_state.get_hpath() == "ChoosePlan":
                sum_scores_list: list[str, float | int] = [{**sum_scores[i], "plan_idx": i} for i in sorted(sum_scores.keys())]    
                sum_scores_list_sorted: list[str, float | int] = sorted(sum_scores_list,
                                                                  key=lambda x: tuple( (x[category] for category in EVAL_CATEGORIES if not (category == "plan_idx") ) ),
                                                                  reverse=True)

                best_plan_scores = sum_scores_list_sorted[0]

                print(f"{self.PRINT_PREFIX} sum_scores_list_sorted:\n{sum_scores_list_sorted}")
                print(f"{self.PRINT_PREFIX} best_plan_scores:\n{best_plan_scores}")

                best_plan_idx = sum_scores_list_sorted[0]['plan_idx']
                print(f"{self.PRINT_PREFIX} plan {best_plan_idx} is the best plan")

                plan_memories = self.copyover_from_best_plan(plan_memories, best_plan_idx)

                self.csm.transition("Propose", locals())
            
            elif self.csm.current_state.get_hpath() == "Propose":

                for plan_memory in plan_memories:
                    
                    # search_query only present due to its presence in the system prompt - it is not meant to be replaced
                    system = plan_memory.load_sys_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", frmt={"task": self.tasks[-1], "search_query": "{search_query}"})
                    
                    plan_memory.load_user_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", dynamic_metaprompt=None, frmt={"step_num": step_num})
                    plan_memory.load_assistant_prefill(START_SEQ)

                    llm_response = self.llm_turn(prompts={"system": system, "messages": plan_memory.conversation_history}, temperature=0.7, stop_sequences=[STOP_SEQ])

                    plan_memory.store_llm_response(START_SEQ + llm_response + STOP_SEQ)
                
                self.csm.transition("ProposeVote", locals())

            elif self.csm.current_state.get_hpath() == "ProposeVote":

                for plan in plan_memories:
                    for voter in propose_voter_memories:
                        step_plan = strip_step_tags(plan.conversation_history[-3]["content"])
                        step_implementation = strip_step_tags(plan.conversation_history[-1]["content"]).strip()

                        system = voter.load_sys_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", frmt={"task": self.tasks[-1]})

                        voter.load_user_prompt(self.csm.current_state.get_hpath(), "TOT_DIR", dynamic_metaprompt=None, frmt={"step_plan": step_plan, "step_implementation": step_implementation})
                        voter.load_assistant_prefill(START_SEQ)

                        llm_response = self.llm_turn(prompts={"system": system, "messages": voter.conversation_history}, temperature=0.7, stop_sequences=[STOP_SEQ])

                        xml_text = START_SEQ + llm_response + STOP_SEQ
                        voter.store_llm_response(xml_text)

                        vote_result = {"step_num": step_num, "plan_idx": plan.plan_idx, "xml_text": xml_text}
                        voter.vote_results.append(vote_result)

    def init_plan_memories(self) -> list[Memory]:
        plan_memories = []

        for plan_idx in range(PLAN_COUNT):
            plan_memory: Memory = Memory(prefix=f"{self.PRINT_PREFIX} (plan {plan_idx})")
            plan_memory.plan_idx = plan_idx
            plan_memories.append(plan_memory)

        return plan_memories
    
    def copyover_from_best_plan(self, plan_memories, best_plan_idx) -> list[Memory]:
        best_plan = None
        for plan_memory in plan_memories:
            if plan_memory.plan_idx == best_plan_idx:
                best_plan = plan_memory
                break

        for plan_memory in plan_memories:
            if plan_memory.plan_idx != best_plan_idx:
                plan_memory.conversation_history = deepcopy(best_plan.conversation_history)

        return plan_memories
    
    def init_voter_memories(self) -> list[Memory]:
        voter_memories = []
        
        for voter_idx in range(VOTER_COUNT):
            voter_memory: Memory = Memory(prefix=f"{self.PRINT_PREFIX} (voter {voter_idx})")

            voter_idx: int = voter_idx
            voter_memory.voter_idx = voter_idx

            vote_results: list[dict[str, Any]] = []
            voter_memory.vote_results = vote_results

            voter_memories.append(voter_memory)

        return voter_memories
    
    def reduce_scores(self, voter_memories: Memory, step_num: int):
        sum_scores = {plan_idx: {eval_category: 0 for eval_category in EVAL_CATEGORIES} for plan_idx in range(PLAN_COUNT)}
        avg_scores = deepcopy(sum_scores)

        scores: dict[int, list] = {}

        for voter in voter_memories:
            for vote_result in voter.vote_results:
                if vote_result['step_num'] == step_num:
                    if not vote_result['plan_idx'] in scores:
                        scores[vote_result['plan_idx']] = []

                    parsed_scores = xmlstr2dict(vote_result['xml_text'])
                    scores[vote_result['plan_idx']].append(parsed_scores)

                    for category in EVAL_CATEGORIES:
                        sum_scores[vote_result['plan_idx']][category] += int(parsed_scores[f'step_{step_num}'][category]['score'])

        for plan_idx, scores in sum_scores.items():
            for category, score in scores.items():
                avg_scores[plan_idx][category] = score / len(voter_memories)
                
        return sum_scores, avg_scores


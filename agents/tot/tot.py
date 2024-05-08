import os
import json

from copy import deepcopy

from rich import print

from agents.state_management import ConversationStateMachine
from agents.memory import Memory

from utils.parsing import xmlstr2dict

from anthropic import Anthropic


PLAN_COUNT_HL = int(os.environ.get("PLAN_COUNT_HL"))
PLAN_COUNT = int(os.environ.get("PLAN_COUNT"))
VOTER_COUNT = int(os.environ.get("VOTER_COUNT"))

EVAL_CATEGORIES = ["correctness", "elegance", "understandability"]


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
    
    def llm_turn(self, prompts, temperature) -> str:
        llm_response = self.csm.current_state.llm_call(client=self.client,
                                        formatted_system=prompts["system"],
                                        formatted_messages=prompts["messages"],
                                        stop_sequences=["</output>"],
                                        temperature=temperature)
        
        print(f"{self.PRINT_PREFIX} llm_response: {llm_response}")
        return llm_response.content[0].text
    
    def run(self):
        memories: list[list[Memory]] = []

        for row in range(VOTER_COUNT):
            memories.append([])

            for col in range(PLAN_COUNT):
                memories[row].append(Memory(prefix=f"{self.PRINT_PREFIX} (voter {row}, [plan {col})"))
                

        while self.csm.current_state.name != "Done":
            if self.csm.current_state.get_hpath() == "Plan":
                for row in range(VOTER_COUNT):
                    for col in range(PLAN_COUNT):
                        prompts = memories[row][col].load_all_prompts(self.csm.current_state.get_hpath(), "TOT_DIR", dynamic_user_metaprompt=None, frmt={"task": self.tasks[-1]})
                
                self.plans = [self.llm_turn(prompts=prompts, temperature=0.7) for _ in range(PLAN_COUNT)]

                for row in range(VOTER_COUNT):
                    for col in range(PLAN_COUNT):
                        memories[row][col].store_llm_response("<output>" + self.plans[col] + "</output>")

                print(f"{self.PRINT_PREFIX} self.plans:\n{self.plans}")
                self.csm.transition("PlanVote", locals())

            elif self.csm.current_state.get_hpath() == "PlanVote":
                for row in range(VOTER_COUNT):
                    for col in range(PLAN_COUNT):
                        prompts = memories[row][col].load_all_prompts(self.csm.current_state.get_hpath(), "TOT_DIR", dynamic_user_metaprompt=None, frmt={"task": self.tasks[-1], "plan": self.plans[col]})
                        vote = self.llm_turn(prompts=prompts, temperature=0.7)
                        memories[row][col].store_llm_response("<output>" + vote + "</output>")
                
                self.csm.transition("SumPlanVotes", locals())
                
            elif self.csm.current_state.get_hpath() == "SumPlanVotes":
                avg_scores = self.get_avg_scores(memories)
                print(f"\navg_scores:\n{avg_scores}")

                

    def get_avg_scores(self, memories):
        sum_scores = {plan_idx: {eval_category: 0 for eval_category in EVAL_CATEGORIES} for plan_idx in range(PLAN_COUNT)}
        avg_scores = deepcopy(sum_scores)

        for voter_idx in range(VOTER_COUNT):
            for plan_idx in range(PLAN_COUNT):
                parsed = xmlstr2dict(memories[voter_idx][plan_idx].conversation_history[-1]["content"])
                parsed_scores = parsed['output']

                for category in EVAL_CATEGORIES:
                    sum_scores[plan_idx][category] += int(parsed_scores[category]["score"])
                    
        for plan_idx in range(PLAN_COUNT): 
            for category in EVAL_CATEGORIES:
                avg_scores[plan_idx].update({category: sum_scores[plan_idx][category] / VOTER_COUNT})
                
        return avg_scores


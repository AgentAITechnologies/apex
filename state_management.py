from __future__ import annotations

from copy import deepcopy
import pygraphviz as pgv
import os

from typing import Optional

from callbacks import *


class ConversationState:
    def __init__(self, name=None, parent: Optional[ConversationState] = None, system="", messages=[], frmt={}):
        self.name = name

        self.system = system
        self.messages = messages
        self.frmt = frmt

        self.formatted_system = None
        self.formatted_messages = None

        self.result = None

        self.parent = parent

        self.transitions: dict[str, ConversationState] = {}
        self.children = []

        self.load_callback()

    def configure_llm_call(self, frmt_update={}):
        self.update_frmt(frmt_update)

        self.build_system()
        self.build_messages()

        return self.formatted_system, self.formatted_messages

    def update_frmt(self, frmt_update, recursive=False):
        self.frmt.update(frmt_update)
        
        def recursive_format(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    recursive_format(value)
                elif isinstance(value, str):
                    try:
                        d[key] = value.format(**self.frmt)
                    except KeyError:
                        d[key] = value
                        # print(f"[state_mgmt] KeyError: {key}\nassigned to\n\"{value}\"\nwithout recursion")
        
        if recursive:
            recursive_format(self.frmt)
    
    def llm_call(self, client, formatted_system, formatted_messages):
        self.formatted_system = formatted_system
        self.formatted_messages = formatted_messages

        message = client.messages.create(
            model=os.environ.get("MODEL"),
            max_tokens=4000,
            temperature=0,
            system=formatted_system,
            messages=formatted_messages
        )
        
        return message

    def add_message(self, message):
        self.messages.append(message)

    def add_transition(self, trigger, next_state):
        self.transitions[trigger] = next_state

    def add_child(self, child_state: ConversationState):
        self.children.append(child_state)
        child_state.parent = self

    def get_next_state(self, response):
        if response in self.transitions:
            return self.transitions[response]
        elif self.parent:
            return self.parent.get_next_state(response)
        else:
            return None

    def get_root(self) -> ConversationState:
        if self.parent:
            return self.parent.get_root()
        else:
            return self

    def get_hpath(self) -> Optional[str]:
        if self.parent and self.parent.name != "Root":
            return self.parent.get_hpath() + "_" + self.name
        else:
            return self.name

    def load_callback(self):
        callback_class_name = f"{self.get_hpath()}_Callback"
        callback_class = globals().get(callback_class_name)
        if callback_class:
            self.callback: Optional[StateCallback] = callback_class()
        else:
            print(f"[CSM] no callback found for state {self.get_hpath()}")
            self.callback: Optional[StateCallback] = None

    def on_enter(self, csm: ConversationStateMachine, locals):
        if self.callback:
            self.callback.on_enter(csm, locals)

    def on_exit(self, csm: ConversationStateMachine, locals):
        if self.callback:
            self.callback.on_exit(csm, locals)


class ConversationStateMachine:
    PRINT_PREFIX = "[CSM]"

    def __init__(self, state_data=None, transition_data=None, init_state_path=None):
        self.initialize_conversation_states(state_data)
        self.initialize_transitions(transition_data)

        self.current_state: ConversationState = self.state_map[init_state_path]
        self.state_history: list[ConversationState] = []
    
    def transition(self, trigger, locals) -> Optional[ConversationState]:
        if trigger in self.current_state.transitions:
            # call exit callback
            self.current_state.on_exit(self, locals)
            # update state history
            self.state_history.append(deepcopy(self.current_state))
            # update current state
            self.current_state = self.current_state.transitions[trigger]
            # call enter callback
            self.current_state.on_enter(self, locals)
            # return next state
            return self.current_state
        else:
            print(f"{self.PRINT_PREFIX} invalid trigger '{trigger}' for state {self.current_state.get_hpath()}")
            return None
        
    def on_enter(self, locals):
        return self.current_state.on_enter(self, locals)
    
    def on_exit(self, locals):
        return self.current_state.on_exit(self, locals)
        
    def build_action_results(self):
        action_results = []
        for state in self.state_history+[self.current_state]:
            if "result" in state.frmt:
                action_results.append(state.frmt["result"])
        return action_results

    def initialize_conversation_states(self, state_data):
        def create_state(state_data, parent=None):
            state = ConversationState(name=state_data["name"],
                                      parent=parent,
                                      system=state_data.get("system", ""),
                                      messages=state_data.get("messages", []),
                                      frmt = state_data.get("frmt", {}))

            for child_data in state_data.get("children", []):
                child_state = create_state(child_data, parent=state)
                state.add_child(child_state)

            return state

        self.root_state = create_state(state_data)

    def find_state_by_path(self, path: str) -> Optional[ConversationState]:
        return self.state_map.get(path)
    
    def initialize_transitions(self, transition_data=None):
        self.transition_data = transition_data
        self.state_map: dict[str, ConversationState] = {}

        def traverse_and_map_states(state: ConversationState):
            self.state_map[state.get_hpath()] = state
            for child in state.children:
                traverse_and_map_states(child)

        traverse_and_map_states(self.root_state)

        for transition in transition_data:
            trigger = transition["trigger"]
            source_paths = transition["source"]
            dest_path = transition["dest"]

            if not isinstance(source_paths, list):
                source_paths = [source_paths]

            for source_path in source_paths:
                source_path = source_path
                source_state = self.find_state_by_path(source_path)
                dest_state = self.find_state_by_path(dest_path)

                if source_state and dest_state:
                    source_state.add_transition(trigger, dest_state)
                else:
                    print(f"{self.PRINT_PREFIX} Warning: Invalid transition - Source: {source_path}, Destination: {dest_path}")

    def visualize(self):
        graph = pgv.AGraph(directed=True)

        graph.graph_attr['fontname'] = 'Consolas'
        graph.node_attr['fontname'] = 'Consolas'
        graph.node_attr['shape'] = 'box'
        graph.node_attr['style'] = 'rounded'
        graph.edge_attr['fontname'] = 'Consolas'

        def add_state_to_graph(state: ConversationState, parent_subgraph: pgv.AGraph = None):
            if parent_subgraph is None:
                subgraph = graph
            else:
                subgraph = parent_subgraph.add_subgraph(name=f"cluster_{state.get_hpath()}")
                subgraph.graph_attr['style'] = 'rounded'

            if not (parent_subgraph is None):
                subgraph.add_node(state.get_hpath(), label=state.name)

            for child in state.children:
                add_state_to_graph(child, subgraph)

        add_state_to_graph(self.root_state)

        for transition in self.transition_data:
            trigger = transition["trigger"]
            source_paths = transition["source"]
            dest_path = transition["dest"]

            if not isinstance(source_paths, list):
                source_paths = [source_paths]

            for source_path in source_paths:
                source_state = graph.get_node(source_path)
                dest_state = graph.get_node(dest_path)

                if source_state and dest_state:
                    graph.add_edge(source_state, dest_state, label=trigger)

        graph.layout(prog='dot')
        
        if not os.path.exists(os.environ.get("OUTPUT_DIR")):
            os.makedirs(os.environ.get("OUTPUT_DIR"))
            
        graph.draw(os.path.join(os.environ.get("OUTPUT_DIR"), 'state_diagram.png'))
     
    def print_current_state(self):
        print(f"{self.PRINT_PREFIX} self.current_state: {self.current_state}")
        print(f"{self.PRINT_PREFIX} self.current_state.get_hpath(): {self.current_state.get_hpath()}")

    def print_state_hierarchy(self, state: ConversationState = None, level=0):
        if state == None:
            state = self.root_state

        print(self.PRINT_PREFIX + "  " * (level+1) + state.get_hpath())
        for child in state.children:
            self.print_state_hierarchy(child, level + 1)
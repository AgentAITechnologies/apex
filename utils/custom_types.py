from typing import Literal, Any, Dict, TypedDict, Union, Optional
from typing_extensions import NotRequired

NestedStrDict = Dict[str, Union[str, 'NestedStrDict', None]]

Message = dict[Literal['role', 'content'], str]
PromptsDict = dict[Literal['system', 'messages'], str | list[Message]]

StrScoresDict = dict[str, dict[str, str]]
NumScoresDict = dict[str, dict[str, float]]

FeedbackDict = dict[Literal["success", "details", "elaboration"], Optional[str | bool]]

# TODO: Find out what this actually is
ScoresList = list[Any]

ToolList = list[dict[str, str | int]]

# Base type for tool calls
ToolCallDict = dict[Literal['content', 'name', 'input'], str | dict[str, str]]

# Type for a list of tool calls
ToolCallsList = list[ToolCallDict]

ProposalCandidatesList = list[dict[Literal['str'] | Literal['dict'], str | ToolCallDict]]

class BashConfig(TypedDict):
    command: NotRequired[str]
    restart: NotRequired[bool]

class BashResult(TypedDict):
    output: str
    exit_code: int

class PythonConfig(TypedDict):
    code: str
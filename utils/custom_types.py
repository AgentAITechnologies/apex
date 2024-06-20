from typing import Literal, Any
from typing import Dict, Union

NestedStrDict = Dict[str, Union[str, 'NestedStrDict', None]]

Message = dict[Literal['role', 'content'], str]
PromptsDict = dict[Literal['system', 'messages'], str | list[Message]]

StrScoresDict = dict[str, dict[str, str]]
NumScoresDict = dict[str, dict[str, float]]

# TODO: Find out what this actually is
ScoresList = list[Any]
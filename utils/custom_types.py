from typing import Literal, Any

Message = dict[Literal['role', 'content'], str]
PromptsDict = dict[Literal['system', 'messages'], str | list[Message]]

StrScoresDict = dict[str, dict[str, str]]
NumScoresDict = dict[str, dict[str, float]]

# TODO: Find out what this actually is
ScoresList = list[Any]
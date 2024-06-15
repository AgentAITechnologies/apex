from typing import Literal, Dict, List, Any

from utils.enums import Role

Message = Dict[Literal["role", "content"], str]

StrScoresDict = Dict[str, Dict[str, str]]
NumScoresDict = Dict[str, Dict[str, float]]

# TODO: Find out what this actually is
ScoresList = List[Any]
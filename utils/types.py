from typing import Literal, Union, Dict

from utils.enums import Role

Message = dict[Literal["role", "content"], Union[Role, str]]

StrScoresDict = Dict[str, Union[str, "StrScoresDict"]]

IntScoreDict = dict[str, int]
IntScoresDict = dict[str, IntScoreDict]

ScoresList = list[str, float | int]
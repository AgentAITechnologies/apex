import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.enums import Role
from utils.custom_types import Message

from agents.prompt_management import get_message


@pytest.mark.parametrize("role, content, expected", [
    (Role.USER, "Hello, how can I help you?", {"role": "user", "content": "Hello, how can I help you?"}),
    (Role.ASSISTANT, "I am an AI assistant.", {"role": "assistant", "content": "I am an AI assistant."})                                         
])
def test_get_msg(role: Role, content: str, expected: Message):
    assert get_message(role, content) == expected
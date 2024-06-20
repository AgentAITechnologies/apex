import sys
import os

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


from utils.stt import STT

def test_stt_singleton():
    stt1 = STT()
    stt2 = STT()
    assert stt1 is stt2
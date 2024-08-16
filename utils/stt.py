from __future__ import annotations

from typing import Type
from typing_extensions import Self

import os
import sys
import numpy as np
from numpy import float64, ndarray, concatenate
import sounddevice as sd
from sounddevice import DeviceList
import soundfile as sf
from pynput import keyboard

from rich import print

import dotenv

from openai import OpenAI


class STT():
    PRINT_PREFIX = "[bold][STT][/bold]"

    _instance = None

    def __new__(cls: Type[Self], *args, **kwargs) -> Self:
        if cls._instance is None:
            print(f"{cls.PRINT_PREFIX} Creating a singleton STT")
            cls._instance = super(STT, cls).__new__(cls)
            cls._instance.__initialized = False

        return cls._instance

    def __init__(self) -> None:
        if not self.__initialized:
            dotenv.load_dotenv()

            if sys.platform.startswith('linux'):
                devices = sd.query_devices()

                if isinstance(devices, DeviceList):
                    audio_in_device_str = os.environ.get("AUDIO_IN_DEVICE")
                    self.interval_sec = .25

                    if audio_in_device_str is not None:

                        if audio_in_device_str.isnumeric():
                            self.audio_in_device = int(audio_in_device_str)

                        elif any([audio_in_device_str in device['name'] for device in devices]):
                            for device in devices:
                                if audio_in_device_str in device['name']:
                                    self.audio_in_device = devices.index(device)

                        else:
                            error_message = f"{self.PRINT_PREFIX} AUDIO_IN_DEVICE not numeric"
                            print(f"[red][bold]{error_message}[/bold][/red]")
                            raise ValueError(error_message)
                        
                        device = sd.query_devices(self.audio_in_device)
                        if isinstance(device, dict):
                            self.channels = device['max_input_channels']
                            self.fps = int(device['default_samplerate'])
                            
                    else:
                        error_message = f"{self.PRINT_PREFIX} AUDIO_IN_DEVICE is not set - this is required on Linux"
                        print(f"[bold][red]{error_message}[/red][/bold]")
                        raise EnvironmentError(error_message)

            self.recording_data: ndarray = ndarray((0, self.channels), dtype=float64)
            self.is_recording: bool = False
            self.done: bool = False

            self.__initialized = True

            print(f"{self.PRINT_PREFIX} Initialized the instance")        

    def on_press(self, key):
        if key == keyboard.Key.alt_r and not self.is_recording:
            self.is_recording = True

    def on_release(self, key):
        if key == keyboard.Key.alt_r and self.is_recording:
            self.is_recording = False
            self.done = True

    def transcribe_speech(self, test: bool=False) -> str:
        if self.audio_in_device is not None:
            recording_data = ndarray((0, self.channels))
            self.is_recording = False
            self.done = False

            client: OpenAI = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

            # sounddevice.py does not annotate the default (None, None) as Optional
            # modified line (58+3 = 61) to include "from typing import Optional"
            # modified line (2075+3 = 2078) to include type annotation
            sd.default.device = self.audio_in_device, None

            with sd.InputStream(samplerate=self.fps, device=self.audio_in_device, channels=self.channels) as instream:
                with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                    while True:
                        if self.is_recording:
                            segment, _ = instream.read(int(self.interval_sec * self.fps))
                            recording_data = concatenate((recording_data, segment))
                        elif self.done:
                            break
                        else:
                            continue

            preprocessed_data: np.float32 = np.float32(recording_data)

            audio_file_path = os.path.join(os.environ.get("UI_DIR", "NO_PATH_SET"), os.environ.get("OUTPUT_DIR", "NO_PATH_SET"), "user_command.wav")

            if not os.path.exists(audio_file_path):
                os.makedirs(os.path.join(os.environ.get("UI_DIR", "NO_PATH_SET"), os.environ.get("OUTPUT_DIR", "NO_PATH_SET")))
                with open(audio_file_path, 'w') as f:
                    f.write("")

            sf.write(audio_file_path, preprocessed_data, self.fps)

            if test:
                print("playback for testing...")

                if sys.platform.startswith('linux'):
                    audio_out_device_str = os.environ.get("AUDIO_OUT_DEVICE")

                    if audio_out_device_str is not None:
                        if audio_out_device_str.isnumeric():
                            self.audio_out_device = int(audio_out_device_str)

                            sd.default.device = self.audio_in_device, self.audio_out_device

                            audio_data, sample_rate = sf.read(audio_file_path)

                            sd.play(audio_data, samplerate=sample_rate)
                            sd.wait()
                        else:
                            error_message = f"{self.PRINT_PREFIX} AUDIO_OUT_DEVICE not numeric"
                            print(f"[red][bold]{error_message}[/bold][/red]")
                            raise ValueError(error_message)
                    else:
                        error_message = f"{self.PRINT_PREFIX} AUDIO_OUT_DEVICE is not set - this is required on Linux"
                        print(f"[bold][red]{error_message}[/red][/bold]")
                        raise EnvironmentError(error_message)

            with open(audio_file_path, 'rb') as f:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )

            return transcription.text
        else:
            return input()


# testing
if __name__ == "__main__":
    stt = STT()
    print(stt.transcribe_speech(test=True))
import os
import time
import wave
import numpy as np
from numpy import float32, float64, ndarray, concatenate
import sounddevice as sd
import soundfile as sf
from pynput import keyboard
from rich import print
import dotenv

from openai import OpenAI


dotenv.load_dotenv()


PRINT_PREFIX = "[bold][STT][/bold]"

if os.environ.get("AUDIO_IN_DEVICE", "NO_DEVICE_SET") != "NO_DEVICE_SET":
    AUDIO_IN_DEVICE = int(os.environ.get("AUDIO_IN_DEVICE"))
else:
    AUDIO_IN_DEVICE = None

    if os.environ.get("USE_STT") == "True":
        print(f"[bold][red]{PRINT_PREFIX} AUDIO_IN_DEVICE is not set, but USE_STT is 'True' - AUDIO_IN_DEVICE is required to be set on Linux if using STT[/red][/bold]")

CHANNELS = sd.query_devices(AUDIO_IN_DEVICE)['max_input_channels']
FPS = int(sd.query_devices(AUDIO_IN_DEVICE)['default_samplerate'])
INTERVAL_SEC = 1


recording_data: ndarray[float64] = ndarray((0, CHANNELS))
is_recording: bool = False
done: bool = False


def on_press(key):
    global is_recording
    if key == keyboard.Key.alt_r and not is_recording:
        is_recording = True

def on_release(key):
    global is_recording, done
    if key == keyboard.Key.alt_r and is_recording:
        is_recording = False
        done = True

def transcribe_speech(test=False):
    if AUDIO_IN_DEVICE is not None:
        global recording_data, is_recording, done

        recording_data = ndarray((0, CHANNELS))
        is_recording = False
        done = False

        client: OpenAI = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        sd.default.device = AUDIO_IN_DEVICE

        with sd.InputStream(samplerate=FPS, device=AUDIO_IN_DEVICE, channels=CHANNELS) as instream:
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                while True:
                    if is_recording:
                        segment, _ = instream.read(int(INTERVAL_SEC * FPS))
                        recording_data = concatenate((recording_data, segment))
                    elif done:
                        break
                    else:
                        time.sleep(0.1)

        preprocessed_data: np.float32 = np.float32(recording_data)

        audio_file_path = os.path.join(os.environ.get("UI_DIR", "NO_PATH_SET"), os.environ.get("OUTPUT_DIR", "NO_PATH_SET"), "user_command.wav")

        if not os.path.exists(audio_file_path):
            os.makedirs(os.path.join(os.environ.get("UI_DIR", "NO_PATH_SET"), os.environ.get("OUTPUT_DIR", "NO_PATH_SET")))
            with open(audio_file_path, 'w') as f:
                f.write("")

        sf.write(audio_file_path, preprocessed_data, FPS)

        if test:
            print("playback for testing...")
            
            if os.environ.get("AUDIO_OUT_DEVICE", "NO_DEVICE_SET") != "NO_DEVICE_SET":
                sd.default.device = int(os.environ.get("AUDIO_OUT_DEVICE"))
                
                audio_data, sample_rate = sf.read(audio_file_path)

                sd.play(audio_data, samplerate=sample_rate)
                sd.wait()
            else:
                print(f"[bold][red]{PRINT_PREFIX} AUDIO_OUT_DEVICE is not set - this is required on Linux[/red][/bold]")

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
    #for device in sd.query_devices():
    #    print(device)

    print(transcribe_speech(test=True))
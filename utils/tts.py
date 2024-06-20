import dotenv
import os
import requests

from io import BytesIO
import sounddevice as sd
import soundfile as sf

from rich import print


dotenv.load_dotenv()


PRINT_PREFIX = "[bold][TTS][/bold]"


def tts(text: str) -> None:
    LATENCY_LEVEL = int(os.environ.get("ELEVENLABS_LATENCY_LEVEL", "0"))

    url = f'https://api.elevenlabs.io/v1/text-to-speech/{os.environ.get("ELEVENLABS_VOICE_ID")}/stream?optimize_streaming_latency={LATENCY_LEVEL}'

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": os.environ.get("ELEVENLABS_API_KEY")
    }

    data = {
        "text": text,
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    response = requests.post(url, json=data, headers=headers, stream=True)

    if response.status_code == 200:
        audio_bytes = response.content
        audio_buffer = BytesIO(audio_bytes)

        AUDIO_OUT_DEVICE = os.environ.get("AUDIO_OUT_DEVICE")
        if AUDIO_OUT_DEVICE is not None:
            sd.default.device = None, int(AUDIO_OUT_DEVICE)
        else:
            print(f"[bold][red]{PRINT_PREFIX} AUDIO_OUT_DEVICE is not set, but USE_TTS is set to 'True' - AUDIO_OUT_DEVICE is required to be set on Linux if using TTS[/red][/bold]")

        audio_data, sample_rate = sf.read(audio_buffer)

        sd.play(audio_data, samplerate=sample_rate)

        # TODO: eventually remove the block
        # get a mutex that only some code paths block on as a finer-grained solution
        sd.wait()
    else:
        print(f"[bold][red]{PRINT_PREFIX} Error: {response.status_code} - {response.text}[/red][/bold]")


# testing
if __name__ == "__main__":
    for device in sd.query_devices():
        print(device)

    print(f"Using device {os.environ.get('AUDIO_OUT_DEVICE')}")

    tts("rat cat on a mat")
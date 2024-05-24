import dotenv
import os
import requests

from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play

dotenv.load_dotenv()

def tts(text):
    LATENCY_LEVEL = int(os.environ.get("ELEVENLABS_LATENCY_LEVEL"))

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
        audio_segment = AudioSegment.from_file(audio_buffer, format='mp3')
        play(audio_segment)
    else:
        print(f"Error: {response.status_code} - {response.text}")
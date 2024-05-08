import os

import pyaudio
from openai import OpenAI
import keyboard
import wave

import dotenv

dotenv.load_dotenv()

# Set up OpenAI API credentials
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Set up pyaudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

REC_KEY = 'alt'
QUIT_KEY = 'q'

def transcribe_speech():
    # Initialize pyaudio
    audio = pyaudio.PyAudio()

    # Open the microphone stream
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)
    
    # print(f"Recording... Release '{REC_KEY}' to stop.")
    frames = []

    while keyboard.is_pressed(REC_KEY):
        data = stream.read(CHUNK)
        frames.append(data)

    # print("Recording stopped. Transcribing...")

    # Convert the recorded audio to a byte string and save the recorded audio to a file
    audio_file = os.path.join(os.environ.get("UI_DIR"), os.environ.get("OUTPUT_DIR"), "user_command.wav")
    wf = wave.open(audio_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b"".join(frames))
    wf.close()

    # Clean up
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # print("Audio file saved. Transcribing...")

    with open(audio_file, "rb") as audio_file:
        # Use the OpenAI API to transcribe the audio

        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
            )

    # Print the transcribed text
    # print("Transcription:", transcription.text)

    return transcription.text



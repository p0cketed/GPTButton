
import sounddevice as sd
import numpy as np
from gpiozero import Button
from google.cloud import speech
from gtts import gTTS
import os
from openai import ChatCompletion
import webrtcvad
import collections

# Configuration
BUTTON_PIN = 17  # GPIO pin where the button is connected
RECORD_SECONDS = 5  # Length of the recording after button press
LANGUAGE_CODE = 'en-US'  # Language code for Google Speech-to-Text

CHATKEY = os.getenv("OPENAI_API_KEY")
if not CHATKEY:
    raise ValueError("CHATKEY not functioning.\n")

DEVICE_INDEX = 1  # Device index for microphone if not default

# Set up the OpenAI API client
openai_client = ChatCompletion(api_key=CHATKEY)

# Set up the button
button = Button(BUTTON_PIN)

# Initialize Google Cloud client
client = speech.SpeechClient()

# Function to record audio
def record_audio():
    fs = 44100  # Sample rate
    vad = webrtcvad.Vad(1)  # Create a VAD object
    vad.set_mode(1)  # Level of aggressiveness from 0 to 3

    print("Recording...")
    frames = collections.deque(maxlen=10)  # A buffer to hold the last few frames
    silence_frames = collections.deque(maxlen=10)  # A buffer to hold silence frames for comparison
    recording = []  # A list to store recorded frames
    is_speech = False  # Flag to keep track of when speech starts
    
    # Stream audio
    with sd.InputStream(samplerate=fs, channels=1, dtype='int16') as stream:
        while True:
            frame, overflowed = stream.read(int(fs * 0.1))  # Read 100ms of audio
            is_speech = vad.is_speech(frame.tobytes(), fs)

            if not is_speech and is_speech_started:
                silence_frames.append(frame)  # If we have started speech, collect silence frames
                if len(silence_frames) == silence_frames.maxlen:
                    break  # If enough silence has accumulated, break the loop
            else:
                recording.extend(silence_frames)  # Add any accumulated silence frames to recording
                silence_frames.clear()  # Clear silence frames buffer
                recording.append(frame)  # Add current frame to recording
                is_speech_started = True  # Set the speech flag

            frames.append(frame)  # Always add the current frame to the frames buffer
            if len(frames) == frames.maxlen and not is_speech_started:
                # If the frames buffer is full and we have not detected speech, clear the buffer
                frames.clear()
    
    print("Done recording.")
    recording = np.concatenate(recording)  # Concatenate all recorded frames
    return np.array(recording, dtype='float64')
# Function to transcribe audio to text
def transcribe_audio(audio_data, language_code=LANGUAGE_CODE):
    audio = speech.RecognitionAudio(content=audio_data.tobytes())
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code=language_code,
    )
    response = client.recognize(config=config, audio=audio)
    transcript = ''
    for result in response.results:
        transcript += result.alternatives[0].transcript
    return transcript

# Function to get a response from OpenAI
def ask_openai(question):
    response = openai_client.create(prompt=question, model="text-davinci-003")
    return response.choices[0].message.content

# Function to convert text to speech
def text_to_speech(text, lang=LANGUAGE_CODE):
    tts = gTTS(text=text, lang=lang)
    tts.save('response.mp3')
    os.system('mpg123 response.mp3')

# Main function to handle the button press
def on_button_press():
    print("Button pressed!")
    audio_data = record_audio()
    question = transcribe_audio(audio_data)
    print(f"Question: {question}")
    answer = ask_openai(question)
    print(f"Answer: {answer}")
    text_to_speech(answer)

# Attach the button press event
button.when_pressed = on_button_press

# Run forever
print("Device is ready, press the button to ask a question.")
while True:
    pass



import sounddevice as sd
import numpy as np
from gpiozero import Button
from google.cloud import speech
from gtts import gTTS
import os
import openai
from openai import ChatCompletion
import webrtcvad
import collections

# Configuration
BUTTON_PIN = 17  # GPIO pin where the button is connected
LANGUAGE_CODE = 'en-US'  # Language code for Google Speech-to-Text

CHATKEY = os.getenv("OPENAI_API_KEY")
if not CHATKEY:
    raise ValueError("CHATKEY not functioning.\n")

DEVICE_INDEX = 1  # Device index for microphone if not default

# Set up the OpenAI API client
openai_client = ChatCompletion(api_key=CHATKEY)

# Set up the button
#button = Button(BUTTON_PIN)

# Initialize Google Cloud client
client = speech.SpeechClient()

# Function to record audio
def record_audio():
    fs = 44100  # Sample rate
    vad = webrtcvad.Vad(1)  # Create a VAD object
    vad.set_mode(1)  # Level of aggressiveness from 0 to 3
    is_speech_started = False

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

def transcribe_audio_whisper(audio_data):
    model_name = 'whisper-1'
    
    #Converting audio input into binary
    question_input = audio_data
    question_file = open(audio_data, "rb")
    
    response = openai.Audio.transcribe(
        
        
    )

def ask_openai(question, openai_client):
    # Encouraging the model to provide a concise answer
    modified_prompt = f"Translate the following into clear and concise English and answer in one short message:\n\n{question}"

    # Using CHATGPT to get the  concise response
    response = openai_client.create(
        prompt=modified_prompt,
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=150, 
        stop=["\n"],    
        n=1,            
        presence_penalty=0, 
        frequency_penalty=0
    )
    
    return response.choices[0].text.strip()  # .text should be used instead of .message.content


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
#button.when_pressed = on_button_press

def on_keyboard_input(): #THIS IS FOR TESTING
    input("Press Enter to start recording...")
    audio_data = record_audio()
    question = transcribe_audio(audio_data)
    print(f"Question: {question}")
    answer = ask_openai(question, openai_client)
    print(f"Answer: {answer}")
    text_to_speech(answer)


# Run forever
print("Device is ready, press the button to ask a question.")
#while True:
#    pass

while True:
    on_keyboard_input()

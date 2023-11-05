
import sounddevice as sd
#from gpiozero import Button
from google.cloud import speech
from gtts import gTTS
import os
import openai
from openai import ChatCompletion
from scipy.io.wavfile import write

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
def record_audio(filename='recorded_audio.wav', duration=5, fs=44100):
    print("Recording...")

    # Record the audio
    audio_data = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait for the recording to finish

    # Save the audio to a file
    write(filename, fs, audio_data)

    print(f"Done recording. Saved as {filename}")
    return filename

def whisper_audio(audio_data):
    model_name = 'whisper-1'
    
    #Converting audio input into binary
    question_input = audio_data
    question_file = open(question_input, "rb")
    
    response = openai.Audio.transcribe(api_key = CHATKEY, model = model_name, file = question_file, response_format='srt')
    return response
    
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
    question = whisper_audio(audio_data)
    print(f"Question: {question}")
    answer = ask_openai(question)
    print(f"Answer: {answer}")
    text_to_speech(answer)
    
# Attach the button press event
#button.when_pressed = on_button_press

def on_keyboard_input(): #THIS IS FOR TESTING
    input("Press Enter to start recording...")
    audio_data = record_audio()
    question = whisper_audio(audio_data)
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

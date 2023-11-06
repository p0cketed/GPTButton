
import sounddevice as sd
#from gpiozero import Button
from google.cloud import texttospeech

import os
import openai
from scipy.io.wavfile import write
from pydub import AudioSegment
from pydub.playback import play

# Configuration
BUTTON_PIN = 17  # GPIO pin where the button is connected
LANGUAGE_CODE = 'en-US'  # Language code for Google Speech-to-Text

OPENAIKEY = os.getenv("OPENAI_API_KEY")
if not OPENAIKEY:
    raise ValueError("OPENAIKEY not functioning.\n")

DEVICE_INDEX = 1  # Device index for microphone if not default

#Google TTS client
client = texttospeech.TextToSpeechClient()

# Set up the button
#button = Button(BUTTON_PIN)

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
    
    response = openai.Audio.transcribe(api_key = OPENAIKEY, model = model_name, file = question_file, response_format='srt')
    return response
    
def ask_openai(question):
    # Using CHATGPT to get a concise response
    
    response = openai.ChatCompletion.create(
        messages = [
        {
            "role": "system",
            "content": "You are an AI knowledgeable in general facts and can provide very concise answers upon request."
        },
        {
            "role": "user",
            "content": f"{question}"
        }
    ],
        model="gpt-3.5-turbo",
        temperature=0.7,
        stop=None,
        n=1,
        max_tokens = 600,
        presence_penalty=0,
        frequency_penalty=0
    )

    # Extracting the text content from the response
    return response.choices[0].message['content'].strip()

# Function to convert text to speech using Google Cloud Text-to-Speech
def text_to_speech(text, lang=LANGUAGE_CODE, filename='response.mp3'):
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)

    # Build the voice request, here we are assuming a neutral gender
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang,
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )

    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # Perform the text-to-speech request on the text input with the selected voice parameters and audio file type
    response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

    # Save the audio to a file
    with open(filename, 'wb') as out:
        out.write(response.audio_content)
        print(f"Generated speech saved to {filename}")

    # Play the audio file
    sound = AudioSegment.from_mp3(filename)
    play(sound)


# Main function to handle the button press
def on_button_press():
    print("Button pressed!")
    audio_data = record_audio()
    question = whisper_audio(audio_data)
    print(f"Question: {question}")
    answer = ask_openai(question)
    print(f"Answer: {answer}")
    text_to_speech(answer)
    
# Attach the button press event working..
#button.when_pressed = on_button_press

def on_keyboard_input():  # THIS IS FOR TESTING
    input("Press Enter to start recording...")
    audio_filename = record_audio()
    question = whisper_audio(audio_filename)
    print(f"Question: {question}")
    answer = ask_openai(question)
    print(f"Answer: {answer}")
    text_to_speech(answer)
    os.remove(audio_filename)
    print(f"Deleted {audio_filename}")


# Run forever
print("Device is ready, press the button to ask a question.")
#while True:
#    pass

while True:
    on_keyboard_input()

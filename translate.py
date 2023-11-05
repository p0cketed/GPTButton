
import sounddevice as sd
#from gpiozero import Button
from gtts import gTTS
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
        max_tokens = 300,
        presence_penalty=0,
        frequency_penalty=0
    )

    # Extracting the text content from the response
    return response.choices[0].message['content'].strip()


def change_speed(sound, speed=4.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

# Function to convert text to speech
def text_to_speech(text, lang=LANGUAGE_CODE, filename='response.mp3', speed=1.0):
    tts = gTTS(text=text, lang=lang)
    tts.save(filename)
    sound = AudioSegment.from_mp3(filename)
    faster_sound = change_speed(sound, speed=speed)
    play(faster_sound)
    faster_sound.export(filename, format="mp3")  # Export the altered file if needed
    os.remove(filename)
    print(f"Deleted {filename}")

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

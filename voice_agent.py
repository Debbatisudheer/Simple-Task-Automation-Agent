# voice_agent.py
import sounddevice as sd
import numpy as np
import speech_recognition as sr

recognizer = sr.Recognizer()
WAKE_WORDS = ["hey jarvis", "jarvis"]
STOP_WORDS = ["stop listening", "go to sleep", "sleep", "bye", "exit"]

def listen_audio(seconds=4, sample_rate=16000):
    """Record audio using sounddevice"""
    audio = sd.rec(int(seconds * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    return audio

def transcribe(audio, sample_rate=16000):
    """Convert numpy audio to text"""
    try:
        audio_data = sr.AudioData(audio.tobytes(), sample_rate, 2)
        text = recognizer.recognize_google(audio_data).lower()
        return text
    except:
        return ""

def listen_for_wake_word():
    print("\n🎧 Waiting for wake word: 'Hey Jarvis' ...")
    while True:
        audio = listen_audio(3)
        text = transcribe(audio)

        if text:
            print(f"🗣 Heard: {text}")

        if any(word in text for word in WAKE_WORDS):
            print("✅ Wake word detected!")
            return True

def listen_continuous():
    """Listen continuously until stop phrase or silence timeout"""
    print("\n🎤 Continuous mode ON — speak freely... (say 'stop listening' to exit)")
    silence_frames = 0

    while True:
        audio = listen_audio(4)
        text = transcribe(audio)

        if not text:
            silence_frames += 1
            if silence_frames >= 2:   # ~8 sec silence
                print("😴 Silence detected — stopping continuous mode.")
                return None
            continue

        print(f"👉 Command: {text}")

        if any(stop in text for stop in STOP_WORDS):
            print("🛑 Stop phrase detected — exiting continuous mode.")
            return None

        yield text   # <-- sends text back to main.py

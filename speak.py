# speak.py (FINAL FIX WITH QUEUE)
import pyttsx3
import threading
import queue

engine = pyttsx3.init()
engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)

speech_queue = queue.Queue()

def _speech_worker():
    while True:
        text = speech_queue.get()
        if text is None:
            break
        print(f"🗣 Jarvis: {text}")
        engine.say(text)
        engine.runAndWait()
        speech_queue.task_done()

# start background speaking thread
speech_thread = threading.Thread(target=_speech_worker, daemon=True)
speech_thread.start()

def jarvis_say(text: str):
    speech_queue.put(text)

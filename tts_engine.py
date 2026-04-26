import pyttsx3
import threading
import queue

class TTSEngine:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.speaker_voices = {}  # Map speaker label to voice index
        self.msg_queue = queue.Queue()
        self.is_running = True
        
        # Start a background thread for TTS to avoid blocking the main transcription loop
        self.thread = threading.Thread(target=self._run_engine, daemon=True)
        self.thread.start()

    def _run_engine(self):
        """Internal loop to process TTS requests."""
        while self.is_running:
            try:
                speaker, text = self.msg_queue.get(timeout=1)
                self._speak(speaker, text)
                self.msg_queue.task_done()
            except queue.Empty:
                continue

    def _speak(self, speaker, text):
        """Assign voice and speak."""
        # Simple logic: Speaker 1 (or A) gets voice 0, Speaker 2 gets voice 1, etc.
        if speaker not in self.speaker_voices:
            voice_index = len(self.speaker_voices) % len(self.voices)
            self.speaker_voices[speaker] = self.voices[voice_index].id
            print(f"Assigning voice {voice_index} to {speaker}")

        self.engine.setProperty('voice', self.speaker_voices[speaker])
        # Slow down the rate a bit for clarity
        self.engine.setProperty('rate', 150)
        
        self.engine.say(text)
        self.engine.runAndWait()

    def speak_async(self, speaker, text):
        """Add a speak request to the queue."""
        self.msg_queue.put((speaker, text))

    def stop(self):
        self.is_running = False
        self.thread.join()

if __name__ == "__main__":
    # Test
    tts = TTSEngine()
    tts.speak_async("Speaker A", "Hello, I am speaker A.")
    tts.speak_async("Speaker B", "Hi there, I am speaker B.")
    import time
    time.sleep(5)

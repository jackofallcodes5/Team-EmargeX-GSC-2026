import sounddevice as sd
import queue
import sys

class AudioStream:
    def __init__(self, rate=16000, chunk=3200):
        self.rate = rate
        self.chunk = chunk
        self.q = queue.Queue()
        self.stream = sd.RawInputStream(
            samplerate=self.rate,
            blocksize=self.chunk,
            dtype='int16',
            channels=1,
            callback=self.callback
        )
        self.stream.start()

    def callback(self, indata, frames, time, status):
        """This is called for each audio block by sounddevice."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def get_audio_chunks(self):
        """Generator that yields audio data from the microphone."""
        try:
            while True:
                data = self.q.get()
                yield data
        except KeyboardInterrupt:
            pass
        finally:
            self.close()

    def close(self):
        self.stream.stop()
        self.stream.close()

if __name__ == "__main__":
    print("Recording... press Ctrl+C to stop.")
    stream = AudioStream()
    try:
        for chunk in stream.get_audio_chunks():
            print(f"Captured {len(chunk)} bytes", end="\r")
    except KeyboardInterrupt:
        print("\nStopped.")

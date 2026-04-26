# Sentinel Dispatch AI
### Real-Time Autonomous Emergency Response System (Desktop Prototype)

## 1. What It Does & How It Works
**Sentinel Dispatch AI** is an advanced, fully autonomous emergency call dispatch prototype. It acts as an artificial intelligence operator that listens to raw microphone traffic in real-time, extracts critical metadata, autonomously decides whether to dispatch emergency services, and updates a live situation map.

**How it works:**
1. **Audio Capture**: The system streams raw PCM audio from a microphone using the `sounddevice` library.
2. **Real-time ASR**: The audio is streamed into offline VOSK models, transcribing speech to text instantly while identifying distinct speakers through cosine similarity.
3. **Dual LLM Extraction**: 
    - The conversation history is passed to a primary Gemini AI which extracts a strict JSON schema containing incident details and generates an intelligent voice response.
    - A secondary Gemini instance runs concurrently to rapidly convert location descriptions into exact map coordinates.
4. **Desktop GUI**: Everything is rendered in a custom Tkinter UI featuring a live updating `tkintermapview`, scrolling parameter grids, dispatch panels, and text-to-speech feedback.
5. **Database Persistence**: The final payload is continuously routed to a local MySQL Database via UPSERT.

## 2. File Structure & Architecture
* **`gui_main.py`**: The core application window. Manages the Tkinter event loop, UI rendering, threading for background AI tasks, and a 10-second operator takeover timer.
* **`gemini_analyzer.py`**: Interfaces with the `google-genai` SDK to evaluate the transcription array, output the structured JSON emergency schema, and formulate AI voice responses.
* **`location_ai.py`**: A parallel AI task solely responsible for resolving extracted textual locations to Latitude and Longitude coordinates.
* **`vosk_handler.py`**: Interacts with the local VOSK machine-learning models to translate acoustic audio into text tokens and compute speaker vectors.
* **`speaker_manager.py`**: Tracks continuous cosine similarity between speaker embeddings to dynamically isolate and label speakers.
* **`audio_stream.py`**: Uses `sounddevice` to capture streaming audio from your default hardware.
* **`tts_engine.py`**: A `pyttsx3` text-to-speech integration allowing the AI system to provide real-time vocal feedback to the caller.
* **`mysql_logger.py`**: A local database logger using `mysql-connector-python` that performs UPSERT operations against the `sentinel_db`.
* **`database_setup.sql`**: The specific boilerplate SQL commands to build the database schema.

## 3. Technologies Stack
* **Language**: Python 3.14
* **UI Framework**: Tkinter, TkinterMapView
* **Speech & Biometrics**: VOSK Offline Models, `sounddevice`, Numpy (FFT Pitch processing)
* **Generative Models**: Google Gemini (`gemini-2.5-flash`) via `google-genai`
* **Databases**: MySQL (Local)

## 4. Setup & Running the Project
Please see the **`run.md`** file for step-by-step commands on how to install, configure, and launch this application!

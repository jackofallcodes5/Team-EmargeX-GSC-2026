# Emergency Call Autonomous Dispatch System (Tkinter Desktop)

## Overview

The **Emergency Call Autonomous Dispatch System** is a real-time speech analytics and transcription pipeline designed to act as an autonomous dispatch agent for emergency calls. It captures live audio, performs real-time speech-to-text (ASR) alongside speaker diarization, automatically analyzes the transcription context using Google's Gemini LLMs to make emergency dispatch decisions, and visually plots the incident on an interactive desktop application.

## Key Features

1. **Self-Contained Python GUI:** A fully custom, dark-themed Tkinter desktop window featuring live transcription, parameter grids, map views, and dispatch alert panels.
2. **Local Real-Time ASR & Diarization:** Uses VOSK with offline models to transcribe audio and compute speaker embeddings instantly.
3. **Dual AI Pipeline:** 
   - **Main Extractor:** Evaluates the nature of the emergency and generates a dynamic vocal reply for the caller.
   - **Location Extractor:** A parallel AI thread solely dedicated to resolving ambiguous geographic strings into precise Latitude/Longitude coordinates.
4. **Live Map Tracking:** Uses `tkintermapview` to drop pins dynamically the second an emergency location is identified from speech.
5. **Operator Takeover Logic:** Built-in 10-second timer rule. If an emergency location isn't rapidly captured by the AI, the interface triggers a "MANUAL TAKEOVER" state.
6. **Real-time Database Syncing:** Syncs the structured emergency JSON report asynchronously to a local MySQL Database (`sentinel_db`).

## System Architecture
See `diagrams.md` or `.drawio` files for complete graphical flowcharts and use cases.

The project scripts are divided into 4 main categories:

**Category 1: Core GUI & Application Logic**
*   **`gui_main.py`**: The primary UI window. It manages thread synchronization, Tkinter loop polling, the map widget, and rendering all visual components.
*   **`tts_engine.py`**: A `pyttsx3` text-to-speech integration allowing the AI system to provide real-time vocal feedback to the caller based on Gemini's `system_reply`.

**Category 2: Audio Capture & Speech Processing**
*   **`audio_stream.py`**: Handles microphone input streams using `sounddevice`, streaming byte chunks for processing.
*   **`vosk_handler.py`**: Manages the loading of local VOSK English and speaker models. Processes audio chunks to yield finalized text and speaker vectors.
*   **`speaker_manager.py`**: Receives VOSK speaker vectors (`spk`) and computes cosine similarity against known speakers.

**Category 3: Generative AI Pipelines**
*   **`gemini_analyzer.py`**: The main `gemini-2.5-flash` integrator. Feeds conversation history to extract a heavily structured JSON schema about the situation and generates a `system_reply`. Updates the shared `temp.json`.
*   **`location_ai.py`**: The second parallel AI instance. It specifically targets geographic text and resolves it to coordinates.

**Category 4: Databases & Configuration**
*   **`mysql_logger.py`**: Performs real-time UPSERT operations to log everything to a local MySQL server.
*   **`database_setup.sql`**: Contains the SQL tables definitions.

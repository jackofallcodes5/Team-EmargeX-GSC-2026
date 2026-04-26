"""
Sentinel Dispatch AI - Desktop Emergency Response Prototype
============================================================
Single-window Tkinter application demonstrating AI-first emergency response.
"""

import tkinter as tk
from tkinter import font as tkfont
import tkintermapview
import threading
import json
import time
import uuid
import os
import sys
import queue
import numpy as np
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from audio_stream import AudioStream
from vosk_handler import VoskHandler
from speaker_manager import SpeakerManager
from gemini_analyzer import GeminiAnalyzer
from location_ai import LocationAnalyzer
from mysql_logger import MySQLLogger
from tts_engine import TTSEngine

# ═══════════════════════════════════════════════════════════
# Theme
# ═══════════════════════════════════════════════════════════
C = {
    "root": "#080c14", "surface": "#0f1629", "card": "#162040",
    "card2": "#1c2d4f", "input": "#1a2744",
    "blue": "#4f8cff", "red": "#ff4f6d", "green": "#00e68a",
    "amber": "#ffb84d", "cyan": "#00d4ff", "purple": "#a855f7",
    "txt": "#f0f4ff", "txt2": "#c8d6e5", "dim": "#7a8ba8",
    "border": "#2a3a5c", "danger_bg": "#2d1320",
    "success_bg": "#0d2818", "warn_bg": "#2d2213",
}
FONT = "Segoe UI"
MONO = "Consolas"
TAKEOVER_SEC = 10
ANALYSIS_COOLDOWN = 4
POLL_MS = 500
TEMP_JSON = "temp.json"

# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def get_seq_id():
    f = "situation_seq.txt"
    if not os.path.exists(f):
        open(f, "w").write("1000")
    seq = int(open(f).read().strip())
    open(f, "w").write(str(seq + 1))
    return f"SIT-{seq}"


def detect_gender(chunk):
    try:
        d = np.frombuffer(chunk, dtype=np.int16)
        if len(d) == 0: return "Unknown"
        w = np.fft.fft(d)
        fr = np.fft.fftfreq(len(w), 1.0 / 16000)
        idx = np.where((fr > 80) & (fr < 300))[0]
        if len(idx) == 0: return "Unknown"
        peak = fr[idx[np.argmax(np.abs(w[idx]))]]
        if 85 <= peak < 165: return "Male"
        elif 165 <= peak <= 255: return "Female"
    except Exception:
        pass
    return "Unknown"

# ═══════════════════════════════════════════════════════════
# Parameter display configuration
# ═══════════════════════════════════════════════════════════
PARAM_FIELDS = [
    ("emergency_category",      "Category"),
    ("emergency_sub_type",      "Sub-Type"),
    ("severity_level",          "Severity"),
    ("incident_description",    "Description"),
    ("caller_name",             "Caller Name"),
    ("caller_contact_number",   "Contact #"),
    ("caller_gender",           "Gender"),
    ("reporter_type",           "Reporter"),
    ("state",                   "State"),
    ("district_city",           "District/City"),
    ("locality_area",           "Locality"),
    ("pin_code",                "PIN Code"),
    ("threat_to_human_life",    "Life Threat"),
    ("number_of_casualties",    "Casualties"),
    ("number_of_injuries",      "Injuries"),
    ("weapon_hazard_involved",  "Weapon/Hazard"),
]


class SentinelApp:
    """Main desktop application."""

    def __init__(self, root):
        self.root = root
        self.root.title("Sentinel Dispatch AI")
        self.root.geometry("1520x960")
        self.root.minsize(1200, 750)
        self.root.configure(bg=C["root"])

        # Shared state
        self.lock = threading.Lock()
        self.history = []
        self.txt_queue = queue.Queue()
        self.params = {}
        self.coords = (None, None)
        self.dispatches = []

        # Session
        self.doc_id = str(uuid.uuid4())
        self.seq_id = get_seq_id()

        # Flags
        self.running = True
        self.first_speech_ts = None
        self.loc_resolved = False
        self.op_takeover = False
        self.ai_state = "Initializing"
        self.last_analysis = 0
        self.last_loc_text = ""
        self.last_reply = ""
        self.marker = None
        self.pulse_on = True

        # Build UI
        self._build()

        # Init temp.json
        with open(TEMP_JSON, "w") as f:
            json.dump({}, f)

        # Delayed backend start
        self.root.after(800, self._start_backend)
        self.root.after(POLL_MS, self._poll)
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

    # ───────────────────────────────────────────────
    # UI Build
    # ───────────────────────────────────────────────
    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self.root, bg=C["surface"], height=64)
        hdr.pack(fill="x", padx=0, pady=0)
        hdr.pack_propagate(False)

        # Logo
        tk.Label(hdr, text="🛡  SENTINEL DISPATCH AI", font=(FONT, 16, "bold"),
                 fg=C["cyan"], bg=C["surface"]).pack(side="left", padx=20)

        # Session
        tk.Label(hdr, text=f"Session: {self.seq_id}  |  ID: {self.doc_id[:8]}…",
                 font=(FONT, 9), fg=C["dim"], bg=C["surface"]).pack(side="right", padx=20)

        # Status cluster
        sf = tk.Frame(hdr, bg=C["surface"])
        sf.pack(side="right", padx=30)

        self.lbl_ai = tk.Label(sf, text="● Initializing", font=(FONT, 11, "bold"),
                               fg=C["amber"], bg=C["surface"])
        self.lbl_ai.pack(side="left", padx=12)

        self.lbl_timer = tk.Label(sf, text="⏱ 00:00", font=(MONO, 11),
                                  fg=C["txt2"], bg=C["surface"])
        self.lbl_timer.pack(side="left", padx=12)

        self.lbl_op = tk.Label(sf, text="👤 Operator: Standby", font=(FONT, 11),
                               fg=C["dim"], bg=C["surface"])
        self.lbl_op.pack(side="left", padx=12)

        self.btn_takeover = tk.Button(sf, text="MANUAL TAKEOVER", font=(FONT, 9, "bold"),
                                      bg=C["red"], fg="#ffffff", relief="flat",
                                      command=self._manual_takeover, cursor="hand2")
        self.btn_takeover.pack(side="left", padx=(0, 10))

        # ── Separator ──
        tk.Frame(self.root, bg=C["blue"], height=2).pack(fill="x")

        # ── Main body ──
        body = tk.Frame(self.root, bg=C["root"])
        body.pack(fill="both", expand=True, padx=8, pady=8)

        # Left: Map
        left = tk.Frame(body, bg=C["card"], bd=0, highlightthickness=1,
                        highlightbackground=C["border"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 4))

        map_hdr = tk.Frame(left, bg=C["card"])
        map_hdr.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(map_hdr, text="📍  Live Emergency Map", font=(FONT, 13, "bold"),
                 fg=C["txt"], bg=C["card"]).pack(side="left")
        self.lbl_coords = tk.Label(map_hdr, text="Lat: --  |  Lon: --",
                                   font=(MONO, 10), fg=C["cyan"], bg=C["card"])
        self.lbl_coords.pack(side="right")

        self.map = tkintermapview.TkinterMapView(left, corner_radius=0)
        self.map.pack(fill="both", expand=True, padx=10, pady=10)
        self.map.set_position(20.5937, 78.9629)  # Default: India center
        self.map.set_zoom(5)

        # Right column
        right = tk.Frame(body, bg=C["root"], width=460)
        right.pack(side="right", fill="both", padx=(4, 0))
        right.pack_propagate(False)

        # ── Parameters panel ──
        pf = tk.Frame(right, bg=C["card"], highlightthickness=1,
                      highlightbackground=C["border"])
        pf.pack(fill="both", expand=True, pady=(0, 4))

        tk.Label(pf, text="📋  Emergency Parameters", font=(FONT, 13, "bold"),
                 fg=C["txt"], bg=C["card"]).pack(anchor="w", padx=12, pady=(10, 6))

        tk.Frame(pf, bg=C["border"], height=1).pack(fill="x", padx=10)

        self.param_canvas = tk.Canvas(pf, bg=C["card"], highlightthickness=0)
        self.param_scroll = tk.Scrollbar(pf, orient="vertical", command=self.param_canvas.yview)
        self.param_inner = tk.Frame(self.param_canvas, bg=C["card"])

        self.param_inner.bind("<Configure>",
            lambda e: self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all")))
        self.param_canvas.create_window((0, 0), window=self.param_inner, anchor="nw")
        self.param_canvas.configure(yscrollcommand=self.param_scroll.set)
        self.param_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=6)
        self.param_scroll.pack(side="right", fill="y", pady=6)

        self.param_labels = {}
        for i, (key, label) in enumerate(PARAM_FIELDS):
            bg = C["card"] if i % 2 == 0 else C["card2"]
            row = tk.Frame(self.param_inner, bg=bg)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=label, font=(FONT, 10, "bold"), fg=C["dim"],
                     bg=bg, width=14, anchor="w").pack(side="left", padx=(8, 4), pady=3)
            vl = tk.Label(row, text="--", font=(FONT, 10), fg=C["txt2"],
                          bg=bg, anchor="w", wraplength=260, justify="left")
            vl.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=3)
            self.param_labels[key] = vl

        # ── Dispatches panel ──
        df = tk.Frame(right, bg=C["card"], highlightthickness=1,
                      highlightbackground=C["border"], height=200)
        df.pack(fill="x", pady=(4, 0))
        df.pack_propagate(False)

        tk.Label(df, text="🚨  Alerted Dispatches", font=(FONT, 13, "bold"),
                 fg=C["txt"], bg=C["card"]).pack(anchor="w", padx=12, pady=(10, 6))
        tk.Frame(df, bg=C["border"], height=1).pack(fill="x", padx=10)

        self.dispatch_text = tk.Text(df, bg=C["card"], fg=C["txt2"], font=(FONT, 10),
                                     relief="flat", wrap="word", state="disabled",
                                     highlightthickness=0)
        self.dispatch_text.pack(fill="both", expand=True, padx=12, pady=8)
        self.dispatch_text.tag_configure("alert", foreground=C["red"], font=(FONT, 10, "bold"))
        self.dispatch_text.tag_configure("reason", foreground=C["amber"])
        self.dispatch_text.tag_configure("ok", foreground=C["green"])

        # ── Transcript panel ──
        tf = tk.Frame(self.root, bg=C["card"], highlightthickness=1,
                      highlightbackground=C["border"])
        tf.pack(fill="x", padx=8, pady=(0, 8))

        tf_hdr = tk.Frame(tf, bg=C["card"])
        tf_hdr.pack(fill="x", padx=12, pady=(8, 4))
        tk.Label(tf_hdr, text="📝  Live Transcript", font=(FONT, 13, "bold"),
                 fg=C["txt"], bg=C["card"]).pack(side="left")
        self.lbl_partial = tk.Label(tf_hdr, text="", font=(FONT, 9, "italic"),
                                    fg=C["dim"], bg=C["card"])
        self.lbl_partial.pack(side="right")

        tk.Frame(tf, bg=C["border"], height=1).pack(fill="x", padx=10)

        self.transcript = tk.Text(tf, bg=C["input"], fg=C["txt2"], font=(MONO, 10),
                                  relief="flat", wrap="word", height=8, state="disabled",
                                  highlightthickness=0, insertbackground=C["txt"])
        self.transcript.pack(fill="x", padx=12, pady=(4, 10))
        self.transcript.tag_configure("speaker", foreground=C["cyan"], font=(MONO, 10, "bold"))
        self.transcript.tag_configure("system", foreground=C["amber"], font=(MONO, 10, "italic"))

    # ───────────────────────────────────────────────
    # Backend
    # ───────────────────────────────────────────────
    def _start_backend(self):
        """Initialize heavy components in a background thread."""
        threading.Thread(target=self._init_components, daemon=True).start()

    def _init_components(self):
        self._set_status("Initializing", C["amber"])
        try:
            self._log("Initializing VOSK speech recognition…")
            self.vosk = VoskHandler()
            self._log("Initializing speaker identification…")
            self.speaker_mgr = SpeakerManager(threshold=0.8)
            self._log("Initializing Gemini analyzer…")
            self.gemini = GeminiAnalyzer()
            self._log("Initializing Location AI…")
            self.location_ai = LocationAnalyzer()
            self._log("Initializing MySQL logger…")
            self.mysql = MySQLLogger()
            self._log("Initializing TTS engine…")
            self.tts = TTSEngine()
            self._log("Opening microphone…")
            self.audio = AudioStream()
            self._log("✓ System ready — Listening for emergency calls")
            self._set_status("Listening", C["green"])

            # Launch worker threads
            threading.Thread(target=self._audio_loop, daemon=True).start()
            threading.Thread(target=self._analysis_loop, daemon=True).start()
            threading.Thread(target=self._location_loop, daemon=True).start()
        except Exception as e:
            self._log(f"✗ Initialization failed: {e}")
            self._set_status("Error", C["red"])

    def _set_status(self, text, color):
        self.ai_state = text
        self.root.after(0, lambda: self.lbl_ai.configure(text=f"● {text}", fg=color))

    def _log(self, msg):
        """Append a system message to the transcript."""
        self.txt_queue.put(("system", msg))

    # ───────────────────────────────────────────────
    # Audio Loop (Thread 2)
    # ───────────────────────────────────────────────
    def _audio_loop(self):
        last_partial = ""
        for chunk in self.audio.get_audio_chunks():
            if not self.running:
                break
            gender = detect_gender(chunk)
            g_tag = f" ({gender})" if gender != "Unknown" else ""
            text, spk_vec = self.vosk.process_chunk(chunk)

            if text:
                label = self.speaker_mgr.get_speaker_label(spk_vec) + g_tag
                utterance = f"[{label}]: {text}"
                with self.lock:
                    self.history.append(utterance)
                    if self.first_speech_ts is None:
                        self.first_speech_ts = time.time()
                self.txt_queue.put(("speech", utterance))
                last_partial = ""
            else:
                partial = self.vosk.get_partial()
                if partial and partial != last_partial:
                    self.txt_queue.put(("partial", partial))
                    last_partial = partial

    # ───────────────────────────────────────────────
    # Analysis Loop (Thread 3) — Main Gemini
    # ───────────────────────────────────────────────
    def _analysis_loop(self):
        analyzed_len = 0
        while self.running:
            time.sleep(1)
            with self.lock:
                cur_len = len(self.history)
                if cur_len <= analyzed_len:
                    continue
                if time.time() - self.last_analysis < ANALYSIS_COOLDOWN:
                    continue
                snapshot = list(self.history)

            self.last_analysis = time.time()
            self._set_status("Analyzing", C["purple"])

            now = datetime.now()
            result = self.gemini.analyze_conversation(snapshot)
            if result:
                result["situation_id"] = self.seq_id
                result["report_date"] = now.strftime("%Y-%m-%d")
                result["report_time"] = now.strftime("%H:%M:%S")
                result["conversation_history"] = snapshot

                # TTS AI Response
                reply = result.get("system_reply")
                if reply and reply != self.last_reply and not self.op_takeover:
                    self.last_reply = reply
                    self._log(f"AI: {reply}")
                    try:
                        self.tts.speak_async("AI", reply)
                    except Exception as e:
                        print(f"TTS Error: {e}")

                with self.lock:
                    self.params = dict(result)
                    # Check dispatch
                    if result.get("dispatch_needed"):
                        reason = result.get("dispatch_reason", "Emergency dispatch required")
                        cat = result.get("emergency_category", "General")
                        entry = f"🚨 {cat} — {reason}"
                        if entry not in self.dispatches:
                            self.dispatches.append(entry)

                # Write to MySQL
                try:
                    self.mysql.log_report(self.doc_id, result)
                except Exception as e:
                    print(f"[MySQL] {e}")

                analyzed_len = cur_len

            self._set_status("Listening", C["green"])

    # ───────────────────────────────────────────────
    # Location Loop (Thread 4) — Second AI
    # ───────────────────────────────────────────────
    def _location_loop(self):
        while self.running:
            time.sleep(2)
            with self.lock:
                loc_parts = [
                    self.params.get("locality_area"),
                    self.params.get("district_city"),
                    self.params.get("state"),
                    self.params.get("pin_code"),
                ]
            loc_text = ", ".join([p for p in loc_parts if p and p != "null"])
            if not loc_text or loc_text == self.last_loc_text:
                continue
            self.last_loc_text = loc_text
            self._log(f"🌐 Resolving location: {loc_text}")

            lat, lon = self.location_ai.resolve_coordinates(loc_text)
            if lat is not None and lon is not None:
                with self.lock:
                    self.coords = (lat, lon)
                    self.loc_resolved = True
                    self.params["latitude"] = lat
                    self.params["longitude"] = lon
                self._log(f"📍 Coordinates: {lat:.4f}, {lon:.4f}")

                # Update temp.json with coords
                try:
                    with open(TEMP_JSON, "r") as f:
                        data = json.load(f)
                    data["latitude"] = lat
                    data["longitude"] = lon
                    with open(TEMP_JSON, "w") as f:
                        json.dump(data, f, indent=2)
                except Exception:
                    pass

    # ───────────────────────────────────────────────
    # UI Polling (Main Thread)
    # ───────────────────────────────────────────────
    def _poll(self):
        if not self.running:
            return

        # ── Process transcript queue ──
        while not self.txt_queue.empty():
            kind, msg = self.txt_queue.get_nowait()
            if kind == "partial":
                self.lbl_partial.configure(text=f"… {msg}")
            elif kind == "speech":
                self.lbl_partial.configure(text="")
                self.transcript.configure(state="normal")
                self.transcript.insert("end", msg + "\n", "speaker")
                self.transcript.see("end")
                self.transcript.configure(state="disabled")
            elif kind == "system":
                self.transcript.configure(state="normal")
                self.transcript.insert("end", f"[System] {msg}\n", "system")
                self.transcript.see("end")
                self.transcript.configure(state="disabled")

        # ── Update parameters panel ──
        with self.lock:
            p = dict(self.params)
            lat, lon = self.coords
            d_list = list(self.dispatches)

        for key, _ in PARAM_FIELDS:
            val = p.get(key)
            display = str(val) if val and str(val).lower() != "null" else "--"
            lbl = self.param_labels.get(key)
            if lbl:
                lbl.configure(text=display)
                # Color severity
                if key == "severity_level" and display != "--":
                    color = {"Critical": C["red"], "High": C["amber"],
                             "Medium": C["cyan"], "Low": C["green"]}.get(display, C["txt2"])
                    lbl.configure(fg=color)

        # ── Update coordinates + map ──
        if lat is not None and lon is not None:
            self.lbl_coords.configure(text=f"Lat: {lat:.4f}  |  Lon: {lon:.4f}")
            if self.marker:
                self.marker.delete()
            self.marker = self.map.set_marker(lat, lon, text="🚨 Emergency")
            self.map.set_position(lat, lon)
            self.map.set_zoom(14)

        # ── Update dispatches ──
        self.dispatch_text.configure(state="normal")
        self.dispatch_text.delete("1.0", "end")
        if d_list:
            for d in d_list:
                self.dispatch_text.insert("end", d + "\n", "alert")
        else:
            self.dispatch_text.insert("end", "No active dispatches", "ok")
        self.dispatch_text.configure(state="disabled")

        # ── Timer + Operator Takeover ──
        if self.first_speech_ts:
            elapsed = time.time() - self.first_speech_ts
            mins = int(elapsed) // 60
            secs = int(elapsed) % 60
            self.lbl_timer.configure(text=f"⏱ {mins:02d}:{secs:02d}")

            if not self.loc_resolved and elapsed > TAKEOVER_SEC and not self.op_takeover:
                self._manual_takeover()
                self._log("⚠ Location not resolved — OPERATOR TAKEOVER activated")
            elif self.loc_resolved and self.op_takeover:
                self.lbl_op.configure(text="👤 Operator: Resolved ✓", fg=C["green"])
            elif self.loc_resolved:
                self.lbl_op.configure(text="👤 Operator: Standby ✓", fg=C["green"])

        # ── Pulse the AI status indicator ──
        if self.ai_state == "Listening":
            self.pulse_on = not self.pulse_on
            fg = C["green"] if self.pulse_on else C["dim"]
            self.lbl_ai.configure(fg=fg)

        self.root.after(POLL_MS, self._poll)

    def _manual_takeover(self):
        """Handle human operator taking over the call."""
        if not self.op_takeover:
            self.op_takeover = True
            self.lbl_op.configure(text="👤 Operator: TAKEOVER", fg=C["red"])
            self.btn_takeover.configure(state="disabled", bg=C["danger_bg"], text="ACTIVE")
            self._log("⚠ Manual operator takeover initiated. AI speech output disabled.")
            if hasattr(self, "tts"):
                try:
                    self.tts.speak_async("System", "Human operator has taken over the call.")
                except Exception:
                    pass

    # ───────────────────────────────────────────────
    # Shutdown
    # ───────────────────────────────────────────────
    def _shutdown(self):
        self.running = False
        try:
            if hasattr(self, "audio"):
                self.audio.close()
            if hasattr(self, "tts"):
                self.tts.stop()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SentinelApp(root)
    root.mainloop()

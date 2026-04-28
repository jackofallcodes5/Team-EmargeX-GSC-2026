# ═══════════════════════════════════════════════════════════
# Sentinel Dispatch Emergency AI — Dockerfile
# ═══════════════════════════════════════════════════════════
# Builds a containerized desktop GUI environment accessible
# via noVNC at http://localhost:6080
# ═══════════════════════════════════════════════════════════

FROM python:3.14-slim

LABEL maintainer="Team EmargeX"
LABEL description="Sentinel Dispatch Emergency AI — Containerized Desktop GUI"

# ── Prevent interactive prompts during apt-get ─────────────
ENV DEBIAN_FRONTEND=noninteractive

# ── Install system dependencies ────────────────────────────
# Categories:
#   - X11 / Display:  xvfb, x11vnc, fluxbox
#   - noVNC:          novnc, websockify (browser-based VNC)
#   - Tkinter:        python3-tk, tcl, tk
#   - Audio:          libportaudio2, libasound2-dev, pulseaudio
#   - TTS:            espeak, espeak-ng, libespeak-dev
#   - Fonts:          fonts-dejavu-core (cross-platform)
#   - Build tools:    gcc (for native Python extensions)
#   - Network:        net-tools, procps (debugging)
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Virtual display & VNC
    xvfb \
    x11vnc \
    fluxbox \
    novnc \
    websockify \
    # Tkinter support
    python3-tk \
    tcl \
    tk \
    # Audio libraries (for sounddevice / PortAudio)
    libportaudio2 \
    portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    pulseaudio \
    # Text-to-Speech (pyttsx3 Linux backend)
    espeak \
    espeak-ng \
    libespeak-dev \
    # Fonts
    fonts-dejavu-core \
    fonts-dejavu-extra \
    # Build tools for pip packages with C extensions
    gcc \
    g++ \
    # Utilities
    procps \
    net-tools \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Set up working directory ───────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────
# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy the full project ─────────────────────────────────
COPY . .

# ── Ensure startup script is executable ────────────────────
RUN chmod +x start.sh

# ── Initialize runtime files ──────────────────────────────
RUN echo '{}' > temp.json \
    && (test -f situation_seq.txt || echo '1000' > situation_seq.txt)

# ── Environment variables ─────────────────────────────────
ENV DISPLAY=:1
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

# ── Expose ports ──────────────────────────────────────────
# 6080 = noVNC web interface (browser access)
# 5900 = VNC direct connection (optional, for VNC clients)
EXPOSE 6080
EXPOSE 5900

# ── Health check ──────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:6080/ || exit 1

# ── Launch ────────────────────────────────────────────────
CMD ["bash", "start.sh"]

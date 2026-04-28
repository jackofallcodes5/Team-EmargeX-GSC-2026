# Running Sentinel Dispatch in Docker

This guide explains how to build and run the **Sentinel Dispatch Emergency AI** desktop application inside a Docker container. The GUI is rendered inside the container and streamed to your browser via **noVNC** — no extra software needed on your machine.

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Docker Desktop** | [Download here](https://www.docker.com/products/docker-desktop/). Make sure it is **running** before proceeding. |
| **Gemini API Key** | At least one Google Gemini API key. Get one at [Google AI Studio](https://aistudio.google.com/). |
| **MySQL** *(optional)* | A running MySQL instance if you want database logging. The app works without it (logs a warning). |

---

## Quick Start (3 Steps)

### Step 1 — Configure Environment Variables

Copy the template and fill in your keys:

```bash
# On Windows (PowerShell)
copy .env.template .env

# On Mac/Linux
cp .env.template .env
```

Edit the `.env` file with your actual values:

```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_API_KEY_2=your_actual_second_key_or_same_key
DB_HOST=host.docker.internal
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=sentinel_db
```

> **Important:** If your MySQL server runs on your host machine (not in Docker), set `DB_HOST=host.docker.internal` on Windows/macOS, or `DB_HOST=172.17.0.1` on Linux.

### Step 2 — Build the Docker Image

```bash
docker build -t sentinel-dispatch .
```

This will:
- Download the Python 3.14 base image
- Install system packages (display server, audio, fonts, TTS)
- Install all Python dependencies
- Copy the project files including Vosk models

> **Note:** The first build may take **5–10 minutes** depending on your internet speed. Subsequent builds are cached and much faster.

### Step 3 — Run the Container

```bash
docker run -d -p 6080:6080 --env-file .env --name sentinel sentinel-dispatch
```

Then open your browser and go to:

### 👉 **http://localhost:6080/vnc.html?autoconnect=true**

You should see the Sentinel Dispatch Emergency AI desktop window.

---

## Detailed Usage

### Viewing Container Logs

To see what the container is doing:

```bash
docker logs -f sentinel
```

You should see output like:

```
══════════════════════════════════════════════════════
  Sentinel Dispatch Emergency AI — Docker Runtime
══════════════════════════════════════════════════════
[1/5] Starting Xvfb virtual display (1600x1024x24)...
[2/5] Starting Fluxbox window manager...
[3/5] Starting x11vnc on port 5900...
[4/5] Starting noVNC web interface on port 6080...
[5/5] Launching Sentinel Dispatch GUI...
  ✓ Ready! Open your browser:
    http://localhost:6080/vnc.html?autoconnect=true
```

### Stopping the Container

```bash
docker stop sentinel
```

### Restarting the Container

```bash
docker start sentinel
```

### Removing the Container (to rebuild)

```bash
docker rm -f sentinel
```

### Changing the Screen Resolution

The default resolution is `1600x1024`. To change it:

```bash
docker run -d -p 6080:6080 --env-file .env \
  -e SCREEN_RESOLUTION=1920x1080x24 \
  --name sentinel sentinel-dispatch
```

### Using a VNC Client Instead of Browser

If you prefer a dedicated VNC client (like RealVNC or TigerVNC), connect to:

```
localhost:5900
```

To expose this port, add `-p 5900:5900` to the run command:

```bash
docker run -d -p 6080:6080 -p 5900:5900 --env-file .env --name sentinel sentinel-dispatch
```

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | **Yes** | Primary Gemini API key for conversation analysis |
| `GEMINI_API_KEY_2` | No | Secondary key for location AI (falls back to primary) |
| `FIREBASE_CREDENTIALS_PATH` | No | Path to Firebase credentials file |
| `DB_HOST` | No | MySQL host. Use `host.docker.internal` for host DB |
| `DB_USER` | No | MySQL username (default: `root`) |
| `DB_PASSWORD` | No | MySQL password |
| `DB_NAME` | No | MySQL database name (default: `sentinel_db`) |

You can also pass variables individually:

```bash
docker run -d -p 6080:6080 \
  -e GEMINI_API_KEY=your_key_here \
  -e GEMINI_API_KEY_2=your_key_here \
  -e DB_HOST=host.docker.internal \
  -e DB_USER=root \
  -e DB_PASSWORD=mypass \
  -e DB_NAME=sentinel_db \
  --name sentinel sentinel-dispatch
```

---

## Mounting Local Files

### Mount a custom `.env` file

```bash
docker run -d -p 6080:6080 \
  -v "$(pwd)/.env:/app/.env:ro" \
  --name sentinel sentinel-dispatch
```

### Mount custom Vosk models

If you have different or updated Vosk model directories:

```bash
docker run -d -p 6080:6080 --env-file .env \
  -v "/path/to/your/model:/app/model:ro" \
  -v "/path/to/your/model-spk:/app/model-spk:ro" \
  --name sentinel sentinel-dispatch
```

### Mount a volume for persistent data

To persist `temp.json` and `situation_seq.txt` across restarts:

```bash
docker run -d -p 6080:6080 --env-file .env \
  -v sentinel-data:/app/data \
  --name sentinel sentinel-dispatch
```

---

## Setting Up the MySQL Database

If you want database logging to work:

1. Make sure MySQL is running on your host machine.
2. Create the database by running the setup script:

```bash
mysql -u root -p < database_setup.sql
```

3. Set `DB_HOST=host.docker.internal` in your `.env` file (or `172.17.0.1` on Linux).
4. Ensure your MySQL instance allows connections from Docker's network.

> **Tip:** If you get connection refused errors, check that MySQL is listening on `0.0.0.0` (not just `127.0.0.1`). You may need to update `bind-address` in your MySQL config.

---

## Troubleshooting

### "Cannot connect to display" or blank screen

**Cause:** Xvfb failed to start or the display environment isn't set correctly.

**Fix:** Check container logs:
```bash
docker logs sentinel
```
Look for errors in steps 1–4. If Xvfb failed, try rebuilding:
```bash
docker rm -f sentinel
docker build --no-cache -t sentinel-dispatch .
```

### Browser shows "noVNC: Connection refused"

**Cause:** The container may still be starting up, or port 6080 is already in use.

**Fix:**
- Wait 10–15 seconds and refresh the page.
- Check if another process is using port 6080:
  ```bash
  # Windows
  netstat -ano | findstr 6080
  # Mac/Linux
  lsof -i :6080
  ```
- Use a different port: `-p 8080:6080` and open `http://localhost:8080`.

### MySQL connection errors

**Cause:** The container cannot reach your host MySQL instance.

**Fix:**
- Use `DB_HOST=host.docker.internal` (Docker Desktop on Windows/macOS)
- Use `DB_HOST=172.17.0.1` (Linux)
- Ensure MySQL is running and the database `sentinel_db` exists
- Check firewall rules aren't blocking Docker's network

### "GEMINI_API_KEY not found" warning

**Cause:** The `.env` file wasn't passed to the container.

**Fix:** Make sure you include `--env-file .env` in your run command, or pass the key directly with `-e GEMINI_API_KEY=your_key`.

### Microphone / Audio not working

**Cause:** Docker containers don't have direct access to host audio hardware by default.

**Fix:** The app will run and display the full GUI, but live microphone capture requires audio passthrough. For demo purposes, the app initializes and shows all UI panels. For live audio, run the app directly on your host machine (see `run.md`).

### Fonts look wrong or are too small

**Cause:** Font rendering differences between host and container.

**Fix:** The container includes DejaVu fonts which provide good cross-platform rendering. If text appears too small, try increasing the screen resolution:
```bash
docker run -d -p 6080:6080 --env-file .env \
  -e SCREEN_RESOLUTION=1920x1080x24 \
  --name sentinel sentinel-dispatch
```

### Container exits immediately

**Cause:** A startup error caused the application to crash.

**Fix:**
```bash
# Check exit logs
docker logs sentinel

# Run interactively to debug
docker run -it -p 6080:6080 --env-file .env sentinel-dispatch bash
# Then inside the container:
bash start.sh
```

---

## Architecture Overview

```
Your Machine                          Docker Container
┌─────────────┐                  ┌──────────────────────────┐
│             │   HTTP :6080     │  Xvfb (Virtual Display)  │
│  Browser    │ ◄──────────────► │       ↕                  │
│             │                  │  Fluxbox (Window Mgr)    │
│             │                  │       ↕                  │
└─────────────┘                  │  gui_main.py (Tkinter)   │
                                 │       ↕                  │
                                 │  x11vnc → noVNC/wsproxy  │
                                 │                          │
                                 │  Python 3.14 + All deps  │
                                 └──────────────────────────┘
```

The desktop GUI renders inside a virtual display (`Xvfb`), which is captured by `x11vnc` and streamed through `noVNC` to your browser over a WebSocket connection on port 6080.

---

## Command Cheat Sheet

| Action | Command |
|---|---|
| Build image | `docker build -t sentinel-dispatch .` |
| Run container | `docker run -d -p 6080:6080 --env-file .env --name sentinel sentinel-dispatch` |
| Open GUI | `http://localhost:6080/vnc.html?autoconnect=true` |
| View logs | `docker logs -f sentinel` |
| Stop | `docker stop sentinel` |
| Start again | `docker start sentinel` |
| Remove | `docker rm -f sentinel` |
| Rebuild clean | `docker build --no-cache -t sentinel-dispatch .` |
| Shell into container | `docker exec -it sentinel bash` |

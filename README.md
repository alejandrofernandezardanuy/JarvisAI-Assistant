# JARVIS

> A fully local, wake-word activated AI voice assistant with an Iron Man-style HUD.

![Python](https://img.shields.io/badge/python-3.11-blue) ![Ollama](https://img.shields.io/badge/LLM-llama3.2-green) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey) ![License](https://img.shields.io/badge/license-MIT-orange)

---

## Overview

JARVIS is a personal AI assistant that runs entirely on your machine. It listens for a wake word, understands natural language via a local LLM, responds with voice synthesis, and displays its state through a custom animated HUD — no cloud required for the core AI.

---

## What JARVIS Can Do

### Music
- Play any song, artist or genre on Spotify
- Pause, resume, skip to next or previous track

### Communication
- Read unread Gmail emails aloud
- Send emails to saved contacts by voice
- Check upcoming Google Calendar events
- Create new calendar events by voice

### Navigation
- Calculate driving time and distance to any destination
- Open the route directly in Google Maps

### Information
- Real-time weather for any city
- Latest news headlines by category (tech, sports, economy, international)
- Current time and date

### System Control
- Raise, lower or mute system volume
- Set precise volume level by percentage
- Check CPU usage, RAM and battery status
- Take screenshots saved to the desktop
- Open File Explorer, minimize/maximize/close windows
- Copy and paste via voice

### Browser & Apps
- Search Google by voice
- Navigate to any URL
- Open and close Chrome tabs
- Scroll pages up and down
- Open Spotify, Discord, Chrome or any website by voice
- Close running applications by voice

### Productivity
- Set timers by voice ("set a 20 minute timer")
- Free conversation with the local LLM for any question or task
- Persistent conversation history across sessions

### Visual HUD
- Iron Man-style fullscreen interface with animated particle orb
- Real-time system metrics (CPU, RAM) and clock on screen
- Compact floating top bar mode that stays visible while you work
- `Alt+C` toggles between fullscreen and compact mode
- Orb animation changes based on assistant state

---

## HUD States

| State | Animation |
|---|---|
| Idle | Slow organic pulse with neural rays from center |
| Listening | Expanding ripples, high energy |
| Processing | 8 independent atomic rings spinning on different axes |
| Speaking | Surface waves traveling across the orb + concentric ripples |

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Ollama + llama3.2 |
| Wake word | openwakeword (ONNX) |
| STT | SpeechRecognition + Google Speech |
| TTS | Edge TTS |
| HUD | PyQt6 |
| State server | Flask + SocketIO |
| Integrations | Spotify, Gmail, Google Calendar, Maps, OpenWeatherMap |

---

## Getting Started

```bash
git clone https://github.com/tu-usuario/jarvis.git
cd jarvis
python -m venv venv311
venv311\Scripts\activate
pip install -r requirements.txt
ollama pull llama3.2
```

Configure your API keys in `jarvis.py` and add `spotify_config.py` and `credentials.json`. Then run:

```bash
python servidor.py   # State server
python hud_qt.py     # Visual HUD
python jarvis.py     # Main assistant
```

Say **"Hey Jarvis"** to activate. For the first 10 seconds after launch, JARVIS listens without requiring the wake word.

---

## Example Commands

```
"Hey Jarvis, play Bohemian Rhapsody"
"What's the weather in Madrid?"
"Turn the volume up"
"How long does it take to drive to Barcelona?"
"Do I have any unread emails?"
"Set a 20 minute timer"
"Show me tech news"
"How's the CPU doing?"
"Take a screenshot"
"Search for the latest iPhone on Google"
"Open VS Code"
"Close Spotify"
```

---

## Project Structure

```
jarvis/
├── jarvis.py              # Main assistant script
├── servidor.py            # Flask state server for HUD
├── hud_qt.py              # PyQt6 visual interface
├── spotify_config.py      # Spotify credentials (not included)
├── credentials.json       # Google OAuth (not included)
├── token_gmail.pickle     # Gmail token (not included)
├── token_calendar.pickle  # Calendar token (not included)
├── historial.json         # Conversation memory
├── iniciar_jarvis.bat     # Windows auto-start script
└── requirements.txt       # Python dependencies
```

---

## Roadmap

- [ ] Floating compact orb widget
- [ ] Natural language Spotify control
- [ ] Daily briefing on startup
- [ ] Long-term memory with SQLite
- [ ] Android phone control via MacroDroid
- [ ] Smart home / IoT integration
- [ ] Custom wake word trained on own voice
- [ ] Migration to Ubuntu

---

## Author

**Alex** — CS Engineering student, BCN eMotorsport autonomous vehicle team.

---

## License

MIT

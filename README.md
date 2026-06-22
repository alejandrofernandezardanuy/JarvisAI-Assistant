# JARVIS

> A fully local, wake-word activated AI voice assistant with an Iron Man-style HUD.

![Python](https://img.shields.io/badge/python-3.11-blue) ![Ollama](https://img.shields.io/badge/LLM-llama3.2-green) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey) ![License](https://img.shields.io/badge/license-MIT-orange)

---

## Overview

JARVIS is a personal AI assistant that runs entirely on your machine. It listens for a wake word, understands natural language via a local LLM, responds with voice synthesis, and displays its state through a custom animated HUD — no cloud required for the core AI.

---

## Features

- **Wake word detection** — "Hey Jarvis" via openwakeword
- **Local LLM** — llama3.2 running on Ollama, fully offline
- **Natural voice** — Edge TTS with Spanish neural voice
- **Iron Man HUD** — PyQt6 particle orb that reacts to assistant state in real time
- **Spotify control** — play, pause, skip by voice
- **Gmail & Calendar** — read emails, check events, send messages by voice
- **Google Maps** — route calculation and navigation
- **Weather, news, timers, system stats** — all by voice
- **Chrome automation** — search, navigate, scroll via Selenium
- **PC macros** — volume, screenshots, window management

---

## HUD States

The central particle orb changes animation based on assistant state:

| State | Animation |
|---|---|
| Idle | Slow organic pulse with neural rays |
| Listening | Expanding ripples, high energy |
| Processing | 8 independent atomic rings |
| Speaking | Surface waves + concentric ripples |

`Alt+C` toggles between fullscreen HUD and compact top bar.

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

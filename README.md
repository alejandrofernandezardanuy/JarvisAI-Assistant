# JARVIS — Personal AI Voice Assistant

A fully local, voice-controlled personal assistant inspired by Iron Man's J.A.R.V.I.S. Built with Python, powered by Ollama and llama3.2, with a custom Iron Man-style HUD.

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Ollama](https://img.shields.io/badge/LLM-ollama%20%2B%20llama3.2-green)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## Demo

> "Hey Jarvis... pon algo de música, ¿qué tiempo hace en Barcelona?"

Jarvis escucha, procesa localmente y responde con voz mientras el HUD muestra el estado en tiempo real.

---

## Features

- **Wake word** — activación por voz con "Hey Jarvis" (openwakeword)
- **LLM local** — conversación natural con llama3.2 vía Ollama, sin APIs externas
- **Voz natural** — síntesis de voz con Edge TTS (es-ES-AlvaroNeural)
- **Spotify** — reproducir canciones, pausar, siguiente, anterior por voz
- **Gmail** — leer emails sin leer y enviar mensajes por voz
- **Google Calendar** — consultar eventos próximos y crear nuevos
- **Google Maps** — calcular rutas con tiempo y distancia, abrir en Chrome
- **Clima** — consulta en tiempo real vía OpenWeatherMap
- **Noticias** — titulares por categoría vía RSS de El País
- **Control del PC** — volumen, estado CPU/RAM/batería, macros, capturas de pantalla
- **Control de Chrome** — búsquedas, navegación, scroll por voz
- **Timers** — temporizadores por voz
- **Hora y fecha** — consulta rápida
- **Memoria persistente** — historial de conversaciones en JSON
- **HUD visual** — interfaz PyQt6 estilo Iron Man con orbe de partículas animado

---

## HUD

Interfaz visual construida con PyQt6. Dos modos:

- **Pantalla completa** — HUD Iron Man con métricas del sistema, reloj y orbe central
- **Modo compacto** — barra flotante en la parte superior, siempre visible

Toggle con `Alt+C`. El orbe cambia de animación según el estado:

| Estado | Animación |
|---|---|
| En espera | Bola orgánica pulsando lentamente con rayos desde el centro |
| Escuchando | Ondas expansivas, más agitada, rayos frecuentes |
| Procesando | 8 anillos atómicos independientes girando en ejes distintos |
| Hablando | Ondas viajando por la superficie + ripples concéntricos |

---

## Stack

| Componente | Tecnología |
|---|---|
| LLM | Ollama + llama3.2 |
| Wake word | openwakeword (hey_jarvis, ONNX) |
| Speech-to-text | SpeechRecognition + Google Speech API |
| Text-to-speech | Edge TTS (es-ES-AlvaroNeural) |
| Audio | sounddevice |
| HUD | PyQt6 |
| Servidor estado | Flask + Flask-SocketIO |
| Spotify | spotipy |
| Gmail / Calendar | Google API Python Client |
| Maps | googlemaps |
| Clima | OpenWeatherMap API |
| Chrome | Selenium + ChromeDriver |
| Volumen | pycaw (Windows) |
| Macros | pyautogui |

---

## Requisitos

- Python 3.11
- [Ollama](https://ollama.com) instalado con `llama3.2`
- Google Chrome instalado
- Cuenta de Spotify (para control de música)
- Credenciales OAuth de Google (Gmail + Calendar)
- API keys: OpenWeatherMap, Google Maps

---

## Instalación

```bash
git clone https://github.com/tu-usuario/jarvis.git
cd jarvis
python -m venv venv311
venv311\Scripts\activate        # Windows
pip install -r requirements.txt
ollama pull llama3.2
```

### Credenciales necesarias

Crea un archivo `spotify_config.py`:
```python
SPOTIFY_CLIENT_ID     = "tu_client_id"
SPOTIFY_CLIENT_SECRET = "tu_client_secret"
SPOTIFY_REDIRECT_URI  = "http://localhost:8888/callback"
```

Coloca tu `credentials.json` de Google en la raíz del proyecto.

Rellena las API keys en `jarvis.py`:
```python
OPENWEATHER_API_KEY = "tu_key"
GOOGLEMAPS_API_KEY  = "tu_key"
```

---

## Uso

Arranca en tres terminales:

```bash
# Terminal 1 — Servidor de estado
python servidor.py

# Terminal 2 — HUD visual
python hud_qt.py

# Terminal 3 — Jarvis
python jarvis.py
```

O usa `iniciar_jarvis.bat` para arrancar todo automáticamente.

Di **"Hey Jarvis"** para activar. Durante los primeros 10 segundos al arrancar escucha directamente sin wake word.

---

## Comandos de ejemplo

```
"Hey Jarvis, pon Bohemian Rhapsody"
"¿Qué tiempo hace en Madrid?"
"Sube el volumen"
"¿Cuánto tarda en coche a Barcelona?"
"¿Qué emails tengo sin leer?"
"Pon un timer de 20 minutos"
"Busca noticias de tecnología"
"¿Cómo está la CPU?"
"Captura de pantalla"
"Abre VS Code"
```

---

## Estructura del proyecto

```
jarvis/
├── jarvis.py              # Script principal
├── servidor.py            # Servidor Flask para el HUD
├── hud_qt.py              # Interfaz visual PyQt6
├── spotify_config.py      # Credenciales Spotify (no incluido)
├── credentials.json       # OAuth Google (no incluido)
├── token_gmail.pickle     # Token Gmail (no incluido)
├── token_calendar.pickle  # Token Calendar (no incluido)
├── historial.json         # Memoria de conversaciones
├── iniciar_jarvis.bat     # Arranque automático Windows
└── requirements.txt       # Dependencias Python
```

---

## Roadmap

- [ ] Modo minimizado con orbe flotante en esquina
- [ ] Spotify mejorado — playlists, géneros, lenguaje natural
- [ ] Modos de uso — estudio, trabajo, película
- [ ] Resumen diario al arrancar
- [ ] Memoria larga con SQLite
- [ ] Control del móvil Android vía MacroDroid
- [ ] IoT — dispositivos inteligentes
- [ ] Wake word personalizado con voz propia
- [ ] Migración a Ubuntu

---

## Autor

**Alex** — Estudiante de Ingeniería Informática, BCN eMotorsport (vehículo autónomo), apasionado de la robótica y la IA.

---

## Licencia

MIT

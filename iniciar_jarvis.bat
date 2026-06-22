@echo off
start "" "C:\Users\alfea\AppData\Local\Programs\Ollama\ollama app.exe"
timeout /t 5
cd C:\Jarvis
call venv311\Scripts\activate
start python servidor.py
timeout /t 2
start python hud_qt.py
timeout /t 2
python jarvis.py
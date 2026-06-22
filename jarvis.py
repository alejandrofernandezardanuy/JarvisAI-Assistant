import ollama
import asyncio
import edge_tts
import os
import uuid
import tempfile
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import wave
import subprocess
import webbrowser
import threading
import queue
import time
import spotipy
import unicodedata
import json
import re
import requests
from datetime import datetime
from openwakeword.model import Model
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from spotipy.oauth2 import SpotifyOAuth
from spotify_config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

driver = None
oww_model = None
OPENWEATHER_API_KEY = "key"
GOOGLEMAPS_API_KEY = "key"
CIUDAD_DEFAULT = "Barcelona"
NEWSAPI_KEY = "key"
ARCHIVO_HISTORIAL = "historial.json"

CONTACTOS = {
    "mi mismo": "alrin@gmail.com",
    "mama": "cmeuy@gmail.com",
    "gabri": "gc55@gmail.com",
}

def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_historial():
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial[-2:], f, ensure_ascii=False, indent=2)

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def iniciar_chrome():
    global driver
    try:
        if driver is not None:
            driver.title
    except:
        driver = None
    if driver is None:
        opciones = webdriver.ChromeOptions()
        opciones.add_argument("--start-maximized")
        opciones.add_argument("--disable-blink-features=AutomationControlled")
        opciones.add_argument("--no-first-run")
        opciones.add_argument("--no-default-browser-check")
        opciones.add_argument("--disable-session-crashed-bubble")
        opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
        opciones.add_experimental_option("useAutomationExtension", False)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def controlar_chrome(mensaje):
    global driver
    mensaje = normalizar(mensaje)

    if "cierra chrome" in mensaje or "cierra el navegador" in mensaje:
        if driver:
            driver.quit()
            driver = None
        return "Chrome cerrado."
    elif "nueva pestana" in mensaje:
        iniciar_chrome()
        driver.execute_script("window.open('');")
        return "Nueva pestaña abierta."
    elif "cierra pestana" in mensaje:
        if driver:
            driver.close()
        return "Pestaña cerrada."
    elif "vuelve atras" in mensaje or "vuelve para atras" in mensaje:
        if driver:
            driver.back()
        return "Volviendo atrás."
    elif "baja" in mensaje:
        if driver:
            driver.execute_script("window.scrollBy(0, 700);")
        return "Bajando."
    elif "sube" in mensaje:
        if driver:
            driver.execute_script("window.scrollBy(0, -700);")
        return "Subiendo."
    elif "pagina" in mensaje and any(str(n) in mensaje for n in range(2, 11)):
        numero = next(n for n in range(2, 11) if str(n) in mensaje)
        iniciar_chrome()
        driver.get(f"https://www.google.com/search?q={driver.title}&start={(numero-1)*10}")
        return f"Yendo a la página {numero}."
    elif "busca" in mensaje or "googlea" in mensaje:
        busqueda = mensaje.replace("busca en google", "").replace("busca", "").replace("googlea", "").strip()
        iniciar_chrome()
        driver.get(f"https://www.google.com/search?q={busqueda.replace(' ', '+')}")
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "search")))
        except:
            pass
        return f"Buscando {busqueda}."
    elif "ve a" in mensaje or "abre la web" in mensaje:
        url = mensaje.replace("ve a", "").replace("abre la web", "").strip()
        if not url.startswith("http"):
            url = "https://" + url
        iniciar_chrome()
        driver.get(url)
        return f"Abriendo {url}."

    return None

SISTEMA = "Eres Jarvis, asistente personal de Alex, ingeniero profesional. Eres resolutivo, directo y eficiente. Sin saludos innecesarios, sin preguntar qué tal, sin relleno. Respondes exactamente lo que se te pregunta con la mínima cantidad de palabras necesarias. Si te piden hacer algo, lo haces y confirmas en una frase. Tu dueño es Alex."

VOZ_EDGE = "es-ES-AlvaroNeural"
historial = cargar_historial()

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-modify-playback-state user-read-playback-state"
))

APPS = {
    "spotify": "start spotify:",
    "discord": "start discord:",
    "chrome": "start chrome",
}

WEBS = {
    "netflix": "https://www.netflix.com",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
}

def activar_dispositivo():
    subprocess.Popen("start spotify:", shell=True)
    time.sleep(5)
    dispositivos = sp.devices()
    if dispositivos["devices"]:
        device_id = dispositivos["devices"][0]["id"]
        sp.transfer_playback(device_id, force_play=True)
        return device_id
    return None

def controlar_spotify(mensaje):
    mensaje = normalizar(mensaje)
    try:
        if "pausa" in mensaje or "para la musica" in mensaje:
            sp.pause_playback()
            return "Musica pausada."
        elif "continua" in mensaje or "pon la musica" in mensaje:
            device_id = activar_dispositivo()
            sp.start_playback(device_id=device_id)
            return "Reproduciendo."
        elif "siguiente" in mensaje or "salta" in mensaje:
            sp.next_track()
            return "Siguiente cancion."
        elif "anterior" in mensaje:
            sp.previous_track()
            return "Cancion anterior."
        elif ("pon" in mensaje or "reproduce" in mensaje) and "volumen" not in mensaje:
            busqueda = mensaje.replace("pon", "").replace("reproduce", "").strip()
            resultados = sp.search(q=busqueda, limit=1, type="track")
            if resultados["tracks"]["items"]:
                uri = resultados["tracks"]["items"][0]["uri"]
                device_id = activar_dispositivo()
                sp.start_playback(device_id=device_id, uris=[uri])
                nombre = resultados["tracks"]["items"][0]["name"]
                return f"Poniendo {nombre}."
    except Exception as e:
        return f"Error con Spotify: {str(e)}"
    return None

def abrir_app(nombre):
    nombre = normalizar(nombre)
    for clave, cmd in APPS.items():
        if clave in nombre:
            subprocess.Popen(cmd, shell=True)
            return f"Abriendo {clave}."
    for clave, url in WEBS.items():
        if clave in nombre:
            webbrowser.open(url)
            return f"Abriendo {clave}."
    return None

def cerrar_app(nombre):
    nombre = normalizar(nombre)
    if "cierra" not in nombre and "cerrar" not in nombre:
        return None
    PROCESOS = {
        "spotify": "Spotify.exe",
        "discord": "Discord.exe",
        "chrome": "chrome.exe",
    }
    for clave, proceso in PROCESOS.items():
        if clave in nombre:
            subprocess.Popen(f"taskkill /f /im {proceso}", shell=True)
            return f"{clave} cerrado."
    return None

async def texto_a_voz(texto, archivo):
    comunicar = edge_tts.Communicate(texto, VOZ_EDGE)
    await comunicar.save(archivo)

def actualizar_hud(estado):
    try:
        requests.post("http://127.0.0.1:5000/estado",
                      json={"estado": estado}, timeout=0.3)
    except:
        pass

def hablar(texto):
    actualizar_hud("hablando")
    archivo = os.path.join(tempfile.gettempdir(), f"jarvis_{uuid.uuid4().hex}.mp3")
    asyncio.run(texto_a_voz(texto, archivo))
    from playsound import playsound
    playsound(archivo)
    try:
        os.remove(archivo)
    except:
        pass
    actualizar_hud("en_espera")

def escuchar_dinamico(timeout_silencio=10, umbral=600):
    RATE = 16000
    CHUNK = 1280
    UMBRAL = umbral

    print("Escuchando...")
    actualizar_hud("escuchando")

    buf = queue.Queue()

    def callback(indata, frames, time_info, status):
        buf.put(indata.copy())

    frames_voz = []
    ultimo_sonido = time.time()
    hablando = False

    with sd.InputStream(samplerate=RATE, channels=1, dtype='int16',
                        blocksize=CHUNK, callback=callback):
        while True:
            chunk = buf.get().flatten()
            nivel = np.abs(chunk).mean()

            if nivel > UMBRAL:
                ultimo_sonido = time.time()
                hablando = True
                frames_voz.append(chunk)
            else:
                if hablando:
                    frames_voz.append(chunk)
                    if time.time() - ultimo_sonido > 1.2:
                        break
                else:
                    if time.time() - ultimo_sonido > timeout_silencio:
                        actualizar_hud("en_espera")
                        return None

    actualizar_hud("procesando")

    if not frames_voz:
        actualizar_hud("en_espera")
        return None

    audio_data = np.concatenate(frames_voz).astype(np.int16)
    archivo_wav = os.path.join(tempfile.gettempdir(), "jarvis_input.wav")
    with wave.open(archivo_wav, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(audio_data.tobytes())

    r = sr.Recognizer()
    with sr.AudioFile(archivo_wav) as source:
        audio = r.record(source)
        try:
            texto = r.recognize_google(audio, language="es-ES")
            print(f"Tu: {texto}")
            return texto
        except sr.UnknownValueError:
            print("No te he entendido.")
            actualizar_hud("en_espera")
            return ""
        except sr.RequestError:
            print("Error de conexion.")
            actualizar_hud("en_espera")
            return ""

def cargar_wake_word():
    global oww_model
    print("Cargando wake word...")
    oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    print("Wake word listo.")

def esperar_wake_word():
    RATE = 16000
    CHUNK = 1280

    print("Esperando 'Hey Jarvis'...")

    buf = queue.Queue()

    def callback(indata, frames, time_info, status):
        buf.put(indata.copy())

    with sd.InputStream(samplerate=RATE, channels=1, dtype='int16',
                        blocksize=CHUNK, callback=callback):
        while True:
            audio_chunk = buf.get().flatten()
            prediction = oww_model.predict(audio_chunk)
            for mdl, score in prediction.items():
                if score > 0.3:
                    print(f"Wake word detectado! Score: {score:.2f}")
                    return

def estado_sistema(mensaje):
    mensaje = normalizar(mensaje)
    if not any(p in mensaje for p in ["cpu", "ram", "memoria", "bateria", "como esta el pc", "como va el pc"]):
        return None

    import psutil
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_usada = round(ram.used / (1024**3), 1)
    ram_total = round(ram.total / (1024**3), 1)
    ram_pct = ram.percent

    bateria = psutil.sensors_battery()
    if bateria:
        bat_pct = round(bateria.percent)
        cargando = "cargando" if bateria.power_plugged else "sin cargar"
        bat_txt = f"Batería al {bat_pct}% {cargando}."
    else:
        bat_txt = "Sin batería detectada."

    return f"CPU al {cpu}%. RAM {ram_usada}GB de {ram_total}GB usada ({ram_pct}%). {bat_txt}"

def controlar_volumen(mensaje):
    mensaje = normalizar(mensaje)
    if not any(p in mensaje for p in ["sube el volumen", "baja el volumen", "silencio", "mutea", "desmutea", "ya puedes hablar", "volumen del sistema"]):
        return None

    from pycaw.pycaw import AudioUtilities
    device = AudioUtilities.GetSpeakers()
    volume = device.EndpointVolume

    if "silencio" in mensaje or "mutea" in mensaje:
        volume.SetMute(1, None)
        return "Silenciado."

    if "desmutea" in mensaje or "ya puedes hablar" in mensaje:
        volume.SetMute(0, None)
        return "Sonido activado."

    if "sube el volumen" in mensaje:
        actual = volume.GetMasterVolumeLevelScalar()
        nuevo = min(1.0, actual + 0.1)
        volume.SetMasterVolumeLevelScalar(nuevo, None)
        return f"Volumen al {round(nuevo*100)}%."

    if "baja el volumen" in mensaje:
        actual = volume.GetMasterVolumeLevelScalar()
        nuevo = max(0.0, actual - 0.1)
        volume.SetMasterVolumeLevelScalar(nuevo, None)
        return f"Volumen al {round(nuevo*100)}%."

    if "volumen del sistema al" in mensaje:
        numeros = [int(s) for s in mensaje.split() if s.isdigit()]
        if numeros:
            nivel = numeros[0]
            volume.SetMasterVolumeLevelScalar(nivel / 100, None)
            return f"Volumen al {nivel}%."

    return None

def consultar_clima(mensaje):
    mensaje = normalizar(mensaje)
    if not any(p in mensaje for p in ["tiempo", "clima", "temperatura", "llueve", "lluvia", "calor", "frio"]):
        return None

    ciudad = CIUDAD_DEFAULT
    for prep in ["en", "de"]:
        if prep in mensaje:
            partes = mensaje.split(prep)
            if len(partes) > 1 and partes[-1].strip():
                ciudad = partes[-1].strip()
                break

    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={OPENWEATHER_API_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url)
        data = r.json()
        if data["cod"] != 200:
            return f"No he encontrado el clima de {ciudad}."
        temp = round(data["main"]["temp"])
        sensacion = round(data["main"]["feels_like"])
        descripcion = data["weather"][0]["description"]
        humedad = data["main"]["humidity"]
        return f"En {ciudad}: {temp}°C, sensación de {sensacion}°C, {descripcion}, humedad {humedad}%."
    except:
        return "Error al consultar el clima."

def consultar_noticias(mensaje):
    mensaje = normalizar(mensaje)
    if not any(p in mensaje for p in ["noticias", "que pasa", "actualidad", "novedades"]):
        return None

    import xml.etree.ElementTree as ET

    CATEGORIAS = {
        "tecnologia": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/tecnologia/portada",
        "deporte": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/deportes/portada",
        "economia": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/economia/portada",
        "internacional": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada",
    }

    url = "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"
    for cat, cat_url in CATEGORIAS.items():
        if cat in mensaje:
            url = cat_url
            break

    try:
        r = requests.get(url, timeout=5)
        root = ET.fromstring(r.content)
        items = root.findall(".//item")[:3]
        noticias = []
        for i, item in enumerate(items, 1):
            titulo = item.find("title").text
            noticias.append(f"{i}. {titulo}")
        return "Principales noticias: " + ". ".join(noticias)
    except:
        return "Error al consultar las noticias."

def consultar_hora(mensaje):
    mensaje = normalizar(mensaje)
    if not any(p in mensaje for p in ["hora", "dia", "fecha", "hoy"]):
        return None

    ahora = datetime.now()
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    dia_semana = dias[ahora.weekday()]
    dia = ahora.day
    mes = meses[ahora.month - 1]
    anyo = ahora.year
    hora = ahora.strftime("%H:%M")

    if "hora" in mensaje:
        return f"Son las {hora}."
    elif any(p in mensaje for p in ["dia", "fecha", "hoy"]):
        return f"Hoy es {dia_semana} {dia} de {mes} de {anyo}."

    return None

def gestionar_timer(mensaje):
    mensaje = normalizar(mensaje)
    if not any(p in mensaje for p in ["timer", "temporizador", "minutos", "segundos"]):
        return None

    minutos = 0
    segundos = 0

    m = re.search(r'(\d+)\s*minuto', mensaje)
    s = re.search(r'(\d+)\s*segundo', mensaje)

    if m:
        minutos = int(m.group(1))
    if s:
        segundos = int(s.group(1))

    total = minutos * 60 + segundos
    if total == 0:
        return None

    def lanzar_timer():
        time.sleep(total)
        aviso = f"Timer de {minutos} minutos completado." if minutos > 0 else f"Timer de {segundos} segundos completado."
        print(f"\nJarvis: {aviso}")
        hablar(aviso)

    hilo = threading.Thread(target=lanzar_timer, daemon=True)
    hilo.start()

    if minutos > 0 and segundos > 0:
        return f"Timer de {minutos} minutos y {segundos} segundos iniciado."
    elif minutos > 0:
        return f"Timer de {minutos} minutos iniciado."
    else:
        return f"Timer de {segundos} segundos iniciado."



def ejecutar_macro(mensaje):
    mensaje = normalizar(mensaje)
    if not any(p in mensaje for p in ["abre el explorador", "captura", "cierra la ventana", "minimiza", "copia", "pega", "maximiza", "escritorio"]):
        return None

    import pyautogui
    import pygetwindow

    if "abre el explorador" in mensaje:
        pyautogui.hotkey("win", "e")
        return "Abriendo explorador."

    if "captura" in mensaje:
        archivo = os.path.join(os.path.expanduser("~"), "Desktop", f"captura_{uuid.uuid4().hex[:6]}.png")
        pyautogui.screenshot(archivo)
        return f"Captura guardada en el escritorio."

    if "cierra la ventana" in mensaje:
        pyautogui.hotkey("alt", "f4")
        return "Ventana cerrada."

    if "minimiza todo" in mensaje or "escritorio" in mensaje:
        pyautogui.hotkey("win", "d")
        return "Escritorio."

    if "minimiza" in mensaje:
        pyautogui.hotkey("win", "down")
        return "Ventana minimizada."

    if "maximiza" in mensaje:
        pyautogui.hotkey("win", "up")
        return "Ventana maximizada."

    if "copia" in mensaje:
        pyautogui.hotkey("ctrl", "c")
        return "Copiado."

    if "pega" in mensaje:
        pyautogui.hotkey("ctrl", "v")
        return "Pegado."

    return None

def gestionar_gmail(mensaje):
    mensaje_norm = normalizar(mensaje)
    if not any(p in mensaje_norm for p in ["email", "correo", "emails", "correos", "manda un email", "manda un correo"]):
        return None

    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from email.mime.text import MIMEText
    import base64
    import pickle

    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send'
    ]
    creds = None

    if os.path.exists('token_gmail.pickle'):
        with open('token_gmail.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_gmail.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # ENVIAR EMAIL
    if "manda un email a" in mensaje_norm or "manda un correo a" in mensaje_norm:
        for nombre, email in CONTACTOS.items():
            if nombre in mensaje_norm:
                # Extraer el mensaje después de "diciendo"
                if "diciendo" in mensaje_norm:
                    cuerpo = mensaje_norm.split("diciendo")[-1].strip()
                elif "que diga" in mensaje_norm:
                    cuerpo = mensaje_norm.split("que diga")[-1].strip()
                else:
                    return "No he entendido el mensaje a enviar."

                mime = MIMEText(cuerpo)
                mime['to'] = email
                mime['subject'] = "Mensaje de Jarvis"
                raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
                service.users().messages().send(userId='me', body={'raw': raw}).execute()
                return f"Email enviado a {nombre}."
        return "No he encontrado ese contacto."

    # LEER EMAILS
    if any(p in mensaje_norm for p in ["emails", "correos", "tengo emails", "tengo correos"]):
        results = service.users().messages().list(userId='me', maxResults=3, labelIds=['INBOX', 'UNREAD']).execute()
        messages = results.get('messages', [])
        if not messages:
            return "No tienes emails sin leer."
        textos = []
        for msg in messages:
            m = service.users().messages().get(userId='me', id=msg['id'], format='metadata',
                metadataHeaders=['From', 'Subject']).execute()
            headers = {h['name']: h['value'] for h in m['payload']['headers']}
            remitente = headers.get('From', 'Desconocido').split('<')[0].strip()
            asunto = headers.get('Subject', 'Sin asunto')
            textos.append(f"{remitente}: {asunto}")
        return f"Tienes {len(messages)} emails sin leer. " + ". ".join(textos)

    return None

def gestionar_calendar(mensaje):
    mensaje_norm = normalizar(mensaje)
    if not any(p in mensaje_norm for p in ["calendario", "eventos", "agenda", "que tengo", "crea un evento"]):
        return None

    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    import datetime

    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None

    if os.path.exists('token_calendar.pickle'):
        with open('token_calendar.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_calendar.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # LEER EVENTOS
    if any(p in mensaje_norm for p in ["que tengo", "eventos", "agenda"]):
        ahora = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=ahora,
            maxResults=3, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])
        if not events:
            return "No tienes eventos próximos."
        textos = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_dt = datetime.datetime.fromisoformat(start.replace('Z', ''))
            hora = start_dt.strftime("%d/%m a las %H:%M")
            textos.append(f"{event['summary']} el {hora}")
        return "Próximos eventos: " + ". ".join(textos)

    # CREAR EVENTO
    if "crea un evento" in mensaje_norm:
        partes = mensaje_norm.split("crea un evento")[-1].strip()
        nombre = partes.split(" el ")[0].strip() if " el " in partes else partes
        event = {
            'summary': nombre,
            'start': {'dateTime': (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat(), 'timeZone': 'Europe/Madrid'},
            'end': {'dateTime': (datetime.datetime.now() + datetime.timedelta(hours=2)).isoformat(), 'timeZone': 'Europe/Madrid'},
        }
        service.events().insert(calendarId='primary', body=event).execute()
        return f"Evento {nombre} creado."

    return None


def minimizar_hud():
    try:
        requests.post("http://127.0.0.1:5000/minimizar", timeout=0.3)
    except:
        pass

def consultar_maps(mensaje):
    mensaje_norm = normalizar(mensaje)
    if not any(p in mensaje_norm for p in ["como llego", "como ir", "ruta", "cuanto tarda", "distancia"]):
        return None

    import googlemaps
    gmaps = googlemaps.Client(key=GOOGLEMAPS_API_KEY)

    destino = None
    for prep in ["a ", "hasta ", "hacia "]:
        if prep in mensaje_norm:
            destino = mensaje_norm.split(prep)[-1].strip()
            break

    if not destino:
        return "No he entendido el destino."

    try:
        directions = gmaps.directions(
            origin=CIUDAD_DEFAULT,
            destination=destino,
            mode="driving",
            language="es"
        )
        if not directions:
            return f"No he encontrado ruta a {destino}."

        leg = directions[0]['legs'][0]
        distancia = leg['distance']['text']
        duracion = leg['duration']['text']

        respuesta = f"De {CIUDAD_DEFAULT} a {destino}: {distancia}, unos {duracion} en coche. ¿Quieres que abra la ruta en Maps?"
        print(f"Jarvis: {respuesta}")
        hablar(respuesta)

        time.sleep(1)
        confirmacion = escuchar_dinamico(timeout_silencio=8, umbral=400)
        if confirmacion and any(p in normalizar(confirmacion) for p in ["si", "vale", "abre", "yes", "claro", "venga", "ok", "afirmativo", "por favor"]):
            url = f"https://www.google.com/maps/dir/{CIUDAD_DEFAULT}/{destino.replace(' ', '+')}"
            iniciar_chrome()
            driver.get(url)
            return "Abriendo ruta en Maps."
        else:
            return "De acuerdo."

    except Exception as e:
        return f"Error consultando Maps: {str(e)}"

def procesar_entrada(entrada):
    if entrada.lower() == "salir":
        despedida = "Hasta luego."
        print(f"Jarvis: {despedida}")
        hablar(despedida)
        return True

    vol = controlar_volumen(entrada)
    if vol:
        print(f"Jarvis: {vol}")
        hablar(vol)
        return False

    timer = gestionar_timer(entrada)
    if timer:
        print(f"Jarvis: {timer}")
        hablar(timer)
        return False

    macro = ejecutar_macro(entrada)
    if macro:
        print(f"Jarvis: {macro}")
        hablar(macro)
        return False

    sistema = estado_sistema(entrada)
    if sistema:
        print(f"Jarvis: {sistema}")
        hablar(sistema)
        return False

    clima = consultar_clima(entrada)
    if clima:
        print(f"Jarvis: {clima}")
        hablar(clima)
        return False

    maps = consultar_maps(entrada)
    if maps:
        print(f"Jarvis: {maps}")
        hablar(maps)
        return False

    noticias = consultar_noticias(entrada)
    if noticias:
        print(f"Jarvis: {noticias}")
        hablar(noticias)
        return False

    gmail = gestionar_gmail(entrada)
    if gmail:
        print(f"Jarvis: {gmail}")
        hablar(gmail)
        return False

    calendar = gestionar_calendar(entrada)
    if calendar:
        print(f"Jarvis: {calendar}")
        hablar(calendar)
        return False

    hora = consultar_hora(entrada)
    if hora:
        print(f"Jarvis: {hora}")
        hablar(hora)
        return False

    spotify = controlar_spotify(entrada)
    if spotify:
        minimizar_hud()
        print(f"Jarvis: {spotify}")
        hablar(spotify)
        return False

    cerrar = cerrar_app(entrada)
    if cerrar:
        minimizar_hud()
        print(f"Jarvis: {cerrar}")
        hablar(cerrar)
        return False

    resultado = abrir_app(entrada)
    if resultado:
        minimizar_hud()
        print(f"Jarvis: {resultado}")
        hablar(resultado)
        return False

    chrome = controlar_chrome(entrada)
    if chrome:
        minimizar_hud()
        print(f"Jarvis: {chrome}")
        hablar(chrome)
        return False

def chatear(mensaje):
    historial.append({"role": "user", "content": mensaje})
    respuesta_completa = ""
    frase_actual = ""
    cola = queue.Queue()

    def worker_voz():
        while True:
            texto = cola.get()
            if texto is None:
                break
            hablar(texto)
            cola.task_done()

    hilo = threading.Thread(target=worker_voz, daemon=True)
    hilo.start()

    actualizar_hud("procesando")

    stream = ollama.chat(
        model="llama3.2",
        messages=[{"role": "system", "content": SISTEMA}] + historial,
        stream=True
    )

    print("Jarvis: ", end="", flush=True)

    for chunk in stream:
        trozo = chunk["message"]["content"]
        print(trozo, end="", flush=True)
        frase_actual += trozo
        respuesta_completa += trozo

        if any(frase_actual.endswith(p) for p in [".", "!", "?", "...", "\n"]):
            if frase_actual.strip():
                cola.put(frase_actual.strip())
            frase_actual = ""

    if frase_actual.strip():
        cola.put(frase_actual.strip())

    cola.put(None)
    hilo.join()

    print()
    historial.append({"role": "assistant", "content": respuesta_completa})
    guardar_historial()
    return respuesta_completa

# ── ARRANQUE ──────────────────────────────────────────────
print("Jarvis iniciado.")
cargar_wake_word()
chatear("Di solo: Listo.")
print()

primer_arranque = True

while True:
    if primer_arranque:
        print("[Escuchando 10s sin wake word...]")
        entrada = escuchar_dinamico(timeout_silencio=10)
        primer_arranque = False
    else:
        esperar_wake_word()
        entrada = escuchar_dinamico(timeout_silencio=10)

    if entrada is None or entrada == "":
        continue

    salir = procesar_entrada(entrada)
    if salir:
        break

    while True:
        print("[Conversacion activa, 10s...]")
        entrada = escuchar_dinamico(timeout_silencio=10)
        if entrada is None or entrada == "":
            print("Sin actividad, volviendo a wake word.")
            break
        salir = procesar_entrada(entrada)
        if salir:
            exit()
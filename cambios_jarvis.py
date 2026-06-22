# ── AÑADIR ESTA FUNCIÓN en jarvis.py (junto al resto de funciones) ──────────

def actualizar_hud(estado):
    try:
        requests.post("http://127.0.0.1:5000/estado",
                      json={"estado": estado}, timeout=0.3)
    except:
        pass


# ── REEMPLAZA la función hablar() existente con esta versión ─────────────────

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


# ── REEMPLAZA la función escuchar_dinamico() con esta versión ────────────────

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


# ── REEMPLAZA la función chatear() con esta versión ──────────────────────────

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
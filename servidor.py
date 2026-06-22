from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import psutil
import threading
import time

estado_actual = {"estado": "en_espera"}
sistema_actual = {"cpu": 0, "ram_pct": 0, "ram_usada": 0.0, "ram_total": 0.0}

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return render_template("hud.html")

@app.route("/estado", methods=["POST"])
def actualizar_estado():
    global estado_actual
    data = request.get_json()
    estado_actual = data
    socketio.emit("estado", data)
    return jsonify({"ok": True})


minimizar_flag = False

@app.route("/minimizar", methods=["POST"])
def minimizar():
    global minimizar_flag
    minimizar_flag = True
    return jsonify({"ok": True})

@app.route("/minimizar_hud", methods=["GET"])
def get_minimizar():
    global minimizar_flag
    val = minimizar_flag
    minimizar_flag = False
    return jsonify({"minimizar": val})

def enviar_sistema():
    global sistema_actual
    while True:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        sistema_actual = {
            "cpu": round(cpu),
            "ram_pct": round(ram.percent),
            "ram_usada": round(ram.used / (1024**3), 1),
            "ram_total": round(ram.total / (1024**3), 1)
        }
        socketio.emit("sistema", sistema_actual)
        time.sleep(2)

@app.route("/estado_actual", methods=["GET"])
def get_estado():
    return jsonify(estado_actual)

@app.route("/sistema_actual", methods=["GET"])
def get_sistema():
    return jsonify(sistema_actual)


if __name__ == "__main__":
    socketio.start_background_task(enviar_sistema)
    socketio.run(app, host="127.0.0.1", port=5000)
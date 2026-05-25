from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import json
import os
import socket
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

BASE = r"C:\Users\salma\OneDrive - Educantabria\SalimaAI\proyecto"
HISTORIAL_FILE = BASE + r"\historial.json"
PROGRESO_FILE = BASE + r"\progreso.json"
PUNTOS_FILE = BASE + r"\puntos.json"

cliente_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODELO_GROQ = "llama-3.3-70b-versatile"
MODELO_LOCAL = "llama3.2:3b"

EJERCICIOS = [
    {"pregunta": "Completa: Ayer ___ (ir/yo) al trabajo.", "respuesta": "fui", "explicacion": "'Fui' es el preterito indefinido de IR. Ayer + indefinido siempre."},
    {"pregunta": "Completa: Ella ___ (ser) profesora desde hace 10 anos.", "respuesta": "es", "explicacion": "Usamos SER para profesiones permanentes."},
    {"pregunta": "Completa: ___ (tener/yo) mucho sueno hoy.", "respuesta": "tengo", "explicacion": "TENER se conjuga: yo tengo, tu tienes, el tiene."},
    {"pregunta": "Elige: Estoy ___ (mucho/muy) cansada.", "respuesta": "muy", "explicacion": "MUY + adjetivo. MUCHO + sustantivo. 'Muy cansada' es correcto."},
    {"pregunta": "Completa: Si ___ (tener/yo) tiempo, estudiaria mas.", "respuesta": "tuviera", "explicacion": "Si + imperfecto subjuntivo + condicional. Tener -> tuviera."},
    {"pregunta": "Corrige: Yo soy muy bien hoy.", "respuesta": "Estoy muy bien hoy", "explicacion": "Los estados temporales usan ESTAR. El bienestar es temporal -> estoy."},
    {"pregunta": "Completa: Hace tres anos que ___ (vivir/yo) en Espana.", "respuesta": "vivo", "explicacion": "Hace + tiempo + que + presente. Accion que empeza en pasado y continua."},
    {"pregunta": "Elige: ___ (Por/Para) favor, habla mas despacio.", "respuesta": "Por", "explicacion": "Por favor es una expresion fija. Para favor no existe."},
    {"pregunta": "Completa: Cuando era pequena, ___ (jugar/yo) en la calle.", "respuesta": "jugaba", "explicacion": "Imperfecto para habitos del pasado. Jugaba = I used to play."},
    {"pregunta": "Corrige: Me gustan mucho la Espana.", "respuesta": "Me gusta mucho Espana", "explicacion": "Espana no lleva articulo. Y 'gustar' con sustantivo singular -> gusta."},
    {"pregunta": "Completa: No entiendo nada, necesito que me lo ___ (explicar/tu).", "respuesta": "expliques", "explicacion": "Necesitar que + subjuntivo. Tu -> expliques en subjuntivo."},
    {"pregunta": "Elige: Llevo tres anos ___ (vivir/viviendo) aqui.", "respuesta": "viviendo", "explicacion": "Llevar + gerundio (-ando/-iendo) para acciones en progreso."},
    {"pregunta": "Corrige: Ayer he ido al supermercado.", "respuesta": "Ayer fui al supermercado", "explicacion": "Con 'ayer' siempre indefinido (fui), nunca perfecto (he ido)."},
    {"pregunta": "Completa: Es importante que ___ (estudiar/tu) cada dia.", "respuesta": "estudies", "explicacion": "Es importante que + subjuntivo. Tu estudiar -> estudies."},
    {"pregunta": "Cual es correcto: Soy cansada o Estoy cansada?", "respuesta": "Estoy cansada", "explicacion": "El cansancio es temporal -> ESTAR. SER es para caracteristicas permanentes."}
]

def hay_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except:
        return False

def cargar_json(path, default):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def guardar_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def obtener_respuesta(conversacion):
    # Comprueba internet en cada mensaje
    if hay_internet():
        print("-> Usando Groq (internet disponible)")
        respuesta = cliente_groq.chat.completions.create(
            model=MODELO_GROQ,
            messages=conversacion,
            max_tokens=300,
            temperature=0.7
        )
        return respuesta.choices[0].message.content
    else:
        print("-> Usando Ollama (sin internet)")
        r = requests.post(
            'http://localhost:11434/api/chat',
            json={"model": MODELO_LOCAL, "messages": conversacion, "stream": False},
            timeout=120
        )
        return r.json()["message"]["content"]

@app.route('/')
def index():
    return open(BASE + r"\salimabot.html", encoding='utf-8').read()

@app.route('/estado', methods=['GET'])
def estado():
    internet = hay_internet()
    return jsonify({
        "internet": internet,
        "modo": "Groq (rapido)" if internet else "Ollama (local)"
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    historial = cargar_json(HISTORIAL_FILE, [])
    progreso = cargar_json(PROGRESO_FILE, {"dias_racha": 0, "ultimo_dia": "", "mensajes_total": 0})

    hoy = datetime.now().strftime("%Y-%m-%d")
    if progreso["ultimo_dia"] != hoy:
        progreso["dias_racha"] += 1
        progreso["ultimo_dia"] = hoy
    progreso["mensajes_total"] += 1
    guardar_json(PROGRESO_FILE, progreso)

    mensajes = data.get("messages", [])
    system_msg = mensajes[0] if mensajes else {"role": "system", "content": "Eres SalimaBot"}
    user_msgs = mensajes[1:] if len(mensajes) > 1 else []
    memoria = historial[-10:]
    conversacion = [system_msg] + memoria + user_msgs

    try:
        texto = obtener_respuesta(conversacion)
        if user_msgs:
            historial.append(user_msgs[-1])
        historial.append({"role": "assistant", "content": texto})
        guardar_json(HISTORIAL_FILE, historial[-50:])
        return jsonify({
            "message": {"role": "assistant", "content": texto},
            "progreso": progreso
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ejercicio', methods=['GET'])
def get_ejercicio():
    import random
    puntos = cargar_json(PUNTOS_FILE, {"total": 0, "correctas": 0, "incorrectas": 0, "racha": 0})
    ej = random.choice(EJERCICIOS)
    return jsonify({**ej, "puntos": puntos})

@app.route('/verificar', methods=['POST'])
def verificar():
    data = request.json
    respuesta_usuario = data.get("respuesta", "").strip().lower()
    respuesta_correcta = data.get("respuesta_correcta", "").strip().lower()
    explicacion = data.get("explicacion", "")
    correcto = respuesta_usuario == respuesta_correcta or respuesta_correcta in respuesta_usuario
    puntos = cargar_json(PUNTOS_FILE, {"total": 0, "correctas": 0, "incorrectas": 0, "racha": 0})
    if correcto:
        puntos["total"] += 10
        puntos["correctas"] += 1
        puntos["racha"] += 1
    else:
        puntos["incorrectas"] += 1
        puntos["racha"] = 0
    guardar_json(PUNTOS_FILE, puntos)
    return jsonify({
        "correcto": correcto,
        "explicacion": explicacion,
        "respuesta_correcta": data.get("respuesta_correcta"),
        "puntos": puntos
    })

@app.route('/puntos', methods=['GET'])
def get_puntos():
    return jsonify(cargar_json(PUNTOS_FILE, {"total": 0, "correctas": 0, "incorrectas": 0, "racha": 0}))

@app.route('/progreso', methods=['GET'])
def get_progreso():
    return jsonify(cargar_json(PROGRESO_FILE, {"dias_racha": 0, "ultimo_dia": "", "mensajes_total": 0}))

@app.route('/reset', methods=['POST'])
def reset():
    guardar_json(HISTORIAL_FILE, [])
    return jsonify({'ok': True})

app.run(port=5000)

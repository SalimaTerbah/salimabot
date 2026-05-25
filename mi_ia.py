import gradio as gr
import requests

MODELO = "qwen2.5:0.5b"

def responder(msg, hist, niv):
    prompt = "Eres SalimaBot profesora de espanol amable y motivadora. Nivel del estudiante: " + niv + ". Si escribe en arabe respondes en arabe con ejemplos en espanol. Si escribe en espanol corriges errores amablemente y propones ejercicios."
    mensajes = [{"role": "system", "content": prompt}]
    for h in hist:
        mensajes.append({"role": "user", "content": h["content"] if h["role"] == "user" else ""})
        mensajes.append({"role": "assistant", "content": h["content"] if h["role"] == "assistant" else ""})
    mensajes.append({"role": "user", "content": msg})
    try:
        r = requests.post("http://localhost:11434/api/chat", json={"model": MODELO, "messages": mensajes, "stream": False}, timeout=120)
        texto = r.json()["message"]["content"]
    except Exception as e:
        texto = "Error: " + str(e)
    hist.append({"role": "user", "content": msg})
    hist.append({"role": "assistant", "content": texto})
    return hist, ""

with gr.Blocks(title="SalimaBot") as app:
    gr.Markdown("# SalimaBot\n### Tu profesora personal de espanol")
    nivel = gr.Radio(choices=["A1","A2","B1","B2","C1"], value="B1", label="Tu nivel")
    chatbot = gr.Chatbot(height=400, type="messages")
    with gr.Row():
        msg = gr.Textbox(placeholder="Escribe aqui...", scale=4)
        btn = gr.Button("Enviar", scale=1)
    btn.click(fn=responder, inputs=[msg, chatbot, nivel], outputs=[chatbot, msg])
    msg.submit(fn=responder, inputs=[msg, chatbot, nivel], outputs=[chatbot, msg])

app.launch()
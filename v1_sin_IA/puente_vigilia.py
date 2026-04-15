import whisper
import subprocess
import os
import sys
from gtts import gTTS

# Función para que la IA "hable"
def decir(texto):
    print(f"IA dice: {texto}")
    # Genera el audio
    tts = gTTS(text=texto, lang='es')
    tts.save("/tmp/respuesta.mp3")
    # Convierte a formato Asterisk (WAV mono, 8000Hz)
    subprocess.run([
        'ffmpeg', '-y', '-i', '/tmp/respuesta.mp3',
        '-ar', '8000', '-ac', '1', '/tmp/ia_dice.wav'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ejecutar_porton():
    decir("Acceso concedido. Abriendo el portón ahora.")
    # Tu comando Dahua
    subprocess.run([
        'curl', '--digest', '-u', 'admin:Splitreset6901',
        'http://192.168.100.108/cgi-bin/accessControl.cgi?action=openDoor&channel=1'
    ])

def procesar_audio(ruta_audio):
    # Cargar Whisper (oído)
    model = whisper.load_model("tiny")
    result = model.transcribe(ruta_audio, language="es")
    texto_vecino = result["text"].lower().strip()
    
    if not texto_vecino:
        decir("No pude escucharte bien. Por favor, pulsa el botón de nuevo.")
        return

    print(f"El vecino dijo: {texto_vecino}")

    # Consultar a Ollama (cerebro)
    cmd_ollama = f'ollama run vigilia-mini "{texto_vecino}"'
    try:
        respuesta_ia = subprocess.check_output(cmd_ollama, shell=True).decode('utf-8').strip()
        
        if "OPEN" in respuesta_ia:
            ejecutar_porton()
        else:
            decir("Lo siento, no tengo autorización para abrir el portón.")
    except:
        decir("Hubo un error en mi sistema, intenta más tarde.")

if __name__ == "__main__":
    archivo_grabado = sys.argv[1] if len(sys.argv) > 1 else "/tmp/vecino.wav"
    procesar_audio(archivo_grabado)

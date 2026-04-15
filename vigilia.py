import subprocess

def procesar_comando(texto_usuario):
    # Consultamos a nuestra IA personalizada
    comando_ollama = f'ollama run vigilia-mini "{texto_usuario}"'
    respuesta = subprocess.check_output(comando_ollama, shell=True).decode('utf-8').strip()

    if "OPEN" in respuesta:
        print("🔓 IA dice OPEN: Abriendo portón...")
        # AQUÍ VA TU COMANDO CURL DE DAHUA
        subprocess.run(['curl', '--digest', '-u', 'admin:Splitreset6901', 'http://192.168.100.108/cgi-bin/accessControl.cgi?action=openDoor&channel=1'])
    else:
        print("❌ Acceso denegado o comando no reconocido.")

# Prueba rápida
procesar_comando("abre la puerta")

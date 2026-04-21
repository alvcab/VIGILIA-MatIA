import subprocess


VTO_IP = "192.168.100.108"
VTO_USER = "admin"
VTO_PASS = "Splitreset6901"


def open_gate():
    result = subprocess.run(
        [
            "curl",
            "-sS",
            "--digest",
            "-u",
            f"{VTO_USER}:{VTO_PASS}",
            f"http://{VTO_IP}/cgi-bin/accessControl.cgi?action=openDoor&channel=1",
        ],
        capture_output=True,
        text=True,
    )

    response_text = result.stdout.strip()
    gate_opened = result.returncode == 0 and response_text == "OK"

    if response_text:
        print(f"[GATE] stdout: {response_text}")
    if result.stderr.strip():
        print(f"[GATE] stderr: {result.stderr.strip()}")
    print(f"[GATE] opened: {gate_opened}")

    return gate_opened

def procesar_comando(texto_usuario):
    # Consultamos a nuestra IA personalizada
    comando_ollama = f'ollama run vigilia-mini "{texto_usuario}"'
    respuesta = subprocess.check_output(comando_ollama, shell=True).decode('utf-8').strip()

    if "OPEN" in respuesta:
        print("🔓 IA dice OPEN: Abriendo portón...")
        if not open_gate():
            print("❌ El comando curl no logró abrir el portón.")
    else:
        print("❌ Acceso denegado o comando no reconocido.")

# Prueba rápida
procesar_comando("abre la puerta")

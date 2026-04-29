import subprocess
import os


VTO_IP = os.environ.get("VTO_IP", "192.168.100.108")
VTO_USER = os.environ.get("VTO_USER", "admin")
VTO_PASS = os.environ.get("VTO_PASS", "Splitreset6901")
VTO_GATE_CHANNEL = int(os.environ.get("VTO_GATE_CHANNEL", "1"))
VTO_GATE_REMOTE_USER_ID = os.environ.get("VTO_GATE_REMOTE_USER_ID", "101")
VALID_MODEL_TOKENS = {"OPEN", "ERROR", "HOLA"}


def normalize_model_token(model_response):
    if model_response is None:
        return None

    normalized_response = model_response.strip().upper()
    if normalized_response in VALID_MODEL_TOKENS:
        return normalized_response
    return None


def build_gate_open_url(channel=VTO_GATE_CHANNEL, remote_user_id=None, remote_type=None):
    url = f"http://{VTO_IP}/cgi-bin/accessControl.cgi?action=openDoor&channel={channel}"
    if remote_user_id is not None:
        url = f"{url}&UserID={remote_user_id}"
    if remote_type is not None:
        url = f"{url}&Type={remote_type}"
    return url


def build_gate_open_urls(channel=VTO_GATE_CHANNEL):
    return (
        build_gate_open_url(channel=channel),
        build_gate_open_url(
            channel=channel,
            remote_user_id=VTO_GATE_REMOTE_USER_ID,
            remote_type="Remote",
        ),
    )


def open_gate():
    for attempt_index, gate_url in enumerate(build_gate_open_urls(), start=1):
        result = subprocess.run(
            [
                "curl",
                "-sS",
                "--digest",
                "-u",
                f"{VTO_USER}:{VTO_PASS}",
                gate_url,
            ],
            capture_output=True,
            text=True,
        )

        response_text = result.stdout.strip()
        gate_opened = result.returncode == 0 and response_text == "OK"

        print(f"[GATE] ip={VTO_IP} channel={VTO_GATE_CHANNEL} attempt={attempt_index}")
        print(f"[GATE] url={gate_url}")
        if response_text:
            print(f"[GATE] stdout: {response_text}")
        if result.stderr.strip():
            print(f"[GATE] stderr: {result.stderr.strip()}")
        print(f"[GATE] opened: {gate_opened}")

        if gate_opened:
            return True

    return False

def procesar_comando(texto_usuario):
    # Consultamos a nuestra IA personalizada
    respuesta = subprocess.check_output(
        ["ollama", "run", "vigilia-mini", texto_usuario],
        text=True,
    ).strip()

    if normalize_model_token(respuesta) == "OPEN":
        print("🔓 IA dice OPEN: Abriendo portón...")
        if not open_gate():
            print("❌ El comando curl no logró abrir el portón.")
    else:
        print("❌ Acceso denegado o comando no reconocido.")

# Prueba rápida
procesar_comando("abre la puerta")

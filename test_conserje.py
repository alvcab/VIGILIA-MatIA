import os
import subprocess
import sys
import time
from datetime import datetime

from v1_sin_IA.event_store import insert_access_event

# --- CONFIGURACIÓN ---
VTO_IP = "192.168.100.108"
VTO_USER = "admin"
VTO_PASS = "Splitreset6901"


def open_gate(channel=1):
    result = subprocess.run(
        [
            "curl",
            "-sS",
            "--digest",
            "-u",
            f"{VTO_USER}:{VTO_PASS}",
            f"http://{VTO_IP}/cgi-bin/accessControl.cgi?action=openDoor&channel={channel}",
        ],
        capture_output=True,
        text=True,
    )

    response_text = result.stdout.strip()
    gate_opened = result.returncode == 0 and response_text == "OK"

    print(f">>> [GATE] channel={channel} curl exit code: {result.returncode}")
    if response_text:
        print(f">>> [GATE] channel={channel} stdout: {response_text}")
    if result.stderr.strip():
        print(f">>> [GATE] channel={channel} stderr: {result.stderr.strip()}")
    print(f">>> [GATE] channel={channel} opened: {gate_opened}")

    return gate_opened


def log_manual_event(channel, gate_opened):
    event_id = insert_access_event(
        created_at=datetime.now().isoformat(timespec="seconds"),
        audio_path=None,
        transcript=f"manual trigger channel={channel}",
        model_response="OPEN" if gate_opened else "ERROR",
        gate_opened=gate_opened,
        snapshot_path=None,
        error_message=None if gate_opened else f"manual_trigger_failed channel={channel}",
    )
    print(f">>> [DB] access event saved with id={event_id}")


def diagnose_channels():
    print(">>> [DIAG] Probando canal 1...")
    channel_1_ok = open_gate(channel=1)
    time.sleep(2)

    print(">>> [DIAG] Probando canal 2...")
    channel_2_ok = open_gate(channel=2)

    print(">>> [DIAG] Resumen")
    print(f">>> [DIAG] channel=1 success: {channel_1_ok}")
    print(f">>> [DIAG] channel=2 success: {channel_2_ok}")


def abrir_y_hablar(channel=1):
    inicio = time.time()
    
    # 1. DISPARO DEL PORTÓN
    gate_opened = open_gate(channel=channel)
    log_manual_event(channel=channel, gate_opened=gate_opened)
    
    # 2. AUDIO INSTANTÁNEO (Sin esperar a la IA)
    mensaje = (
        f"Abriendo portón por canal {channel}."
        if gate_opened
        else f"No pude abrir el portón por canal {channel}."
    )
    print(f">>> [ACCION] {mensaje}")
    if sys.platform == "darwin":
        os.system(f'say "{mensaje}" &')
    else:
        os.system(f'espeak-ng -v es -s 160 "{mensaje}" &')
    
    fin = time.time()
    print(f"Tiempo de ejecución interna: {round(fin - inicio, 4)}s")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--diagnose":
        diagnose_channels()
        sys.exit(0)

    selected_channel = 1
    run_once = False
    args = [arg for arg in sys.argv[1:] if arg != "--once"]
    if "--once" in sys.argv[1:]:
        run_once = True

    if args:
        try:
            selected_channel = int(args[0])
        except ValueError:
            print("Uso: python3 test_conserje.py [channel] [--once] o python3 test_conserje.py --diagnose")
            sys.exit(1)

    print("--- VIGILIA: MODO RESPUESTA INSTANTÁNEA ---")
    print(f"Canal configurado: {selected_channel}")
    if run_once:
        print("Modo de una sola ejecucion activado.")
        abrir_y_hablar(channel=selected_channel)
        sys.exit(0)

    print("Presiona ENTER para abrir (Ctrl+C para salir)")
    
    try:
        while True:
            input("\n[LISTO] Esperando visitante...")
            abrir_y_hablar(channel=selected_channel)
    except KeyboardInterrupt:
        print("\nApagando...")

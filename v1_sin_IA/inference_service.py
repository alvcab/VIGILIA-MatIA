import json
import os
import signal
import socket
import sys
import time
from pathlib import Path

import whisper


SOCKET_PATH = Path("/tmp/vigilia_inference.sock")
WHISPER_MODEL_NAME = "tiny"
SERVER_TIMEOUT_SECONDS = 30


def send_response(connection, payload):
    body = json.dumps(payload, ensure_ascii=True) + "\n"
    connection.sendall(body.encode("utf-8"))


def receive_request(connection):
    chunks = []
    while True:
        data = connection.recv(4096)
        if not data:
            break
        chunks.append(data)
        if b"\n" in data:
            break

    if not chunks:
        return None

    message = b"".join(chunks).decode("utf-8").strip()
    if not message:
        return None
    return json.loads(message)


def handle_transcribe(model, payload):
    audio_path = payload["audio_path"]
    started_at = time.perf_counter()
    print(f"[SERVICE] action=transcribe audio_path={audio_path}", flush=True)
    result = model.transcribe(audio_path, language="es")
    return {
        "ok": True,
        "text": result["text"],
        "timing_seconds": time.perf_counter() - started_at,
    }


def remove_socket_file():
    try:
        SOCKET_PATH.unlink()
    except FileNotFoundError:
        return


def install_signal_handlers(server_socket):
    def shutdown_handler(signum, frame):
        remove_socket_file()
        server_socket.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)


def main():
    remove_socket_file()

    preload_started_at = time.perf_counter()
    model = whisper.load_model(WHISPER_MODEL_NAME)
    print(
        f"[SERVICE] whisper_model_loaded={WHISPER_MODEL_NAME} "
        f"seconds={time.perf_counter() - preload_started_at:.3f}",
        flush=True,
    )

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(str(SOCKET_PATH))
    os.chmod(SOCKET_PATH, 0o600)
    server_socket.listen()
    server_socket.settimeout(SERVER_TIMEOUT_SECONDS)
    install_signal_handlers(server_socket)

    print(f"[SERVICE] listening socket={SOCKET_PATH}", flush=True)

    try:
        while True:
            try:
                connection, _ = server_socket.accept()
            except socket.timeout:
                continue

            with connection:
                try:
                    request = receive_request(connection)
                    if not request:
                        continue

                    action = request.get("action")
                    payload = request.get("payload", {})

                    if action == "health":
                        print("[SERVICE] action=health", flush=True)
                        send_response(
                            connection,
                            {
                                "ok": True,
                                "service": "vigilia_inference",
                                "pid": os.getpid(),
                                "socket_path": str(SOCKET_PATH),
                            },
                        )
                        continue

                    if action == "transcribe":
                        send_response(connection, handle_transcribe(model, payload))
                        continue

                    send_response(connection, {"ok": False, "error": "unknown_action"})
                except Exception as exc:
                    send_response(connection, {"ok": False, "error": str(exc)})
    finally:
        remove_socket_file()


if __name__ == "__main__":
    main()

import json
import os
import signal
import socket
import sys
import time

try:
    from v1.face_engine import is_backend_available, record_face_observation_from_image
    from v1.runtime_paths import FACE_SERVICE_SOCKET_PATH, ensure_runtime_directories
except ModuleNotFoundError:
    from face_engine import is_backend_available, record_face_observation_from_image
    from runtime_paths import FACE_SERVICE_SOCKET_PATH, ensure_runtime_directories


SERVER_TIMEOUT_SECONDS = 30


def send_response(connection, payload):
    body = json.dumps(payload, ensure_ascii=True) + "\n"
    connection.sendall(body.encode("utf-8"))


def safe_send_response(connection, payload):
    try:
        send_response(connection, payload)
        return True
    except BrokenPipeError:
        print("[FACE_SERVICE] client_disconnected_before_response", flush=True)
        return False
    except OSError as exc:
        print(f"[FACE_SERVICE] response_failed error={exc}", flush=True)
        return False


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


def handle_recognize(payload):
    image_path = payload["image_path"]
    tolerance = float(payload.get("tolerance", 0.45))
    downscale_factor = payload.get("downscale_factor")
    started_at = time.perf_counter()
    print(
        f"[FACE_SERVICE] action=recognize image_path={image_path} "
        f"downscale={downscale_factor}",
        flush=True,
    )

    if not is_backend_available():
        return {
            "ok": False,
            "backend_available": False,
            "error": "face_recognition backend is not installed",
        }

    try:
        result = record_face_observation_from_image(
            image_path=image_path,
            tolerance=tolerance,
            downscale_factor=downscale_factor,
        )
    except ValueError as exc:
        return {
            "ok": True,
            "backend_available": True,
            "error": "face_encoding_not_found",
            "message": str(exc),
            "timing_seconds": time.perf_counter() - started_at,
        }

    return {
        "ok": True,
        "backend_available": True,
        "observation_id": result["observation_id"],
        "matched": result["matched"],
        "distance": result["distance"],
        "tolerance": result["tolerance"],
        "matched_person_id": result["person"]["id"] if result["person"] else None,
        "matched_person_name": result["person"]["name"] if result["person"] else None,
        "person": result["person"],
        "timing_seconds": time.perf_counter() - started_at,
    }


def remove_socket_file():
    try:
        FACE_SERVICE_SOCKET_PATH.unlink()
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
    ensure_runtime_directories()
    remove_socket_file()

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server_socket.bind(str(FACE_SERVICE_SOCKET_PATH))
    os.chmod(FACE_SERVICE_SOCKET_PATH, 0o600)
    server_socket.listen()
    server_socket.settimeout(SERVER_TIMEOUT_SECONDS)
    install_signal_handlers(server_socket)

    print(f"[FACE_SERVICE] listening socket={FACE_SERVICE_SOCKET_PATH}", flush=True)

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
                        safe_send_response(
                            connection,
                            {
                                "ok": True,
                                "service": "vigilia_face",
                                "pid": os.getpid(),
                                "socket_path": str(FACE_SERVICE_SOCKET_PATH),
                            },
                        )
                        continue

                    if action == "recognize":
                        safe_send_response(connection, handle_recognize(payload))
                        continue

                    safe_send_response(connection, {"ok": False, "error": "unknown_action"})
                except Exception as exc:
                    safe_send_response(connection, {"ok": False, "error": str(exc)})
    finally:
        remove_socket_file()


if __name__ == "__main__":
    main()

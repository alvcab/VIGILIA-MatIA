import json
import socket
import sys

try:
    from v1.runtime_paths import INFERENCE_SOCKET_PATH, ensure_runtime_directories
except ModuleNotFoundError:
    from runtime_paths import INFERENCE_SOCKET_PATH, ensure_runtime_directories


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "health"
    timeout_seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0

    ensure_runtime_directories()

    if not INFERENCE_SOCKET_PATH.exists():
        print(json.dumps({"ok": False, "error": "socket_missing"}))
        sys.exit(1)

    request_body = {"action": action, "payload": {}}

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout_seconds)
            client.connect(str(INFERENCE_SOCKET_PATH))
            client.sendall((json.dumps(request_body) + "\n").encode("utf-8"))

            chunks = []
            while True:
                data = client.recv(4096)
                if not data:
                    break
                chunks.append(data)
                if b"\n" in data:
                    break
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)

    if not chunks:
        print(json.dumps({"ok": False, "error": "empty_response"}))
        sys.exit(1)

    payload_text = b"".join(chunks).decode("utf-8").strip()
    print(payload_text)

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        sys.exit(1)

    sys.exit(0 if payload.get("ok") else 1)


if __name__ == "__main__":
    main()

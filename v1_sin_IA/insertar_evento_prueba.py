import sys
from datetime import datetime

try:
    from v1_sin_IA.event_store import insert_access_event
except ModuleNotFoundError:
    from event_store import insert_access_event


def print_usage():
    print("Uso:")
    print("  python3 v1_sin_IA/insertar_evento_prueba.py")
    print("  python3 v1_sin_IA/insertar_evento_prueba.py [open|deny]")


def main():
    mode = "open"

    if len(sys.argv) > 2:
        print_usage()
        sys.exit(1)

    if len(sys.argv) == 2:
        mode = sys.argv[1].lower()
        if mode not in {"open", "deny"}:
            print_usage()
            sys.exit(1)

    gate_opened = mode == "open"
    transcript = "abre la puerta" if gate_opened else "hola, solo vengo a consultar"
    model_response = "OPEN" if gate_opened else "ERROR"
    error_message = None if gate_opened else "manual_test_denied"

    event_id = insert_access_event(
        created_at=datetime.now().isoformat(timespec="seconds"),
        audio_path="/tmp/manual_test.wav",
        transcript=transcript,
        model_response=model_response,
        gate_opened=gate_opened,
        snapshot_path="captures/manual_test_snapshot.jpg",
        error_message=error_message,
    )

    print(f"Evento de prueba insertado con id={event_id}")


if __name__ == "__main__":
    main()

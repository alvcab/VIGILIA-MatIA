import sys
from pathlib import Path

try:
    from v1_sin_IA.event_store import get_recent_access_events
except ModuleNotFoundError:
    from event_store import get_recent_access_events


def print_usage():
    print("Uso:")
    print("  python3 v1_sin_IA/ver_eventos.py")
    print("  python3 v1_sin_IA/ver_eventos.py [limite]")


def format_value(value):
    if value is None or value == "":
        return "-"
    return str(value)


def snapshot_status(snapshot_path):
    if snapshot_path is None or snapshot_path == "":
        return "-"
    return "exists" if Path(snapshot_path).exists() else "missing"


def main():
    limit = 10

    if len(sys.argv) > 2:
        print_usage()
        sys.exit(1)

    if len(sys.argv) == 2:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print_usage()
            sys.exit(1)

    events = get_recent_access_events(limit=limit)

    if not events:
        print("No hay eventos registrados todavia.")
        return

    for event in events:
        print(f"id: {event['id']}")
        print(f"created_at: {format_value(event['created_at'])}")
        print(f"audio_path: {format_value(event['audio_path'])}")
        print(f"transcript: {format_value(event['transcript'])}")
        print(f"model_response: {format_value(event['model_response'])}")
        print(f"gate_opened: {bool(event['gate_opened'])}")
        print(f"decision_source: {format_value(event.get('decision_source'))}")
        print(f"decision_reason: {format_value(event.get('decision_reason'))}")
        print(f"snapshot_path: {format_value(event['snapshot_path'])}")
        print(f"snapshot_status: {snapshot_status(event['snapshot_path'])}")
        print(f"error_message: {format_value(event['error_message'])}")
        print("-" * 40)


if __name__ == "__main__":
    main()

import json
import sys

try:
    from v1_sin_IA.face_engine import (
        is_backend_available,
        record_face_observation_from_image,
    )
except ModuleNotFoundError:
    from face_engine import (
        is_backend_available,
        record_face_observation_from_image,
    )


def print_usage():
    print("Uso:")
    print("  python3 v1_sin_IA/reconocer_rostro.py <image_path>")
    print("  python3 v1_sin_IA/reconocer_rostro.py <image_path> --json")


def main():
    json_output = "--json" in sys.argv[1:]
    args = [arg for arg in sys.argv[1:] if arg != "--json"]

    if len(args) != 1:
        print_usage()
        sys.exit(1)

    image_path = args[0]

    if not is_backend_available():
        if json_output:
            print(
                json.dumps(
                    {
                        "backend_available": False,
                        "error": "face_recognition backend is not installed",
                    }
                )
            )
        else:
            print("El backend face_recognition aun no esta instalado.")
            print("La base SQLite y el flujo de matching ya quedaron preparados.")
        sys.exit(2)

    result = record_face_observation_from_image(image_path=image_path)

    if json_output:
        payload = {
            "backend_available": True,
            "observation_id": result["observation_id"],
            "matched": result["matched"],
            "distance": result["distance"],
            "tolerance": result["tolerance"],
            "matched_person_id": result["person"]["id"] if result["person"] else None,
            "matched_person_name": result["person"]["name"] if result["person"] else None,
            "person": result["person"],
        }
        print(json.dumps(payload))
        return

    print(f"observation_id: {result['observation_id']}")
    print(f"matched: {result['matched']}")
    print(f"distance: {result['distance']}")
    print(f"tolerance: {result['tolerance']}")
    if result["person"]:
        print(f"matched_person_id: {result['person']['id']}")
        print(f"matched_person_name: {result['person']['name']}")
    else:
        print("matched_person_id: -")
        print("matched_person_name: -")


if __name__ == "__main__":
    main()

import sys

try:
    from v1_sin_IA.face_engine import record_face_observation_from_image
    from v1_sin_IA.face_registry import add_person
except ModuleNotFoundError:
    from face_engine import record_face_observation_from_image
    from face_registry import add_person


def print_usage():
    print("Uso:")
    print(
        "  python v1_sin_IA/probar_reconocimiento.py "
        "<nombre> <imagen_referencia> <imagen_a_reconocer> [tolerance]"
    )


def main():
    if len(sys.argv) not in {4, 5}:
        print_usage()
        sys.exit(1)

    person_name = sys.argv[1]
    reference_image_path = sys.argv[2]
    image_to_recognize = sys.argv[3]
    tolerance = float(sys.argv[4]) if len(sys.argv) == 5 else 0.45

    print("[FACE] Registrando persona autorizada...")
    add_person([person_name, reference_image_path])

    print("[FACE] Ejecutando reconocimiento...")
    result = record_face_observation_from_image(
        image_path=image_to_recognize,
        tolerance=tolerance,
    )

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

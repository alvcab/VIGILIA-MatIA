import json
from pathlib import Path

try:
    import face_recognition
except ModuleNotFoundError:
    face_recognition = None

try:
    from v1_sin_IA.event_store import (
        get_authorized_people,
        insert_face_observation,
    )
except ModuleNotFoundError:
    from event_store import (
        get_authorized_people,
        insert_face_observation,
    )


def is_backend_available():
    return face_recognition is not None


def require_backend():
    if not is_backend_available():
        raise RuntimeError(
            "face_recognition backend is not installed. "
            "Install dlib and face_recognition first."
        )


def load_face_encoding(image_path):
    require_backend()

    image_path = Path(image_path)
    image = face_recognition.load_image_file(str(image_path))
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        raise ValueError(f"No face encoding found in {image_path}")

    return encodings[0]


def encode_face_as_json(image_path):
    encoding = load_face_encoding(image_path)
    return json.dumps(encoding.tolist())


def compare_against_registry(image_path, tolerance=0.45):
    require_backend()

    unknown_encoding = load_face_encoding(image_path)
    authorized_people = get_authorized_people()

    best_match = None
    best_distance = None

    for person in authorized_people:
        reference_image_path = person.get("reference_image_path")
        if not reference_image_path:
            continue

        try:
            known_encoding = load_face_encoding(reference_image_path)
        except Exception:
            continue

        distance = face_recognition.face_distance(
            [known_encoding],
            unknown_encoding,
        )[0]

        if best_distance is None or distance < best_distance:
            best_distance = float(distance)
            best_match = person

    if best_match is None:
        return {
            "matched": False,
            "person": None,
            "distance": None,
            "tolerance": tolerance,
        }

    return {
        "matched": best_distance <= tolerance,
        "person": best_match,
        "distance": best_distance,
        "tolerance": tolerance,
    }


def record_face_observation_from_image(image_path, tolerance=0.45):
    comparison = compare_against_registry(image_path=image_path, tolerance=tolerance)

    observation_id = insert_face_observation(
        image_path=str(image_path),
        matched_person_id=comparison["person"]["id"] if comparison["person"] else None,
        confidence=(1.0 - comparison["distance"]) if comparison["distance"] is not None else None,
        face_embedding_json=encode_face_as_json(image_path),
        notes="matched" if comparison["matched"] else "unmatched",
    )

    comparison["observation_id"] = observation_id
    return comparison

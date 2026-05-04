import json
import os
import time
from pathlib import Path

try:
    import face_recognition
except ModuleNotFoundError:
    face_recognition = None

try:
    from v1.event_store import (
        get_authorized_people,
        insert_face_observation,
    )
except ModuleNotFoundError:
    from event_store import (
        get_authorized_people,
        insert_face_observation,
    )


REFERENCE_ENCODING_CACHE = {}
FACE_ENCODING_DOWNSCALE_FACTOR = max(
    1, int(os.environ.get("VIGILIA_FACE_ENCODING_DOWNSCALE_FACTOR", "2"))
)


def is_backend_available():
    return face_recognition is not None


def require_backend():
    if not is_backend_available():
        raise RuntimeError(
            "face_recognition backend is not installed. "
            "Install dlib and face_recognition first."
        )


def resolve_downscale_factor(downscale_factor=None):
    if downscale_factor is None:
        return FACE_ENCODING_DOWNSCALE_FACTOR
    return max(1, int(downscale_factor))


def load_face_encoding(image_path, downscale_factor=None):
    started_at = time.perf_counter()
    require_backend()

    resolved_downscale_factor = resolve_downscale_factor(downscale_factor)
    image_path = Path(image_path)
    image = face_recognition.load_image_file(str(image_path))
    if resolved_downscale_factor > 1:
        image = image[
            ::resolved_downscale_factor,
            ::resolved_downscale_factor,
        ].copy()

    encodings = face_recognition.face_encodings(image)

    if not encodings:
        raise ValueError(f"No face encoding found in {image_path}")

    print(
        f"[TIMING] face_encoding_seconds path={image_path} "
        f"value={time.perf_counter() - started_at:.3f} "
        f"downscale={resolved_downscale_factor}"
    )
    return encodings[0]


def load_face_encoding_cached(image_path, downscale_factor=None):
    image_path = Path(image_path)
    cache_key = None
    resolved_downscale_factor = resolve_downscale_factor(downscale_factor)

    try:
        stat = image_path.stat()
        cache_key = (str(image_path.resolve()), stat.st_mtime_ns, resolved_downscale_factor)
    except FileNotFoundError:
        return load_face_encoding(image_path, downscale_factor=resolved_downscale_factor)

    cached_encoding = REFERENCE_ENCODING_CACHE.get(cache_key)
    if cached_encoding is not None:
        print(f"[TIMING] face_encoding_cache_hit path={image_path}")
        return cached_encoding

    encoding = load_face_encoding(image_path, downscale_factor=resolved_downscale_factor)
    REFERENCE_ENCODING_CACHE.clear()
    REFERENCE_ENCODING_CACHE[cache_key] = encoding
    return encoding


def encode_face_as_json(image_path):
    encoding = load_face_encoding(image_path)
    return json.dumps(encoding.tolist())


def compare_against_registry(image_path, tolerance=0.45, downscale_factor=None):
    started_at = time.perf_counter()
    require_backend()

    unknown_encoding = load_face_encoding(image_path, downscale_factor=downscale_factor)
    unknown_encoding_ready_at = time.perf_counter()
    print(
        "[TIMING] face_unknown_encoding_ready_seconds "
        f"value={unknown_encoding_ready_at - started_at:.3f}"
    )
    authorized_people = get_authorized_people()
    registry_loaded_at = time.perf_counter()
    print(
        "[TIMING] face_registry_load_seconds "
        f"value={registry_loaded_at - unknown_encoding_ready_at:.3f}"
    )

    best_match = None
    best_distance = None

    for person in authorized_people:
        reference_image_path = person.get("reference_image_path")
        if not reference_image_path:
            continue

        try:
            known_encoding = load_face_encoding_cached(
                reference_image_path,
                downscale_factor=downscale_factor,
            )
        except Exception:
            continue

        distance = face_recognition.face_distance(
            [known_encoding],
            unknown_encoding,
        )[0]

        if best_distance is None or distance < best_distance:
            best_distance = float(distance)
            best_match = person

    print(
        "[TIMING] face_registry_compare_seconds "
        f"value={time.perf_counter() - registry_loaded_at:.3f}"
    )

    if best_match is None:
        print(
            "[TIMING] face_compare_total_seconds "
            f"value={time.perf_counter() - started_at:.3f}"
        )
        return {
            "matched": False,
            "person": None,
            "distance": None,
            "tolerance": tolerance,
        }

    print(
        "[TIMING] face_compare_total_seconds "
        f"value={time.perf_counter() - started_at:.3f}"
    )
    return {
        "matched": best_distance <= tolerance,
        "person": best_match,
        "distance": best_distance,
        "tolerance": tolerance,
    }


def record_face_observation_from_image(image_path, tolerance=0.45, downscale_factor=None):
    started_at = time.perf_counter()
    require_backend()

    image_path = str(image_path)
    unknown_encoding = load_face_encoding(image_path, downscale_factor=downscale_factor)
    comparison = compare_against_registry_with_encoding(
        unknown_encoding=unknown_encoding,
        tolerance=tolerance,
    )
    face_embedding_json = json.dumps(unknown_encoding.tolist())

    observation_id = insert_face_observation(
        image_path=image_path,
        matched_person_id=comparison["person"]["id"] if comparison["person"] else None,
        confidence=(1.0 - comparison["distance"]) if comparison["distance"] is not None else None,
        face_embedding_json=face_embedding_json,
        notes="matched" if comparison["matched"] else "unmatched",
    )

    comparison["observation_id"] = observation_id
    print(
        "[TIMING] face_observation_total_seconds "
        f"value={time.perf_counter() - started_at:.3f}"
    )
    return comparison


def compare_against_registry_with_encoding(unknown_encoding, tolerance=0.45):
    started_at = time.perf_counter()
    authorized_people = get_authorized_people()
    registry_loaded_at = time.perf_counter()
    print(
        "[TIMING] face_registry_load_seconds "
        f"value={registry_loaded_at - started_at:.3f}"
    )

    best_match = None
    best_distance = None

    for person in authorized_people:
        reference_image_path = person.get("reference_image_path")
        if not reference_image_path:
            continue

        try:
            known_encoding = load_face_encoding_cached(reference_image_path)
        except Exception:
            continue

        distance = face_recognition.face_distance(
            [known_encoding],
            unknown_encoding,
        )[0]

        if best_distance is None or distance < best_distance:
            best_distance = float(distance)
            best_match = person

    print(
        "[TIMING] face_registry_compare_seconds "
        f"value={time.perf_counter() - registry_loaded_at:.3f}"
    )
    print(
        "[TIMING] face_compare_total_seconds "
        f"value={time.perf_counter() - started_at:.3f}"
    )

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

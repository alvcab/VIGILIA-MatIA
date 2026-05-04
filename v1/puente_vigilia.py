import subprocess
import sys
import json
import os
import re
import socket
import unicodedata
import time
import signal
import importlib
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

try:
    from v1.event_store import (
        get_enabled_access_phrases,
        get_resident_aliases,
        get_residents,
        insert_access_event,
    )
    from v1.vto_camera import capture_snapshot, VTO_FAST_FACE_SUBTYPE
except ModuleNotFoundError:
    from event_store import (
        get_enabled_access_phrases,
        get_resident_aliases,
        get_residents,
        insert_access_event,
    )
    from vto_camera import capture_snapshot, VTO_FAST_FACE_SUBTYPE

try:
    from v1.runtime_paths import (
        DEFAULT_RESPONSE_AUDIO_PATH as RUNTIME_DEFAULT_RESPONSE_AUDIO_PATH,
        FACE_SERVICE_SOCKET_PATH as RUNTIME_FACE_SERVICE_SOCKET_PATH,
        INFERENCE_SOCKET_PATH as RUNTIME_INFERENCE_SOCKET_PATH,
        ensure_runtime_directories,
    )
except ModuleNotFoundError:
    from runtime_paths import (
        DEFAULT_RESPONSE_AUDIO_PATH as RUNTIME_DEFAULT_RESPONSE_AUDIO_PATH,
        FACE_SERVICE_SOCKET_PATH as RUNTIME_FACE_SERVICE_SOCKET_PATH,
        INFERENCE_SOCKET_PATH as RUNTIME_INFERENCE_SOCKET_PATH,
        ensure_runtime_directories,
    )

VTO_IP = os.environ.get("VTO_IP", "192.168.100.108")
VTO_USER = os.environ.get("VTO_USER", "admin")
VTO_PASS = os.environ.get("VTO_PASS", "Splitreset6901")
VTO_GATE_CHANNEL = int(os.environ.get("VTO_GATE_CHANNEL", "1"))
VTO_GATE_TIMEOUT_SECONDS = float(os.environ.get("VTO_GATE_TIMEOUT_SECONDS", "6"))
VTO_GATE_REMOTE_USER_ID = os.environ.get("VTO_GATE_REMOTE_USER_ID", "101")
FACE_ENV_PYTHON = Path.home() / "miniforge3" / "envs" / "vigilia-face" / "bin" / "python"
FACE_RECOGNIZER_SCRIPT = Path(__file__).with_name("reconocer_rostro.py")
FACE_SERVICE_SOCKET_PATH = RUNTIME_FACE_SERVICE_SOCKET_PATH
INFERENCE_SOCKET_PATH = RUNTIME_INFERENCE_SOCKET_PATH
DEFAULT_RESPONSE_AUDIO_PATH = RUNTIME_DEFAULT_RESPONSE_AUDIO_PATH
DECISION_MODEL_NAME = os.environ.get("VIGILIA_DECISION_MODEL", "vigilia-mini")
SPOKEN_RESPONSE_MODEL_NAME = os.environ.get(
    "VIGILIA_SPOKEN_RESPONSE_MODEL",
    DECISION_MODEL_NAME,
)
MODEL_TIMEOUT_SECONDS = float(os.environ.get("VIGILIA_MODEL_TIMEOUT_SECONDS", "10"))
SPOKEN_RESPONSE_TIMEOUT_SECONDS = float(
    os.environ.get("VIGILIA_SPOKEN_RESPONSE_TIMEOUT_SECONDS", "8")
)
INFERENCE_SERVICE_TIMEOUT_SECONDS = float(
    os.environ.get("VIGILIA_INFERENCE_SERVICE_TIMEOUT_SECONDS", "8")
)
AUDIO_TRANSCRIPTION_TIMEOUT_SECONDS = int(os.environ.get("VIGILIA_AUDIO_TRANSCRIPTION_TIMEOUT_SECONDS", "12"))
AUDIO_TARGET_MAX_DB = float(os.environ.get("VIGILIA_AUDIO_TARGET_MAX_DB", "-3"))
AUDIO_MAX_GAIN_DB = float(os.environ.get("VIGILIA_AUDIO_MAX_GAIN_DB", "24"))
TTS_TIMEOUT_SECONDS = float(os.environ.get("VIGILIA_TTS_TIMEOUT_SECONDS", "6"))
LOCAL_RESPONSE_PLAYBACK_ENABLED = os.environ.get(
    "VIGILIA_PLAY_RESPONSE_LOCALLY",
    "1",
).strip().lower() in {"1", "true", "yes", "on"}
LOCAL_RESPONSE_PLAYBACK_TIMEOUT_SECONDS = float(
    os.environ.get("VIGILIA_LOCAL_RESPONSE_PLAYBACK_TIMEOUT_SECONDS", "10")
)
PREFER_DIRECT_LOCAL_TTS = os.environ.get(
    "VIGILIA_PREFER_DIRECT_LOCAL_TTS",
    "1",
).strip().lower() in {"1", "true", "yes", "on"}
DISABLE_VTO_SNAPSHOT = os.environ.get(
    "VIGILIA_DISABLE_VTO_SNAPSHOT",
    "0",
).strip().lower() in {"1", "true", "yes", "on"}
ENABLE_LOCAL_FOLLOWUP_CAPTURE = os.environ.get(
    "VIGILIA_ENABLE_LOCAL_FOLLOWUP_CAPTURE",
    "1",
).strip().lower() in {"1", "true", "yes", "on"}
LOCAL_FOLLOWUP_AUDIO_DEVICE = os.environ.get(
    "VIGILIA_LOCAL_FOLLOWUP_AUDIO_DEVICE",
    ":1",
)
LOCAL_FOLLOWUP_DURATION_SECONDS = float(
    os.environ.get("VIGILIA_LOCAL_FOLLOWUP_DURATION_SECONDS", "4")
)
VALID_MODEL_TOKENS = {"OPEN", "ERROR", "HOLA"}
VOICE_OPEN_KEYWORDS = (
    "abre",
    "abrir",
    "abran",
    "abrame",
    "ábreme",
    "porton",
    "portón",
    "puerta",
    "deja pasar",
    "dejame pasar",
    "déjame pasar",
    "acceso",
)
VOICE_OPEN_PHRASES = (
    "abre el porton por favor",
    "abrir el porton por favor",
    "abre el porton",
    "abrir el porton",
    "abre la puerta",
    "abrir la puerta",
    "abreme el porton",
    "abreme la puerta",
    "dejame pasar",
    "deja pasar",
)
GREETING_ONLY_PHRASES = (
    "hola",
    "hola hola",
    "hola buenas",
    "hola buenos dias",
    "hola buenas tardes",
    "hola buenas noches",
    "buenos dias",
    "buenas tardes",
    "buenas noches",
)
VOICE_OPEN_FUZZY_THRESHOLD = 0.72
VOICE_OPEN_KEYWORD_FUZZY_THRESHOLD = 0.78
FACE_RETRY_ON_OPEN_REQUESTS = 2
FAST_FACE_ENTRY_ATTEMPTS = int(os.environ.get("VIGILIA_FAST_FACE_ENTRY_ATTEMPTS", "3"))
FAST_FACE_ENTRY_PAUSE_SECONDS = float(
    os.environ.get("VIGILIA_FAST_FACE_ENTRY_PAUSE_SECONDS", "0.35")
)
FAST_FACE_DOWNSCALE_FACTOR = os.environ.get("VIGILIA_FAST_FACE_DOWNSCALE_FACTOR", "4")
FACE_SERVICE_TIMEOUT_SECONDS = float(os.environ.get("VIGILIA_FACE_SERVICE_TIMEOUT_SECONDS", "8"))
FACE_BORDERLINE_DISTANCE_MARGIN = 0.10
FACE_KNOWN_RESIDENT_EXTENDED_MARGIN = float(
    os.environ.get("VIGILIA_FACE_KNOWN_RESIDENT_EXTENDED_MARGIN", "0.15")
)
CLAIMED_UNIT_PATTERNS = (
    r"\b(?:depto|departamento|dpto|depa|unidad)\s+([a-z0-9-]+)\b",
    r"\b(?:torre|block|bloque)\s+([a-z0-9-]+)\b",
)
DELIVERY_KEYWORDS = (
    "paquete",
    "encomienda",
    "delivery",
    "pedido",
    "reparto",
    "repartidor",
    "courier",
)
whisper = None


def build_gate_open_url(channel=VTO_GATE_CHANNEL, remote_user_id=None, remote_type=None):
    url = f"http://{VTO_IP}/cgi-bin/accessControl.cgi?action=openDoor&channel={channel}"
    if remote_user_id is not None:
        url = f"{url}&UserID={remote_user_id}"
    if remote_type is not None:
        url = f"{url}&Type={remote_type}"
    return url


def build_gate_open_urls(channel=VTO_GATE_CHANNEL):
    return (
        build_gate_open_url(channel=channel),
        build_gate_open_url(
            channel=channel,
            remote_user_id=VTO_GATE_REMOTE_USER_ID,
            remote_type="Remote",
        ),
    )


def get_whisper_module():
    global whisper
    if whisper is not None:
        return whisper

    try:
        whisper = importlib.import_module("whisper")
        return whisper
    except KeyboardInterrupt as exc:
        raise RuntimeError("local_transcription_import_interrupted") from exc
    except Exception as exc:
        raise RuntimeError("local_transcription_import_failed") from exc


def render_asterisk_audio_variants(source_audio_path, output_base_path, timeout_seconds):
    output_base_path = Path(output_base_path)
    wav_path = output_base_path.with_suffix(".wav")
    alaw_path = output_base_path.with_suffix(".alaw")
    ulaw_path = output_base_path.with_suffix(".ulaw")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_audio_path),
            "-ar",
            "8000",
            "-ac",
            "1",
            str(wav_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout_seconds,
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_audio_path),
            "-f",
            "alaw",
            "-ar",
            "8000",
            "-ac",
            "1",
            str(alaw_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout_seconds,
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source_audio_path),
            "-f",
            "mulaw",
            "-ar",
            "8000",
            "-ac",
            "1",
            str(ulaw_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout_seconds,
        check=True,
    )


def play_local_response_audio(response_audio_path):
    if not LOCAL_RESPONSE_PLAYBACK_ENABLED:
        return

    response_audio_path = Path(response_audio_path)
    if not response_audio_path.exists():
        return

    try:
        subprocess.Popen(
            ["afplay", str(response_audio_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        print(f"[TTS] local_playback error={exc}")


def start_direct_local_tts(texto):
    if not LOCAL_RESPONSE_PLAYBACK_ENABLED or not PREFER_DIRECT_LOCAL_TTS:
        return False

    try:
        subprocess.run(
            ["say", "-v", "Monica", texto],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TTS_TIMEOUT_SECONDS,
            check=False,
        )
        return True
    except Exception as exc:
        print(f"[TTS] direct_local_tts error={exc}")
        return False


# Función para que la IA "hable"
def decir(texto, response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH):
    ensure_runtime_directories()
    started_at = time.perf_counter()
    print(f"IA dice: {texto}")
    direct_local_tts_started = start_direct_local_tts(texto)
    response_audio_path = Path(response_audio_path)
    response_audio_path.parent.mkdir(parents=True, exist_ok=True)
    temp_aiff_path = response_audio_path.with_suffix(".aiff")
    temp_mp3_path = response_audio_path.with_suffix(".mp3")

    source_audio_path = None
    try:
        say_result = subprocess.run(
            [
                "say",
                "-v",
                "Monica",
                "-o",
                str(temp_aiff_path),
                texto,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=TTS_TIMEOUT_SECONDS,
        )

        if say_result.returncode == 0 and temp_aiff_path.exists():
            source_audio_path = temp_aiff_path
        else:
            try:
                from gtts import gTTS
            except ModuleNotFoundError as exc:
                raise RuntimeError("local_tts_failed_and_gtts_not_installed") from exc

            tts = gTTS(text=texto, lang="es")
            tts.save(str(temp_mp3_path))
            source_audio_path = temp_mp3_path

        render_asterisk_audio_variants(
            source_audio_path=source_audio_path,
            output_base_path=response_audio_path.with_suffix(""),
            timeout_seconds=TTS_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        print(f"[TTS] fallback error={exc}")
        silent_source_path = response_audio_path.with_suffix(".silence.wav")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=8000:cl=mono",
                "-t",
                "0.5",
                str(silent_source_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if silent_source_path.exists():
            try:
                render_asterisk_audio_variants(
                    source_audio_path=silent_source_path,
                    output_base_path=response_audio_path.with_suffix(""),
                    timeout_seconds=TTS_TIMEOUT_SECONDS,
                )
            finally:
                silent_source_path.unlink(missing_ok=True)
    finally:
        temp_aiff_path.unlink(missing_ok=True)
        temp_mp3_path.unlink(missing_ok=True)

    if not direct_local_tts_started:
        play_local_response_audio(response_audio_path)
    print(f"[TIMING] tts_seconds={time.perf_counter() - started_at:.3f}")

def ejecutar_porton(
    response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH,
    success_message="Acceso concedido. Abriendo el portón ahora.",
    failure_message="No pude abrir el portón.",
    speak_response=True,
):
    started_at = time.perf_counter()
    gate_opened = False

    for attempt_index, gate_url in enumerate(build_gate_open_urls(), start=1):
        try:
            result = subprocess.run(
                [
                    "curl",
                    "-sS",
                    "--digest",
                    "-u",
                    f"{VTO_USER}:{VTO_PASS}",
                    gate_url,
                ],
                capture_output=True,
                text=True,
                timeout=VTO_GATE_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print(f"[GATE] ip={VTO_IP} channel={VTO_GATE_CHANNEL} attempt={attempt_index}")
            print(f"[GATE] url={gate_url}")
            print("[GATE] error: timeout")
            continue
        except Exception as exc:
            print(f"[GATE] ip={VTO_IP} channel={VTO_GATE_CHANNEL} attempt={attempt_index}")
            print(f"[GATE] url={gate_url}")
            print(f"[GATE] error: {exc}")
            continue

        response_text = result.stdout.strip()
        gate_opened = result.returncode == 0 and response_text == "OK"

        print(f"[GATE] ip={VTO_IP} channel={VTO_GATE_CHANNEL} attempt={attempt_index}")
        print(f"[GATE] url={gate_url}")
        if response_text:
            print(f"[GATE] stdout: {response_text}")
        if result.stderr.strip():
            print(f"[GATE] stderr: {result.stderr.strip()}")
        print(f"[GATE] opened: {gate_opened}")

        if gate_opened:
            break

    print(f"[TIMING] gate_request_seconds={time.perf_counter() - started_at:.3f}")

    if speak_response:
        if gate_opened:
            decir(success_message, response_audio_path=response_audio_path)
        else:
            decir(failure_message, response_audio_path=response_audio_path)

    return gate_opened


def try_capture_snapshot():
    started_at = time.perf_counter()
    if DISABLE_VTO_SNAPSHOT:
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        print("[VTO] Snapshot disabled by environment")
        return None, "snapshot_disabled"

    try:
        snapshot_path = capture_snapshot()
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        return str(snapshot_path), None
    except KeyboardInterrupt:
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        print("[VTO] Snapshot interrupted")
        return None, "snapshot_interrupted"
    except Exception as exc:
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        print(f"[VTO] Snapshot failed: {exc}")
        return None, str(exc)


def build_local_audio_capture_command(output_path, duration_seconds, device_spec):
    base_command = [
        "ffmpeg",
        "-y",
        "-f",
        "avfoundation",
    ]

    normalized_device_spec = (device_spec or "").strip()
    if normalized_device_spec.startswith(":") and normalized_device_spec[1:].isdigit():
        normalized_device_spec = normalized_device_spec[1:]

    if normalized_device_spec.isdigit():
        return base_command + [
            "-audio_device_index",
            normalized_device_spec,
            "-i",
            "",
            "-t",
            str(duration_seconds),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_path),
        ]

    audio_input = normalized_device_spec or ":0"
    return base_command + [
        "-i",
        audio_input,
        "-t",
        str(duration_seconds),
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
    ]


def capture_local_followup_audio(output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        build_local_audio_capture_command(
            output_path=output_path,
            duration_seconds=LOCAL_FOLLOWUP_DURATION_SECONDS,
            device_spec=LOCAL_FOLLOWUP_AUDIO_DEVICE,
        ),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=max(LOCAL_FOLLOWUP_DURATION_SECONDS + 3, 6),
        check=True,
    )

    return output_path


def send_service_request(action, payload, timeout_seconds, socket_path):
    if not socket_path.exists():
        return None

    started_at = time.perf_counter()
    request_body = {
        "action": action,
        "payload": payload,
    }

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout_seconds)
            client.connect(str(socket_path))
            client.sendall((json.dumps(request_body) + "\n").encode("utf-8"))

            chunks = []
            while True:
                data = client.recv(4096)
                if not data:
                    break
                chunks.append(data)
                if b"\n" in data:
                    break
    except (OSError, TimeoutError, socket.timeout) as exc:
        print(f"[SERVICE] request_failed action={action} error={exc}")
        return None

    if not chunks:
        return None

    payload_text = b"".join(chunks).decode("utf-8").strip()
    response_payload = json.loads(payload_text)
    print(
        f"[TIMING] service_roundtrip_seconds action={action} "
        f"value={time.perf_counter() - started_at:.3f}"
    )
    return response_payload


def try_face_recognition(snapshot_path, extra_env=None):
    started_at = time.perf_counter()
    print("[FACE] starting recognition")
    if not snapshot_path:
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_skipped_no_snapshot"

    downscale_factor = None
    if extra_env:
        downscale_factor = extra_env.get("VIGILIA_FACE_ENCODING_DOWNSCALE_FACTOR")

    face_service_payload = send_service_request(
        action="recognize",
        payload={
            "image_path": snapshot_path,
            "downscale_factor": downscale_factor,
        },
        timeout_seconds=FACE_SERVICE_TIMEOUT_SECONDS,
        socket_path=FACE_SERVICE_SOCKET_PATH,
    )
    if face_service_payload and face_service_payload.get("ok"):
        if face_service_payload.get("error") == "face_encoding_not_found":
            print(f"[FACE] no_face_detected snapshot={snapshot_path}")
            print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
            return None, "face_encoding_not_found"

        if not face_service_payload.get("backend_available", False):
            print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
            return None, face_service_payload.get(
                "error",
                "face_recognition_backend_unavailable",
            )

        print(
            "[FACE] "
            f"matched={face_service_payload.get('matched')} "
            f"name={face_service_payload.get('matched_person_name')} "
            f"distance={face_service_payload.get('distance')}"
        )
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return face_service_payload, None

    if not FACE_ENV_PYTHON.exists():
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_env_not_found"

    try:
        process_env = os.environ.copy()
        if extra_env:
            process_env.update(extra_env)
        result = subprocess.run(
            [
                str(FACE_ENV_PYTHON),
                str(FACE_RECOGNIZER_SCRIPT),
                snapshot_path,
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=12,
            env=process_env,
        )
    except subprocess.TimeoutExpired:
        print("[FACE] error: timeout")
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_timeout"
    except KeyboardInterrupt:
        print("[FACE] error: interrupted")
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_interrupted"
    except Exception as exc:
        print(f"[FACE] error: {exc}")
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_execution_error"

    if result.returncode not in {0, 2}:
        stderr_text = result.stderr.strip()
        print(f"[FACE] stderr: {stderr_text}")
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_execution_error"

    stdout_text = result.stdout.strip().splitlines()
    if not stdout_text:
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_no_output"

    payload_text = stdout_text[-1]
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        print(f"[FACE] raw output: {result.stdout.strip()}")
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_invalid_output"

    if payload.get("error") == "face_encoding_not_found":
        print(f"[FACE] no_face_detected snapshot={snapshot_path}")
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_encoding_not_found"

    if not payload.get("backend_available", False):
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, payload.get("error", "face_recognition_backend_unavailable")

    print(
        "[FACE] "
        f"matched={payload.get('matched')} "
        f"name={payload.get('matched_person_name')} "
        f"distance={payload.get('distance')}"
    )
    print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
    return payload, None


def retry_face_recognition_for_open_request(visitor_text, face_result, face_error):
    if not detect_open_request(visitor_text):
        return face_result, face_error, None

    if has_trusted_face_match(face_result):
        return face_result, face_error, None

    best_face_result = face_result
    best_face_error = face_error
    retry_snapshot_path = None

    for attempt in range(1, FACE_RETRY_ON_OPEN_REQUESTS + 1):
        print(f"[FACE] retry attempt={attempt}")
        retry_snapshot_path, retry_snapshot_error = try_capture_snapshot()
        retry_face_result, retry_face_error = try_face_recognition(retry_snapshot_path)

        if has_trusted_face_match(retry_face_result):
            return retry_face_result, combine_errors(face_error, retry_snapshot_error, retry_face_error), retry_snapshot_path

        if best_face_result is None and retry_face_result is not None:
            best_face_result = retry_face_result
            best_face_error = combine_errors(face_error, retry_snapshot_error, retry_face_error)
            continue

        current_distance = face_result_distance(best_face_result)
        retry_distance = face_result_distance(retry_face_result)
        if retry_distance is not None and (current_distance is None or retry_distance < current_distance):
            best_face_result = retry_face_result
            best_face_error = combine_errors(face_error, retry_snapshot_error, retry_face_error)

    return best_face_result, best_face_error, retry_snapshot_path


def build_denial_message(visitor_text, face_error, resident_context=None):
    resident_context = resident_context or {}
    claimed_resident_name = resident_context.get("claimed_resident_name")
    claimed_unit = resident_context.get("claimed_unit")

    if detect_open_request(visitor_text) and face_error and "face_encoding_not_found" in face_error:
        return "No logro verte bien. Acercate a la camara, mira de frente y vuelve a intentarlo."

    if detect_open_request(visitor_text) and not has_claimed_resident_context(resident_context):
        return "Para autorizar la apertura, dime a que residente o departamento vienes."

    if detect_open_request(visitor_text) and claimed_resident_name:
        return (
            f"No puedo autorizar la apertura para {claimed_resident_name} todavia. "
            "Acercate a la camara, mira de frente y vuelve a intentarlo."
        )

    if detect_open_request(visitor_text) and claimed_unit:
        return (
            f"No puedo autorizar la apertura para la unidad {claimed_unit} todavia. "
            "Acercate a la camara, mira de frente y vuelve a intentarlo."
        )

    return "Lo siento, no tengo autorización para abrir el portón."


def build_claimed_context_wait_message(resident_context=None):
    resident_context = resident_context or {}
    claimed_resident_name = resident_context.get("claimed_resident_name")
    claimed_unit = resident_context.get("claimed_unit")

    if claimed_resident_name:
        return f"Entendido. Un momento por favor con {claimed_resident_name}."

    if claimed_unit:
        return f"Entendido. Un momento por favor con el departamento {claimed_unit}."

    return "Entendido. Un momento por favor."


def detect_delivery_context(visitor_text):
    normalized_text = normalize_spanish_text(visitor_text)
    return any(keyword in normalized_text for keyword in DELIVERY_KEYWORDS)


def capture_snapshot_and_face():
    snapshot_path, snapshot_error = try_capture_snapshot()
    face_result, face_error = try_face_recognition(snapshot_path)
    return snapshot_path, snapshot_error, face_result, face_error


def capture_fast_entry_snapshot_and_face():
    started_at = time.perf_counter()
    try:
        snapshot_path = capture_snapshot(subtype=VTO_FAST_FACE_SUBTYPE)
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        face_result, face_error = try_face_recognition(
            str(snapshot_path),
            extra_env={"VIGILIA_FACE_ENCODING_DOWNSCALE_FACTOR": FAST_FACE_DOWNSCALE_FACTOR},
        )
        return str(snapshot_path), None, face_result, face_error
    except KeyboardInterrupt:
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        print("[VTO] Snapshot interrupted")
        return None, "snapshot_interrupted", None, "face_recognition_skipped_no_snapshot"
    except Exception as exc:
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        print(f"[VTO] Snapshot failed: {exc}")
        return None, str(exc), None, "face_recognition_skipped_no_snapshot"


def capture_fast_face_entry_match():
    best_snapshot_path = None
    best_snapshot_error = None
    best_face_result = None
    best_face_error = None

    for attempt in range(1, FAST_FACE_ENTRY_ATTEMPTS + 1):
        if attempt > 1:
            print(f"[FAST_FACE] retry attempt={attempt}")
            time.sleep(FAST_FACE_ENTRY_PAUSE_SECONDS)

        snapshot_path, snapshot_error, face_result, face_error = capture_fast_entry_snapshot_and_face()
        if has_trusted_face_match(face_result):
            return snapshot_path, snapshot_error, face_result, face_error

        if best_snapshot_path is None and snapshot_path is not None:
            best_snapshot_path = snapshot_path
            best_snapshot_error = snapshot_error

        if best_face_result is None and face_result is not None:
            best_face_result = face_result
            best_face_error = face_error
            continue

        current_distance = face_result_distance(best_face_result)
        retry_distance = face_result_distance(face_result)
        if retry_distance is not None and (current_distance is None or retry_distance < current_distance):
            best_snapshot_path = snapshot_path
            best_snapshot_error = snapshot_error
            best_face_result = face_result
            best_face_error = face_error

        if best_face_result is None:
            best_face_error = combine_errors(best_face_error, face_error)
        if best_snapshot_error is None:
            best_snapshot_error = snapshot_error

    return best_snapshot_path, best_snapshot_error, best_face_result, best_face_error


def build_decision_prompt(visitor_text, face_result):
    if face_result:
        facial_context = (
            f"matched={face_result.get('matched')} | "
            f"name={face_result.get('matched_person_name') or 'unknown'} | "
            f"confidence={face_confidence(face_result) or 0.0:.4f}"
        )
    else:
        facial_context = "matched=unknown | name=unknown | confidence=0.0000"

    return (
        "Return exactly one token: OPEN, HOLA, or ERROR.\n"
        "Do not repeat the prompt.\n"
        "Do not write sentences.\n"
        "If the visitor asks to open the gate or door, return OPEN.\n"
        "If the visitor is only greeting or making a non-access remark, return HOLA.\n"
        "If the audio is unclear or the request is ambiguous, return ERROR.\n"
        "Do not grant access based only on FACIAL_CONTEXT.\n"
        "Examples:\n"
        "VISITOR_SPEECH: hola buenas tardes\nFACIAL_CONTEXT: matched=true | name=Alvaro | confidence=0.9900\nANSWER: HOLA\n"
        "VISITOR_SPEECH: abre el porton por favor\nFACIAL_CONTEXT: matched=true | name=Alvaro | confidence=0.9900\nANSWER: OPEN\n"
        "VISITOR_SPEECH: no se entiende\nFACIAL_CONTEXT: matched=false | name=unknown | confidence=0.0000\nANSWER: ERROR\n"
        f"VISITOR_SPEECH: {visitor_text}\n"
        f"FACIAL_CONTEXT: {facial_context}\n"
        "ANSWER:"
    )


def query_access_model(visitor_text, face_result):
    started_at = time.perf_counter()
    prompt = build_decision_prompt(visitor_text=visitor_text, face_result=face_result)
    print(f"[MODEL] prompt:\n{prompt}")

    try:
        result = subprocess.run(
            ["ollama", "run", DECISION_MODEL_NAME, prompt],
            capture_output=True,
            text=True,
            timeout=MODEL_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        print(
            "[MODEL] timeout "
            f"seconds={MODEL_TIMEOUT_SECONDS:.3f} "
            f"model={DECISION_MODEL_NAME}"
        )
        print(f"[TIMING] model_seconds={time.perf_counter() - started_at:.3f}")
        raise RuntimeError("ollama_query_timeout") from exc

    if result.returncode != 0:
        stderr_text = result.stderr.strip()
        print(f"[MODEL] stderr: {stderr_text}")
        print(f"[TIMING] model_seconds={time.perf_counter() - started_at:.3f}")
        raise RuntimeError("ollama_query_failed")

    response_text = result.stdout.strip()
    print(f"[MODEL] response: {response_text}")
    print(f"[TIMING] model_seconds={time.perf_counter() - started_at:.3f}")
    return response_text


def build_spoken_response_fallback(visitor_text, decision, face_error, resident_context=None):
    resident_context = resident_context or {}
    decision = decision or {}

    if decision.get("should_open"):
        return "Acceso concedido. Abriendo el portón ahora."

    if not normalize_spanish_text(visitor_text):
        return "No pude escucharte bien. Por favor, pulsa el botón de nuevo."

    if detect_delivery_context(visitor_text):
        return "No puedo autorizar la entrada. Por favor deje el paquete en conserjería."

    if (
        has_claimed_resident_context(resident_context)
        and not detect_open_request(visitor_text)
    ):
        return build_claimed_context_wait_message(resident_context)

    if is_greeting_only_text(visitor_text):
        return "Hola. Dime a qué residente o departamento vienes."

    return build_denial_message(
        visitor_text,
        face_error,
        resident_context=resident_context,
    )


def normalize_spoken_response(response_text):
    if response_text is None:
        return None

    normalized = " ".join(response_text.strip().split())
    normalized = normalized.strip("\"' ")

    if not normalized:
        return None

    if len(normalized) > 180:
        return None

    if len(normalized.split()) > 28:
        return None

    return normalized


def should_skip_spoken_response_model(visitor_text, decision, resident_context=None):
    resident_context = resident_context or {}
    decision = decision or {}

    if decision.get("should_open"):
        return False

    if not normalize_spanish_text(visitor_text):
        return True

    if detect_delivery_context(visitor_text):
        return True

    if is_greeting_only_text(visitor_text):
        return True

    if detect_open_request(visitor_text) and not has_claimed_resident_context(resident_context):
        return True

    if (
        has_claimed_resident_context(resident_context)
        and not detect_open_request(visitor_text)
    ):
        return True

    return False


def build_spoken_response_prompt(visitor_text, decision, resident_context=None, face_error=None):
    resident_context = resident_context or {}
    fallback_response = build_spoken_response_fallback(
        visitor_text=visitor_text,
        decision=decision,
        face_error=face_error,
        resident_context=resident_context,
    )

    return (
        "Redacta una sola frase breve en espanol para un citofono de condominio.\n"
        "Devuelve solo la frase final, sin comillas ni explicaciones.\n"
        "Maximo 18 palabras.\n"
        "No inventes acciones que el sistema no hara.\n"
        "Si ACCESS_GRANTED=true, confirma apertura inmediata.\n"
        "Si DELIVERY_CONTEXT=true y ACCESS_GRANTED=false, indica dejar el paquete en conserjeria.\n"
        "Si OPEN_REQUEST=true y CLAIMED_CONTEXT_PRESENT=false, pide a que residente o departamento viene.\n"
        "Si GREETING_ONLY=true y ACCESS_GRANTED=false, pide a que residente o departamento viene.\n"
        "Si AUDIO_UNCLEAR=true, pide repetir.\n"
        "Si ACCESS_GRANTED=false, no digas que abriras el porton.\n"
        f"VISITOR_SPEECH: {visitor_text or 'unknown'}\n"
        f"ACCESS_GRANTED: {str(bool(decision.get('should_open'))).lower()}\n"
        f"OPEN_REQUEST: {str(detect_open_request(visitor_text)).lower()}\n"
        f"GREETING_ONLY: {str(is_greeting_only_text(visitor_text)).lower()}\n"
        f"DELIVERY_CONTEXT: {str(detect_delivery_context(visitor_text)).lower()}\n"
        f"AUDIO_UNCLEAR: {str(not normalize_spanish_text(visitor_text)).lower()}\n"
        f"CLAIMED_CONTEXT_PRESENT: {str(has_claimed_resident_context(resident_context)).lower()}\n"
        f"CLAIMED_RESIDENT_NAME: {resident_context.get('claimed_resident_name') or 'unknown'}\n"
        f"CLAIMED_UNIT: {resident_context.get('claimed_unit') or 'unknown'}\n"
        f"DECISION_REASON: {decision.get('reason') or 'unknown'}\n"
        f"SAFE_FALLBACK: {fallback_response}\n"
        "ANSWER:"
    )


def query_spoken_response_model(visitor_text, decision, resident_context=None, face_error=None):
    started_at = time.perf_counter()
    prompt = build_spoken_response_prompt(
        visitor_text=visitor_text,
        decision=decision,
        resident_context=resident_context,
        face_error=face_error,
    )
    print(f"[RESPONSE_MODEL] prompt:\n{prompt}")

    try:
        result = subprocess.run(
            ["ollama", "run", SPOKEN_RESPONSE_MODEL_NAME, prompt],
            capture_output=True,
            text=True,
            timeout=SPOKEN_RESPONSE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        print(
            "[RESPONSE_MODEL] timeout "
            f"seconds={SPOKEN_RESPONSE_TIMEOUT_SECONDS:.3f} "
            f"model={SPOKEN_RESPONSE_MODEL_NAME}"
        )
        print(f"[TIMING] response_model_seconds={time.perf_counter() - started_at:.3f}")
        raise RuntimeError("spoken_response_query_timeout") from exc

    if result.returncode != 0:
        stderr_text = result.stderr.strip()
        print(f"[RESPONSE_MODEL] stderr: {stderr_text}")
        print(f"[TIMING] response_model_seconds={time.perf_counter() - started_at:.3f}")
        raise RuntimeError("spoken_response_query_failed")

    response_text = result.stdout.strip()
    print(f"[RESPONSE_MODEL] response: {response_text}")
    print(f"[TIMING] response_model_seconds={time.perf_counter() - started_at:.3f}")
    return response_text


def build_spoken_response(visitor_text, decision, face_error, resident_context=None):
    resident_context = resident_context or {}
    fallback_response = build_spoken_response_fallback(
        visitor_text=visitor_text,
        decision=decision,
        face_error=face_error,
        resident_context=resident_context,
    )

    if should_skip_spoken_response_model(
        visitor_text=visitor_text,
        decision=decision,
        resident_context=resident_context,
    ):
        return fallback_response

    try:
        response_text = query_spoken_response_model(
            visitor_text=visitor_text,
            decision=decision,
            resident_context=resident_context,
            face_error=face_error,
        )
    except Exception as exc:
        print(f"[RESPONSE_MODEL] fallback error={exc}")
        return fallback_response

    normalized_response = normalize_spoken_response(response_text)
    if normalized_response is None:
        print("[RESPONSE_MODEL] invalid_response fallback=true")
        return fallback_response

    return normalized_response


def send_inference_request(action, payload, timeout_seconds):
    if os.environ.get("VIGILIA_DISABLE_INFERENCE_SERVICE") == "1":
        return None

    return send_service_request(
        action=action,
        payload=payload,
        timeout_seconds=timeout_seconds,
        socket_path=INFERENCE_SOCKET_PATH,
    )


def normalize_model_token(model_response):
    if model_response is None:
        return None

    normalized_response = model_response.strip().upper()
    if normalized_response in VALID_MODEL_TOKENS:
        return normalized_response
    return None


def normalize_spanish_text(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def fuzzy_contains_phrase(text, phrase, threshold=VOICE_OPEN_FUZZY_THRESHOLD):
    text_words = text.split()
    phrase_words = phrase.split()

    if not text_words or len(text_words) < len(phrase_words):
        return False

    window_size = len(phrase_words)
    for index in range(len(text_words) - window_size + 1):
        window = " ".join(text_words[index:index + window_size])
        similarity = SequenceMatcher(None, window, phrase).ratio()
        if similarity >= threshold:
            return True
    return False


def fuzzy_matches_keyword(text, keywords, threshold=VOICE_OPEN_KEYWORD_FUZZY_THRESHOLD):
    text_words = text.split()
    if not text_words:
        return False

    for word in text_words:
        for keyword in keywords:
            if SequenceMatcher(None, word, keyword).ratio() >= threshold:
                return True
    return False


def token_overlap_open_phrase(text, phrases):
    text_words = set(text.split())
    if not text_words:
        return False

    for phrase in phrases:
        phrase_words = set(phrase.split())
        if len(phrase_words & text_words) >= 3:
            return True
    return False


def detect_open_request(visitor_text):
    normalized_text = normalize_spanish_text(visitor_text)

    if any(keyword in normalized_text for keyword in VOICE_OPEN_KEYWORDS):
        return True

    if fuzzy_matches_keyword(normalized_text, VOICE_OPEN_KEYWORDS):
        return True

    known_access_phrases = get_enabled_access_phrases()
    if normalized_text in known_access_phrases:
        return True

    if token_overlap_open_phrase(normalized_text, known_access_phrases):
        return True

    return any(
        fuzzy_contains_phrase(normalized_text, phrase)
        for phrase in VOICE_OPEN_PHRASES
    )


def is_greeting_only_text(visitor_text):
    normalized_text = normalize_spanish_text(visitor_text)
    if not normalized_text:
        return False

    if normalized_text in GREETING_ONLY_PHRASES:
        return True

    return any(
        fuzzy_contains_phrase(normalized_text, phrase, threshold=0.84)
        for phrase in GREETING_ONLY_PHRASES
    )


def normalize_unit_text(unit_text):
    return normalize_spanish_text(unit_text or "")


def resident_name_candidates(resident):
    candidates = []
    for field_name in ("preferred_name", "full_name"):
        normalized_value = normalize_spanish_text(resident.get(field_name) or "")
        if normalized_value and normalized_value not in candidates:
            candidates.append(normalized_value)
    return candidates


def resolve_claimed_resident_context(
    visitor_text,
    residents=None,
    resident_aliases=None,
):
    normalized_text = normalize_spanish_text(visitor_text)
    if not normalized_text:
        return {
            "claimed_resident_name": None,
            "claimed_unit": None,
            "resolved_resident_id": None,
        }

    residents = residents if residents is not None else get_residents()
    resident_aliases = (
        resident_aliases if resident_aliases is not None else get_resident_aliases()
    )

    residents_by_id = {resident["id"]: resident for resident in residents}
    residents_by_unit = {}
    for resident in residents:
        normalized_unit = normalize_unit_text(resident.get("apartment_unit"))
        if not normalized_unit:
            continue
        residents_by_unit.setdefault(normalized_unit, []).append(resident["id"])

    matched_name_ids = []
    matched_unit_ids = []

    padded_text = f" {normalized_text} "
    for alias in resident_aliases:
        normalized_alias = alias.get("normalized_alias")
        if not normalized_alias:
            continue
        if f" {normalized_alias} " not in padded_text:
            continue
        resident_id = alias["resident_id"]
        alias_type = alias.get("alias_type") or "name"
        if alias_type == "unit":
            matched_unit_ids.append(resident_id)
        else:
            matched_name_ids.append(resident_id)

    if not matched_name_ids:
        for resident in residents:
            for normalized_candidate in resident_name_candidates(resident):
                if f" {normalized_candidate} " in padded_text:
                    matched_name_ids.append(resident["id"])
                    break

    extracted_units = []
    for pattern in CLAIMED_UNIT_PATTERNS:
        for match in re.finditer(pattern, normalized_text):
            extracted_units.append(normalize_unit_text(match.group(1)))

    explicit_unit_ids = []
    for extracted_unit in extracted_units:
        explicit_unit_ids.extend(residents_by_unit.get(extracted_unit, []))

    unique_name_ids = sorted(set(matched_name_ids))
    unique_unit_ids = sorted(set(matched_unit_ids + explicit_unit_ids))
    all_candidate_ids = sorted(set(unique_name_ids + unique_unit_ids))

    claimed_resident_name = None
    if len(unique_name_ids) == 1:
        claimed_resident_name = residents_by_id[unique_name_ids[0]]["full_name"]

    claimed_unit = None
    if extracted_units:
        claimed_unit = extracted_units[0]
    elif len(unique_unit_ids) == 1:
        claimed_unit = residents_by_id[unique_unit_ids[0]].get("apartment_unit")
        claimed_unit = normalize_unit_text(claimed_unit)

    resolved_resident_id = None
    if len(all_candidate_ids) == 1:
        resolved_resident_id = all_candidate_ids[0]

    if resolved_resident_id and claimed_resident_name is None:
        claimed_resident_name = residents_by_id[resolved_resident_id]["full_name"]

    if resolved_resident_id and claimed_unit is None:
        claimed_unit = normalize_unit_text(
            residents_by_id[resolved_resident_id].get("apartment_unit")
        )

    return {
        "claimed_resident_name": claimed_resident_name,
        "claimed_unit": claimed_unit,
        "resolved_resident_id": resolved_resident_id,
    }


def classify_face_match_band(face_result):
    if not face_result:
        return "unknown"
    distance = face_result.get("distance")
    tolerance = face_result.get("tolerance")
    if distance is None or tolerance is None:
        if not face_result.get("matched"):
            return "low"
        return "unknown"

    distance = float(distance)
    tolerance = float(tolerance)
    if distance <= tolerance:
        return "trusted"
    if distance <= tolerance + FACE_BORDERLINE_DISTANCE_MARGIN:
        return "borderline"
    return "low"


def has_trusted_face_match(face_result):
    return classify_face_match_band(face_result) == "trusted"


def has_known_resident_extended_face_match(face_result):
    if not face_result:
        return False
    person = face_result.get("person") or {}
    if person.get("resident_id") is None:
        return False

    distance = face_result.get("distance")
    tolerance = face_result.get("tolerance")
    if distance is None or tolerance is None:
        return False

    return float(distance) <= float(tolerance) + FACE_KNOWN_RESIDENT_EXTENDED_MARGIN


def face_match_is_access_enabled(face_result):
    if not face_result:
        return False
    person = face_result.get("person") or {}
    return bool(person.get("access_enabled", 1))


def face_match_is_known_resident(face_result):
    if not face_result:
        return False
    person = face_result.get("person") or {}
    return person.get("resident_id") is not None


def face_result_resident_matches_claim(face_result, resident_context):
    if not face_result or not resident_context:
        return False
    person = face_result.get("person") or {}
    claimed_resident_id = resident_context.get("resolved_resident_id")
    if claimed_resident_id is None:
        return False
    return person.get("resident_id") == claimed_resident_id


def has_claimed_resident_context(resident_context):
    resident_context = resident_context or {}
    return bool(
        resident_context.get("claimed_resident_name")
        or resident_context.get("claimed_unit")
        or resident_context.get("resolved_resident_id")
    )


def has_meaningful_speech(visitor_text):
    normalized_text = normalize_spanish_text(visitor_text)
    if not normalized_text:
        return False

    words = normalized_text.split()
    if len(words) >= 3:
        return True

    return len(normalized_text) >= 12


def is_unintelligible_transcript(visitor_text):
    raw_text = (visitor_text or "").strip()
    if not raw_text:
        return True

    normalized_text = normalize_spanish_text(raw_text)
    if not normalized_text:
        return True

    allowed_chars = sum(
        1 for char in raw_text
        if char.isalnum() or char.isspace() or char in ".,;:!?-_'\""
    )
    allowed_ratio = allowed_chars / max(len(raw_text), 1)

    if allowed_ratio < 0.7:
        return True

    alnum_count = sum(1 for char in normalized_text if char.isalnum())
    if alnum_count < 2:
        return True

    if len(normalized_text.split()) == 1 and len(normalized_text) <= 2:
        return True

    if (
        len(normalized_text.split()) <= 2
        and not detect_open_request(raw_text)
        and not detect_delivery_context(raw_text)
        and not is_greeting_only_text(raw_text)
        and not has_claimed_resident_context(resolve_claimed_resident_context(raw_text))
    ):
        return True

    return False


def should_skip_decision_model(visitor_text, resident_context=None):
    resident_context = resident_context or {}
    normalized_text = normalize_spanish_text(visitor_text)

    if not normalized_text:
        return True

    if detect_open_request(visitor_text):
        return False

    if detect_delivery_context(visitor_text):
        return True

    if is_greeting_only_text(visitor_text):
        return True

    if has_claimed_resident_context(resident_context):
        return True

    return False


def should_request_followup_turn(visitor_text, resident_context=None, decision=None):
    resident_context = resident_context or {}
    decision = decision or {}

    if not ENABLE_LOCAL_FOLLOWUP_CAPTURE:
        return False

    if not DISABLE_VTO_SNAPSHOT:
        return False

    if detect_delivery_context(visitor_text):
        return False

    if has_claimed_resident_context(resident_context):
        return False

    if decision.get("should_open"):
        return False

    if is_greeting_only_text(visitor_text):
        return True

    return decision.get("reason") == "non_open_request_resolved_without_model"


def combine_visitor_turns(first_text, second_text):
    first_text = (first_text or "").strip()
    second_text = (second_text or "").strip()

    if not first_text:
        return second_text
    if not second_text:
        return first_text

    return f"{first_text}. {second_text}"


def should_auto_open_known_resident_on_button_press(visitor_text, face_result):
    if not (
        has_trusted_face_match(face_result)
        or has_known_resident_extended_face_match(face_result)
    ):
        return False
    if not face_match_is_access_enabled(face_result):
        return False
    if not face_match_is_known_resident(face_result):
        return False

    normalized_text = normalize_spanish_text(visitor_text)
    if not normalized_text:
        return True

    return is_greeting_only_text(normalized_text)


def resolve_model_unavailable_fallback(visitor_text, face_result, resident_context=None):
    return {
        "should_open": False,
        "source": "model_response",
        "reason": "model_unavailable_fallback",
    }


def resolve_access_decision(visitor_text, face_result, model_response, resident_context=None):
    voice_requests_open = detect_open_request(visitor_text)
    face_match_band = classify_face_match_band(face_result)
    trusted_face_match = has_trusted_face_match(face_result)
    access_enabled_face_match = face_match_is_access_enabled(face_result)
    known_resident_face_match = face_match_is_known_resident(face_result)
    normalized_model_token = normalize_model_token(model_response)
    resident_context = resident_context or {}
    resident_context_match = face_result_resident_matches_claim(
        face_result=face_result,
        resident_context=resident_context,
    )
    has_resident_context = has_claimed_resident_context(resident_context)

    if should_auto_open_known_resident_on_button_press(visitor_text, face_result):
        return {
            "should_open": True,
            "source": "resident_context",
            "reason": "known_resident_button_press_face_match",
        }

    if (
        voice_requests_open
        and trusted_face_match
        and access_enabled_face_match
        and resident_context_match
    ):
        return {
            "should_open": True,
            "source": "resident_context",
            "reason": (
                "voice_requested_open_and_claimed_resident_matches_trusted_face"
            ),
        }

    if (
        voice_requests_open
        and trusted_face_match
        and access_enabled_face_match
        and known_resident_face_match
        and not has_resident_context
    ):
        return {
            "should_open": True,
            "source": "resident_context",
            "reason": "voice_requested_open_and_known_resident_face_match",
        }

    if (
        voice_requests_open
        and face_match_band == "borderline"
        and access_enabled_face_match
        and known_resident_face_match
        and not has_resident_context
    ):
        return {
            "should_open": True,
            "source": "resident_context",
            "reason": "voice_requested_open_and_known_resident_borderline_face_match",
        }

    if (
        voice_requests_open
        and has_known_resident_extended_face_match(face_result)
        and access_enabled_face_match
        and known_resident_face_match
        and not has_resident_context
    ):
        return {
            "should_open": True,
            "source": "resident_context",
            "reason": "voice_requested_open_and_known_resident_extended_face_match",
        }

    if (
        voice_requests_open
        and resident_context_match
        and face_match_band == "borderline"
        and access_enabled_face_match
    ):
        return {
            "should_open": True,
            "source": "resident_context",
            "reason": (
                "voice_requested_open_and_claimed_resident_matches_borderline_face"
            ),
        }

    if voice_requests_open and trusted_face_match and not access_enabled_face_match:
        return {
            "should_open": False,
            "source": "hybrid_policy",
            "reason": "voice_requested_open_but_face_match_within_tolerance_not_whitelisted",
        }

    if voice_requests_open and trusted_face_match and access_enabled_face_match:
        return {
            "should_open": False,
            "source": "resident_context",
            "reason": "voice_requested_open_but_claimed_resident_does_not_match_face",
        }

    if voice_requests_open and normalized_model_token == "OPEN":
        return {
            "should_open": False,
            "source": "resident_context",
            "reason": "voice_requested_open_but_model_open_without_resident_match",
        }

    if voice_requests_open and face_match_band == "borderline":
        return {
            "should_open": False,
            "source": "hybrid_policy",
            "reason": "voice_requested_open_but_face_match_borderline",
        }

    if normalized_model_token == "OPEN":
        return {
            "should_open": True,
            "source": "model_response",
            "reason": "model_returned_open",
        }

    if normalized_model_token == "HOLA":
        return {
            "should_open": False,
            "source": "model_response",
            "reason": "model_returned_hola",
        }

    if normalized_model_token == "ERROR":
        return {
            "should_open": False,
            "source": "model_response",
            "reason": "model_returned_error",
        }

    if voice_requests_open and not trusted_face_match:
        return {
            "should_open": False,
            "source": "hybrid_policy",
            "reason": "voice_requested_open_but_face_match_not_within_tolerance",
        }

    if model_response and normalized_model_token is None:
        return {
            "should_open": False,
            "source": "model_response",
            "reason": "model_response_invalid_token",
        }

    return {
        "should_open": False,
        "source": "model_response",
        "reason": "model_did_not_return_open",
    }

def procesar_audio(ruta_audio, response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH):
    ensure_runtime_directories()
    # Cargar Whisper (oído)
    if not Path(ruta_audio).exists():
        raise FileNotFoundError(f"Audio file not found: {ruta_audio}")

    created_at = datetime.now().isoformat(timespec="seconds")
    started_at = time.perf_counter()
    snapshot_path, snapshot_error = try_capture_snapshot()
    transcription_error = None
    try:
        result = transcribe_audio(ruta_audio)
    except Exception as exc:
        transcription_error = str(exc)
        print(f"[AUDIO] transcription_failed error={transcription_error}")
        result = {"text": ""}
    face_result, face_error = try_face_recognition(snapshot_path)

    print(f"[TIMING] pre_decision_seconds={time.perf_counter() - started_at:.3f}")
    texto_vecino = result["text"].lower().strip()
    if is_unintelligible_transcript(texto_vecino):
        texto_vecino = ""
    resident_context = resolve_claimed_resident_context(texto_vecino)
    followup_error = None
    pre_model_decision = resolve_access_decision(
        visitor_text=texto_vecino,
        face_result=face_result,
        model_response=None,
        resident_context=resident_context,
    )
    
    if not texto_vecino:
        gate_opened = False
        if pre_model_decision["should_open"]:
            print(
                "[DECISION] "
                f"source={pre_model_decision['source']} "
                f"reason={pre_model_decision['reason']} "
                f"should_open={pre_model_decision['should_open']} "
                "stage=empty_transcript"
            )
            gate_opened = ejecutar_porton(response_audio_path=response_audio_path)
        else:
            decir(
                "No pude escucharte bien. Por favor, pulsa el botón de nuevo.",
                response_audio_path=response_audio_path,
            )
        insert_access_event(
            created_at=created_at,
            audio_path=ruta_audio,
            transcript=texto_vecino,
            model_response=None,
            gate_opened=gate_opened,
            snapshot_path=snapshot_path,
            error_message=combine_errors(snapshot_error, face_error, transcription_error),
            face_match_name=face_result.get("matched_person_name") if face_result else None,
            face_match_confidence=face_confidence(face_result),
            face_observation_id=face_result.get("observation_id") if face_result else None,
            decision_source=(
                pre_model_decision["source"] if pre_model_decision["should_open"] else "speech_capture"
            ),
            decision_reason=(
                pre_model_decision["reason"] if pre_model_decision["should_open"] else "empty_transcript"
            ),
            claimed_resident_name=resident_context["claimed_resident_name"],
            claimed_unit=resident_context["claimed_unit"],
            resolved_resident_id=resident_context["resolved_resident_id"],
        )
        return

    if should_skip_decision_model(
        visitor_text=texto_vecino,
        resident_context=resident_context,
    ):
        decision = {
            "should_open": False,
            "source": "local_policy",
            "reason": "non_open_request_resolved_without_model",
        }
        spoken_response = build_spoken_response(
            visitor_text=texto_vecino,
            decision=decision,
            face_error=face_error,
            resident_context=resident_context,
        )

        if should_request_followup_turn(
            visitor_text=texto_vecino,
            resident_context=resident_context,
            decision=decision,
        ):
            print(
                "[DECISION] "
                f"source={decision['source']} "
                f"reason={decision['reason']} "
                f"should_open={decision['should_open']} "
                "stage=followup_prompt"
            )
            decir(spoken_response, response_audio_path=response_audio_path)

            followup_audio_path = (
                Path(response_audio_path).with_suffix("").with_name("vigilia_followup.wav")
            )
            try:
                capture_local_followup_audio(followup_audio_path)
                followup_result = transcribe_audio(str(followup_audio_path))
                followup_text = followup_result["text"].lower().strip()
                if followup_text:
                    print(f"[FOLLOWUP] visitor said: {followup_text}")
                    texto_vecino = combine_visitor_turns(texto_vecino, followup_text)
                    resident_context = resolve_claimed_resident_context(texto_vecino)
                    pre_model_decision = resolve_access_decision(
                        visitor_text=texto_vecino,
                        face_result=face_result,
                        model_response=None,
                        resident_context=resident_context,
                    )
                else:
                    followup_error = "followup_empty_transcript"
            except Exception as exc:
                followup_error = str(exc)
                print(f"[FOLLOWUP] capture_failed error={followup_error}")
            finally:
                followup_audio_path.unlink(missing_ok=True)

            if followup_error:
                decir(
                    "No pude escucharte bien. Por favor, pulsa el botón de nuevo.",
                    response_audio_path=response_audio_path,
                )
                insert_access_event(
                    created_at=created_at,
                    audio_path=ruta_audio,
                    transcript=texto_vecino,
                    model_response=None,
                    gate_opened=False,
                    snapshot_path=snapshot_path,
                    error_message=combine_errors(snapshot_error, face_error, followup_error),
                    face_match_name=face_result.get("matched_person_name") if face_result else None,
                    face_match_confidence=face_confidence(face_result),
                    face_observation_id=face_result.get("observation_id") if face_result else None,
                    decision_source="speech_capture",
                    decision_reason="followup_empty_transcript",
                    claimed_resident_name=resident_context["claimed_resident_name"],
                    claimed_unit=resident_context["claimed_unit"],
                    resolved_resident_id=resident_context["resolved_resident_id"],
                )
                return

            if should_skip_decision_model(
                visitor_text=texto_vecino,
                resident_context=resident_context,
            ):
                decision = {
                    "should_open": False,
                    "source": "local_policy",
                    "reason": "non_open_request_resolved_without_model_followup",
                }
                print(
                    "[DECISION] "
                    f"source={decision['source']} "
                    f"reason={decision['reason']} "
                    f"should_open={decision['should_open']} "
                    "stage=followup_resolved"
                )

                decir(
                    build_spoken_response(
                        visitor_text=texto_vecino,
                        decision=decision,
                        face_error=face_error,
                        resident_context=resident_context,
                    ),
                    response_audio_path=response_audio_path,
                )

                insert_access_event(
                    created_at=created_at,
                    audio_path=ruta_audio,
                    transcript=texto_vecino,
                    model_response=None,
                    gate_opened=False,
                    snapshot_path=snapshot_path,
                    error_message=combine_errors(snapshot_error, face_error),
                    face_match_name=face_result.get("matched_person_name") if face_result else None,
                    face_match_confidence=face_confidence(face_result),
                    face_observation_id=face_result.get("observation_id") if face_result else None,
                    decision_source=decision["source"],
                    decision_reason=decision["reason"],
                    claimed_resident_name=resident_context["claimed_resident_name"],
                    claimed_unit=resident_context["claimed_unit"],
                    resolved_resident_id=resident_context["resolved_resident_id"],
                )
                return
        else:
            print(
                "[DECISION] "
                f"source={decision['source']} "
                f"reason={decision['reason']} "
                f"should_open={decision['should_open']} "
                "stage=pre_model"
            )

            decir(
                spoken_response,
                response_audio_path=response_audio_path,
            )

            insert_access_event(
                created_at=created_at,
                audio_path=ruta_audio,
                transcript=texto_vecino,
                model_response=None,
                gate_opened=False,
                snapshot_path=snapshot_path,
                error_message=combine_errors(snapshot_error, face_error),
                face_match_name=face_result.get("matched_person_name") if face_result else None,
                face_match_confidence=face_confidence(face_result),
                face_observation_id=face_result.get("observation_id") if face_result else None,
                decision_source=decision["source"],
                decision_reason=decision["reason"],
                claimed_resident_name=resident_context["claimed_resident_name"],
                claimed_unit=resident_context["claimed_unit"],
                resolved_resident_id=resident_context["resolved_resident_id"],
            )
            return

    print(f"El vecino dijo: {texto_vecino}")
    if any(resident_context.values()):
        print(
            "[RESIDENT] "
            f"claimed_name={resident_context['claimed_resident_name']} "
            f"claimed_unit={resident_context['claimed_unit']} "
            f"resolved_resident_id={resident_context['resolved_resident_id']}"
        )

    face_result, merged_face_error, retry_snapshot_path = retry_face_recognition_for_open_request(
        visitor_text=texto_vecino,
        face_result=face_result,
        face_error=face_error,
    )
    if merged_face_error is not None:
        face_error = merged_face_error
    if retry_snapshot_path is not None:
        snapshot_path = retry_snapshot_path

    pre_model_decision = resolve_access_decision(
        visitor_text=texto_vecino,
        face_result=face_result,
        model_response=None,
        resident_context=resident_context,
    )

    if pre_model_decision["should_open"] or pre_model_decision["source"] == "hybrid_policy":
        print(
            "[DECISION] "
            f"source={pre_model_decision['source']} "
            f"reason={pre_model_decision['reason']} "
            f"should_open={pre_model_decision['should_open']} "
            "stage=pre_model"
        )

        gate_opened = False
        if pre_model_decision["should_open"]:
            gate_opened = ejecutar_porton(
                response_audio_path=response_audio_path,
                success_message=build_spoken_response(
                    visitor_text=texto_vecino,
                    decision=pre_model_decision,
                    face_error=face_error,
                    resident_context=resident_context,
                ),
            )
        else:
            decir(
                build_spoken_response(
                    visitor_text=texto_vecino,
                    decision=pre_model_decision,
                    face_error=face_error,
                    resident_context=resident_context,
                ),
                response_audio_path=response_audio_path,
            )

        insert_access_event(
            created_at=created_at,
            audio_path=ruta_audio,
            transcript=texto_vecino,
            model_response=None,
            gate_opened=gate_opened,
            snapshot_path=snapshot_path,
            error_message=combine_errors(snapshot_error, face_error),
            face_match_name=face_result.get("matched_person_name") if face_result else None,
            face_match_confidence=face_confidence(face_result),
            face_observation_id=face_result.get("observation_id") if face_result else None,
            decision_source=pre_model_decision["source"],
            decision_reason=pre_model_decision["reason"],
            claimed_resident_name=resident_context["claimed_resident_name"],
            claimed_unit=resident_context["claimed_unit"],
            resolved_resident_id=resident_context["resolved_resident_id"],
        )
        return
    
    # Consultar a Ollama (cerebro)
    try:
        respuesta_ia = query_access_model(
            visitor_text=texto_vecino,
            face_result=face_result,
        )
        decision = resolve_access_decision(
            visitor_text=texto_vecino,
            face_result=face_result,
            model_response=respuesta_ia,
            resident_context=resident_context,
        )
        gate_opened = False

        print(
            "[DECISION] "
            f"source={decision['source']} "
            f"reason={decision['reason']} "
            f"should_open={decision['should_open']}"
        )

        if decision["should_open"]:
            gate_opened = ejecutar_porton(
                response_audio_path=response_audio_path,
                success_message=build_spoken_response(
                    visitor_text=texto_vecino,
                    decision=decision,
                    face_error=face_error,
                    resident_context=resident_context,
                ),
            )
        else:
            decir(
                build_spoken_response(
                    visitor_text=texto_vecino,
                    decision=decision,
                    face_error=face_error,
                    resident_context=resident_context,
                ),
                response_audio_path=response_audio_path,
            )

        insert_access_event(
            created_at=created_at,
            audio_path=ruta_audio,
            transcript=texto_vecino,
            model_response=respuesta_ia,
            gate_opened=gate_opened,
            snapshot_path=snapshot_path,
            error_message=combine_errors(snapshot_error, face_error),
            face_match_name=face_result.get("matched_person_name") if face_result else None,
            face_match_confidence=face_confidence(face_result),
            face_observation_id=face_result.get("observation_id") if face_result else None,
            decision_source=decision["source"],
            decision_reason=decision["reason"],
            claimed_resident_name=resident_context["claimed_resident_name"],
            claimed_unit=resident_context["claimed_unit"],
            resolved_resident_id=resident_context["resolved_resident_id"],
        )
    except Exception as exc:
        print(f"[MODEL] fallback error={exc}")
        decision = resolve_model_unavailable_fallback(
            visitor_text=texto_vecino,
            face_result=face_result,
            resident_context=resident_context,
        )
        print(
            "[DECISION] "
            f"source={decision['source']} "
            f"reason={decision['reason']} "
            f"should_open={decision['should_open']} "
            "stage=model_fallback"
        )

        gate_opened = False
        if decision["should_open"]:
            gate_opened = ejecutar_porton(
                response_audio_path=response_audio_path,
                success_message=build_spoken_response(
                    visitor_text=texto_vecino,
                    decision=decision,
                    face_error=face_error,
                    resident_context=resident_context,
                ),
            )
        else:
            decir(
                build_spoken_response(
                    visitor_text=texto_vecino,
                    decision=decision,
                    face_error=face_error,
                    resident_context=resident_context,
                ),
                response_audio_path=response_audio_path,
            )

        insert_access_event(
            created_at=created_at,
            audio_path=ruta_audio,
            transcript=texto_vecino,
            model_response=None,
            gate_opened=gate_opened,
            snapshot_path=snapshot_path,
            error_message=combine_errors(
                snapshot_error,
                face_error,
                str(exc),
            ),
            face_match_name=face_result.get("matched_person_name") if face_result else None,
            face_match_confidence=face_confidence(face_result),
            face_observation_id=face_result.get("observation_id") if face_result else None,
            decision_source=decision["source"],
            decision_reason=decision["reason"],
            claimed_resident_name=resident_context["claimed_resident_name"],
            claimed_unit=resident_context["claimed_unit"],
            resolved_resident_id=resident_context["resolved_resident_id"],
        )


def process_fast_face_entry(response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH):
    ensure_runtime_directories()

    created_at = datetime.now().isoformat(timespec="seconds")
    snapshot_path, snapshot_error, face_result, face_error = capture_fast_face_entry_match()
    decision = resolve_access_decision(
        visitor_text="",
        face_result=face_result,
        model_response=None,
        resident_context={},
    )

    gate_opened = False
    if decision["should_open"]:
        print(
            "[DECISION] "
            f"source={decision['source']} "
            f"reason={decision['reason']} "
            f"should_open={decision['should_open']} "
            "stage=fast_face_entry"
        )
        gate_opened = ejecutar_porton(
            response_audio_path=response_audio_path,
            speak_response=False,
        )
    else:
        print(
            "[DECISION] "
            f"source={decision['source']} "
            f"reason={decision['reason']} "
            f"should_open={decision['should_open']} "
            "stage=fast_face_entry_continue"
        )

    insert_access_event(
        created_at=created_at,
        audio_path=None,
        transcript="",
        model_response=None,
        gate_opened=gate_opened,
        snapshot_path=snapshot_path,
        error_message=combine_errors(snapshot_error, face_error),
        face_match_name=face_result.get("matched_person_name") if face_result else None,
        face_match_confidence=face_confidence(face_result),
        face_observation_id=face_result.get("observation_id") if face_result else None,
        decision_source=decision["source"],
        decision_reason=(
            decision["reason"] if gate_opened else "fast_face_entry_no_match"
        ),
        claimed_resident_name=None,
        claimed_unit=None,
        resolved_resident_id=None,
    )

    return gate_opened


def transcribe_audio(ruta_audio):
    prepared_audio_path = prepare_audio_for_transcription(ruta_audio)

    service_payload = send_inference_request(
        action="transcribe",
        payload={"audio_path": str(prepared_audio_path)},
        timeout_seconds=INFERENCE_SERVICE_TIMEOUT_SECONDS,
    )
    if service_payload and service_payload.get("ok"):
        print(f"[TIMING] transcription_service_seconds={service_payload.get('timing_seconds', 0.0):.3f}")
        return {"text": service_payload["text"]}

    started_at = time.perf_counter()
    previous_handler = signal.getsignal(signal.SIGALRM)

    def _raise_transcription_timeout(signum, frame):
        raise TimeoutError("local_transcription_timeout")

    signal.signal(signal.SIGALRM, _raise_transcription_timeout)
    signal.alarm(AUDIO_TRANSCRIPTION_TIMEOUT_SECONDS)
    try:
        whisper_module = get_whisper_module()
        model = whisper_module.load_model("tiny")
        print(f"[TIMING] whisper_load_seconds={time.perf_counter() - started_at:.3f}")

        transcribe_started_at = time.perf_counter()
        result = model.transcribe(str(prepared_audio_path), language="es")
    except TimeoutError as exc:
        print(f"[TIMING] whisper_total_seconds={time.perf_counter() - started_at:.3f}")
        raise RuntimeError("local_transcription_timeout") from exc
    except RuntimeError as exc:
        print(f"[TIMING] whisper_total_seconds={time.perf_counter() - started_at:.3f}")
        raise
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)

    print(f"[TIMING] transcription_seconds={time.perf_counter() - transcribe_started_at:.3f}")
    print(f"[TIMING] whisper_total_seconds={time.perf_counter() - started_at:.3f}")
    return result


def face_confidence(face_result):
    if not face_result or face_result.get("distance") is None:
        return None
    return 1.0 - float(face_result["distance"])


def face_result_distance(face_result):
    if not face_result or face_result.get("distance") is None:
        return None
    return float(face_result["distance"])


def combine_errors(*values):
    filtered_values = [value for value in values if value]
    if not filtered_values:
        return None
    return " | ".join(filtered_values)


def measure_audio_max_volume(audio_path):
    result = subprocess.run(
        [
            "ffmpeg",
            "-i",
            str(audio_path),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        timeout=12,
    )

    volumedetect_text = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", volumedetect_text)
    if not match:
        return None
    return float(match.group(1))


def prepare_audio_for_transcription(audio_path):
    audio_path = Path(audio_path)
    prepared_audio_path = audio_path
    try:
        max_volume_db = measure_audio_max_volume(audio_path)
    except Exception as exc:
        print(f"[AUDIO] preprocess_measure_failed error={exc}")
        return prepared_audio_path

    if max_volume_db is None:
        return prepared_audio_path

    print(f"[AUDIO] max_volume_db={max_volume_db:.1f}")
    gain_db = min(AUDIO_TARGET_MAX_DB - max_volume_db, AUDIO_MAX_GAIN_DB)
    if gain_db <= 0.5:
        return prepared_audio_path

    prepared_audio_path = audio_path.with_name(f"{audio_path.stem}_prep.wav")
    started_at = time.perf_counter()
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(audio_path),
            "-af",
            f"highpass=f=120,lowpass=f=3800,volume={gain_db:.1f}dB",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(prepared_audio_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=20,
        check=True,
    )
    print(
        "[AUDIO] preprocessed "
        f"gain_db={gain_db:.1f} "
        f"path={prepared_audio_path} "
        f"seconds={time.perf_counter() - started_at:.3f}"
    )
    return prepared_audio_path

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fast-face-entry":
        response_audio_path = sys.argv[2] if len(sys.argv) > 2 else str(DEFAULT_RESPONSE_AUDIO_PATH)
        gate_opened = process_fast_face_entry(response_audio_path=response_audio_path)
        sys.exit(0 if gate_opened else 2)

    archivo_grabado = sys.argv[1] if len(sys.argv) > 1 else "/tmp/vecino.wav"
    response_audio_path = sys.argv[2] if len(sys.argv) > 2 else str(DEFAULT_RESPONSE_AUDIO_PATH)
    try:
        procesar_audio(archivo_grabado, response_audio_path=response_audio_path)
    except FileNotFoundError as exc:
        print(f"[AUDIO] {exc}")
        print("[AUDIO] Debes indicar un archivo WAV real, por ejemplo:")
        print("[AUDIO]   ./run_vigilia.sh /ruta/al/audio.wav")
        sys.exit(1)

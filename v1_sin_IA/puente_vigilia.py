import whisper
import subprocess
import sys
import json
import os
import re
import socket
import unicodedata
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from gtts import gTTS

try:
    from v1_sin_IA.event_store import insert_access_event
    from v1_sin_IA.vto_camera import capture_snapshot
except ModuleNotFoundError:
    from event_store import insert_access_event
    from vto_camera import capture_snapshot


VTO_IP = "192.168.100.108"
VTO_USER = "admin"
VTO_PASS = "Splitreset6901"
FACE_ENV_PYTHON = Path.home() / "miniforge3" / "envs" / "vigilia-face" / "bin" / "python"
FACE_RECOGNIZER_SCRIPT = Path(__file__).with_name("reconocer_rostro.py")
INFERENCE_SOCKET_PATH = Path("/tmp/vigilia_inference.sock")
DEFAULT_RESPONSE_AUDIO_PATH = Path("/tmp/ia_dice.wav")
VALID_MODEL_TOKENS = {"OPEN", "ERROR", "HOLA"}
USE_PERSISTENT_FACE_SERVICE = False
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
VOICE_OPEN_FUZZY_THRESHOLD = 0.72

# Función para que la IA "hable"
def decir(texto, response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH):
    started_at = time.perf_counter()
    print(f"IA dice: {texto}")
    response_audio_path = Path(response_audio_path)
    response_audio_path.parent.mkdir(parents=True, exist_ok=True)
    temp_mp3_path = response_audio_path.with_suffix(".mp3")

    # Genera el audio
    tts = gTTS(text=texto, lang='es')
    tts.save(str(temp_mp3_path))
    # Convierte a formato Asterisk (WAV mono, 8000Hz)
    subprocess.run([
        'ffmpeg', '-y', '-i', str(temp_mp3_path),
        '-ar', '8000', '-ac', '1', str(response_audio_path)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    temp_mp3_path.unlink(missing_ok=True)
    print(f"[TIMING] tts_seconds={time.perf_counter() - started_at:.3f}")

def ejecutar_porton(response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH):
    started_at = time.perf_counter()
    result = subprocess.run(
        [
            "curl",
            "-sS",
            "--digest",
            "-u",
            f"{VTO_USER}:{VTO_PASS}",
            f"http://{VTO_IP}/cgi-bin/accessControl.cgi?action=openDoor&channel=1",
        ],
        capture_output=True,
        text=True,
    )

    response_text = result.stdout.strip()
    gate_opened = result.returncode == 0 and response_text == "OK"

    if response_text:
        print(f"[GATE] stdout: {response_text}")
    if result.stderr.strip():
        print(f"[GATE] stderr: {result.stderr.strip()}")
    print(f"[GATE] opened: {gate_opened}")
    print(f"[TIMING] gate_request_seconds={time.perf_counter() - started_at:.3f}")

    if gate_opened:
        decir("Acceso concedido. Abriendo el portón ahora.", response_audio_path=response_audio_path)
    else:
        decir("No pude abrir el portón.", response_audio_path=response_audio_path)

    return gate_opened


def try_capture_snapshot():
    started_at = time.perf_counter()
    try:
        snapshot_path = capture_snapshot()
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        return str(snapshot_path), None
    except Exception as exc:
        print(f"[TIMING] snapshot_seconds={time.perf_counter() - started_at:.3f}")
        print(f"[VTO] Snapshot failed: {exc}")
        return None, str(exc)


def try_face_recognition(snapshot_path):
    started_at = time.perf_counter()
    print("[FACE] starting recognition")
    if not snapshot_path:
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_skipped_no_snapshot"

    if USE_PERSISTENT_FACE_SERVICE:
        service_payload = send_inference_request(
            action="face_recognize",
            payload={
                "image_path": snapshot_path,
                "tolerance": 0.45,
            },
            timeout_seconds=12,
        )
        if service_payload:
            if service_payload.get("ok"):
                print(
                    "[FACE] "
                    f"matched={service_payload.get('matched')} "
                    f"name={service_payload.get('matched_person_name')} "
                    f"distance={service_payload.get('distance')}"
                )
                print(f"[TIMING] face_recognition_service_seconds={service_payload.get('timing_seconds', 0.0):.3f}")
                print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
                return service_payload, None

            print(f"[FACE] service_error: {service_payload.get('error')}")

    if not FACE_ENV_PYTHON.exists():
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_env_not_found"

    try:
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
        )
    except subprocess.TimeoutExpired:
        print("[FACE] error: timeout")
        print(f"[TIMING] face_recognition_seconds={time.perf_counter() - started_at:.3f}")
        return None, "face_recognition_timeout"
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


def capture_snapshot_and_face():
    snapshot_path, snapshot_error = try_capture_snapshot()
    face_result, face_error = try_face_recognition(snapshot_path)
    return snapshot_path, snapshot_error, face_result, face_error


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

    result = subprocess.run(
        ["ollama", "run", "vigilia-mini", prompt],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        stderr_text = result.stderr.strip()
        print(f"[MODEL] stderr: {stderr_text}")
        print(f"[TIMING] model_seconds={time.perf_counter() - started_at:.3f}")
        raise RuntimeError("ollama_query_failed")

    response_text = result.stdout.strip()
    print(f"[MODEL] response: {response_text}")
    print(f"[TIMING] model_seconds={time.perf_counter() - started_at:.3f}")
    return response_text


def send_inference_request(action, payload, timeout_seconds):
    if os.environ.get("VIGILIA_DISABLE_INFERENCE_SERVICE") == "1":
        return None

    if not INFERENCE_SOCKET_PATH.exists():
        return None

    started_at = time.perf_counter()
    request_body = {
        "action": action,
        "payload": payload,
    }

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


def detect_open_request(visitor_text):
    normalized_text = normalize_spanish_text(visitor_text)

    if any(keyword in normalized_text for keyword in VOICE_OPEN_KEYWORDS):
        return True

    return any(
        fuzzy_contains_phrase(normalized_text, phrase)
        for phrase in VOICE_OPEN_PHRASES
    )


def has_trusted_face_match(face_result):
    if not face_result:
        return False
    if not face_result.get("matched"):
        return False
    distance = face_result.get("distance")
    tolerance = face_result.get("tolerance")
    if distance is None or tolerance is None:
        return False
    return float(distance) <= float(tolerance)


def face_match_is_access_enabled(face_result):
    if not face_result:
        return False
    person = face_result.get("person") or {}
    return bool(person.get("access_enabled", 1))


def resolve_access_decision(visitor_text, face_result, model_response):
    voice_requests_open = detect_open_request(visitor_text)
    trusted_face_match = has_trusted_face_match(face_result)
    access_enabled_face_match = face_match_is_access_enabled(face_result)
    normalized_model_token = normalize_model_token(model_response)

    if voice_requests_open and trusted_face_match and access_enabled_face_match:
        return {
            "should_open": True,
            "source": "hybrid_policy",
            "reason": (
                "voice_requested_open_and_face_match_within_tolerance_and_whitelisted"
            ),
        }

    if voice_requests_open and trusted_face_match and not access_enabled_face_match:
        return {
            "should_open": False,
            "source": "hybrid_policy",
            "reason": "voice_requested_open_but_face_match_within_tolerance_not_whitelisted",
        }

    if normalized_model_token == "OPEN":
        return {
            "should_open": True,
            "source": "model_response",
            "reason": "model_returned_open",
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
    # Cargar Whisper (oído)
    if not Path(ruta_audio).exists():
        raise FileNotFoundError(f"Audio file not found: {ruta_audio}")

    created_at = datetime.now().isoformat(timespec="seconds")
    started_at = time.perf_counter()
    snapshot_path, snapshot_error = try_capture_snapshot()
    result = transcribe_audio(ruta_audio)
    face_result, face_error = try_face_recognition(snapshot_path)

    print(f"[TIMING] pre_decision_seconds={time.perf_counter() - started_at:.3f}")
    texto_vecino = result["text"].lower().strip()
    
    if not texto_vecino:
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
            error_message=combine_errors(snapshot_error, face_error),
            face_match_name=face_result.get("matched_person_name") if face_result else None,
            face_match_confidence=face_confidence(face_result),
            face_observation_id=face_result.get("observation_id") if face_result else None,
            decision_source="speech_capture",
            decision_reason="empty_transcript",
        )
        return

    print(f"El vecino dijo: {texto_vecino}")

    pre_model_decision = resolve_access_decision(
        visitor_text=texto_vecino,
        face_result=face_result,
        model_response=None,
    )

    if pre_model_decision["source"] == "hybrid_policy":
        print(
            "[DECISION] "
            f"source={pre_model_decision['source']} "
            f"reason={pre_model_decision['reason']} "
            f"should_open={pre_model_decision['should_open']} "
            "stage=pre_model"
        )

        gate_opened = False
        if pre_model_decision["should_open"]:
            gate_opened = ejecutar_porton(response_audio_path=response_audio_path)
        else:
            decir(
                "Lo siento, no tengo autorización para abrir el portón.",
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
        )
        gate_opened = False

        print(
            "[DECISION] "
            f"source={decision['source']} "
            f"reason={decision['reason']} "
            f"should_open={decision['should_open']}"
        )

        if decision["should_open"]:
            gate_opened = ejecutar_porton(response_audio_path=response_audio_path)
        else:
            decir(
                "Lo siento, no tengo autorización para abrir el portón.",
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
        )
    except Exception:
        decir(
            "Hubo un error en mi sistema, intenta más tarde.",
            response_audio_path=response_audio_path,
        )
        insert_access_event(
            created_at=created_at,
            audio_path=ruta_audio,
            transcript=texto_vecino,
            model_response=None,
            gate_opened=False,
            snapshot_path=snapshot_path,
            error_message=combine_errors(
                snapshot_error,
                face_error,
                "ollama_or_processing_error",
            ),
            face_match_name=face_result.get("matched_person_name") if face_result else None,
            face_match_confidence=face_confidence(face_result),
            face_observation_id=face_result.get("observation_id") if face_result else None,
            decision_source="system_error",
            decision_reason="ollama_or_processing_error",
        )


def transcribe_audio(ruta_audio):
    service_payload = send_inference_request(
        action="transcribe",
        payload={"audio_path": ruta_audio},
        timeout_seconds=15,
    )
    if service_payload and service_payload.get("ok"):
        print(f"[TIMING] transcription_service_seconds={service_payload.get('timing_seconds', 0.0):.3f}")
        return {"text": service_payload["text"]}

    started_at = time.perf_counter()
    model = whisper.load_model("tiny")
    print(f"[TIMING] whisper_load_seconds={time.perf_counter() - started_at:.3f}")

    transcribe_started_at = time.perf_counter()
    result = model.transcribe(ruta_audio, language="es")
    print(f"[TIMING] transcription_seconds={time.perf_counter() - transcribe_started_at:.3f}")
    print(f"[TIMING] whisper_total_seconds={time.perf_counter() - started_at:.3f}")
    return result


def face_confidence(face_result):
    if not face_result or face_result.get("distance") is None:
        return None
    return 1.0 - float(face_result["distance"])


def combine_errors(*values):
    filtered_values = [value for value in values if value]
    if not filtered_values:
        return None
    return " | ".join(filtered_values)

if __name__ == "__main__":
    archivo_grabado = sys.argv[1] if len(sys.argv) > 1 else "/tmp/vecino.wav"
    response_audio_path = sys.argv[2] if len(sys.argv) > 2 else str(DEFAULT_RESPONSE_AUDIO_PATH)
    try:
        procesar_audio(archivo_grabado, response_audio_path=response_audio_path)
    except FileNotFoundError as exc:
        print(f"[AUDIO] {exc}")
        print("[AUDIO] Debes indicar un archivo WAV real, por ejemplo:")
        print("[AUDIO]   ./run_vigilia.sh /ruta/al/audio.wav")
        sys.exit(1)

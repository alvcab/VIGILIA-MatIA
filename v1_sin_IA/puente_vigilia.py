import whisper
import subprocess
import sys
import json
from datetime import datetime
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
DEFAULT_RESPONSE_AUDIO_PATH = Path("/tmp/ia_dice.wav")
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
HIGH_CONFIDENCE_FACE_THRESHOLD = 0.82

# Función para que la IA "hable"
def decir(texto, response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH):
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

def ejecutar_porton(response_audio_path=DEFAULT_RESPONSE_AUDIO_PATH):
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

    if gate_opened:
        decir("Acceso concedido. Abriendo el portón ahora.", response_audio_path=response_audio_path)
    else:
        decir("No pude abrir el portón.", response_audio_path=response_audio_path)

    return gate_opened


def try_capture_snapshot():
    try:
        snapshot_path = capture_snapshot()
        return str(snapshot_path), None
    except Exception as exc:
        print(f"[VTO] Snapshot failed: {exc}")
        return None, str(exc)


def try_face_recognition(snapshot_path):
    if not snapshot_path:
        return None, "face_recognition_skipped_no_snapshot"

    if not FACE_ENV_PYTHON.exists():
        return None, "face_recognition_env_not_found"

    result = subprocess.run(
        [
            str(FACE_ENV_PYTHON),
            str(FACE_RECOGNIZER_SCRIPT),
            snapshot_path,
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode not in {0, 2}:
        stderr_text = result.stderr.strip()
        print(f"[FACE] stderr: {stderr_text}")
        return None, "face_recognition_execution_error"

    stdout_text = result.stdout.strip().splitlines()
    if not stdout_text:
        return None, "face_recognition_no_output"

    payload_text = stdout_text[-1]
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        print(f"[FACE] raw output: {result.stdout.strip()}")
        return None, "face_recognition_invalid_output"

    if not payload.get("backend_available", False):
        return None, payload.get("error", "face_recognition_backend_unavailable")

    print(
        "[FACE] "
        f"matched={payload.get('matched')} "
        f"name={payload.get('matched_person_name')} "
        f"distance={payload.get('distance')}"
    )
    return payload, None


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
        "ACCESS_REQUEST\n"
        f"VISITOR_SPEECH: {visitor_text}\n"
        f"FACIAL_CONTEXT: {facial_context}\n"
        "TASK: Decide if the visitor is asking to open the gate.\n"
        "POLICY: If the speech clearly asks to open and the face is a high-confidence match, prioritize OPEN.\n"
        "POLICY: If the speech does not request access, do not open based only on the face.\n"
        "RULE: Reply with only one token.\n"
        "VALID_TOKENS: OPEN, ERROR, HOLA\n"
    )


def query_access_model(visitor_text, face_result):
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
        raise RuntimeError("ollama_query_failed")

    response_text = result.stdout.strip()
    print(f"[MODEL] response: {response_text}")
    return response_text


def detect_open_request(visitor_text):
    normalized_text = visitor_text.lower()
    return any(keyword in normalized_text for keyword in VOICE_OPEN_KEYWORDS)


def has_high_confidence_face_match(face_result):
    if not face_result:
        return False
    if not face_result.get("matched"):
        return False
    confidence = face_confidence(face_result)
    if confidence is None:
        return False
    return confidence >= HIGH_CONFIDENCE_FACE_THRESHOLD


def face_match_is_access_enabled(face_result):
    if not face_result:
        return False
    person = face_result.get("person") or {}
    return bool(person.get("access_enabled", 1))


def resolve_access_decision(visitor_text, face_result, model_response):
    voice_requests_open = detect_open_request(visitor_text)
    high_confidence_face_match = has_high_confidence_face_match(face_result)
    access_enabled_face_match = face_match_is_access_enabled(face_result)
    normalized_model_response = (model_response or "").strip().upper()

    if voice_requests_open and high_confidence_face_match and access_enabled_face_match:
        return {
            "should_open": True,
            "source": "hybrid_policy",
            "reason": (
                "voice_requested_open_and_face_match_high_confidence_and_whitelisted"
            ),
        }

    if voice_requests_open and high_confidence_face_match and not access_enabled_face_match:
        return {
            "should_open": False,
            "source": "hybrid_policy",
            "reason": "voice_requested_open_but_face_match_not_whitelisted",
        }

    if "OPEN" in normalized_model_response:
        return {
            "should_open": True,
            "source": "model_response",
            "reason": "model_returned_open",
        }

    if voice_requests_open and not high_confidence_face_match:
        return {
            "should_open": False,
            "source": "hybrid_policy",
            "reason": "voice_requested_open_but_face_match_not_high_confidence",
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

    model = whisper.load_model("tiny")
    created_at = datetime.now().isoformat(timespec="seconds")
    snapshot_path, snapshot_error = try_capture_snapshot()
    face_result, face_error = try_face_recognition(snapshot_path)
    result = model.transcribe(ruta_audio, language="es")
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

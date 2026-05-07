from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from app.config import load_config, resolve_repo_path
from services.access_control.dry_run import DryRunGate
from services.decision.conversation_store import ConversationStore
from services.decision.hybrid import evaluate_hybrid_decision
from services.decision.policy import decide_from_text
from services.decision.resident_directory import ResidentDirectory
from services.decision.turn_evaluator import TurnEvaluator, TurnInput
from services.telephony.baresip_pipeline import BaresipPipeline
from services.telephony.audio_file_flow import AudioFileFlow
from services.telephony.call_router import CallRouter
from services.telephony.in_memory import InMemorySessionFactory
from services.telephony.sip_adapter import SipAdapter
from services.tts.canned_audio import build_spoken_response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIGILIA M4 GDS3725 scaffold")
    parser.add_argument(
        "--mode",
        choices=[
            "decision-only",
            "dry-run",
            "session-replay",
            "audio-file",
            "sip-preview",
            "sip-session",
            "baresip-preview",
            "hybrid-decision",
            "conversation-turn",
            "turn-evaluation",
            "baresip-inbox",
            "baresip-watch-once",
        ],
        default=None,
    )
    parser.add_argument("--text", default="", help="Input text for the policy layer")
    parser.add_argument("--caller-id", default="test-intercom", help="Simulated caller id")
    parser.add_argument("--audio-file", default="", help="Local WAV file for audio-file mode")
    parser.add_argument("--session-id", default="", help="Conversation session id for follow-up tests")
    parser.add_argument("--face-resident-id", default="", help="Trusted face match resident id")
    parser.add_argument("--face-display-name", default="", help="Trusted face match display name")
    parser.add_argument("--face-confidence", default="", help="Trusted face match confidence label")
    parser.add_argument(
        "--face-trusted",
        action="store_true",
        help="Indicates that the device delivered a trusted resident face match",
    )
    parser.add_argument(
        "--face-checked",
        action="store_true",
        help="Indicates that the device attempted face recognition for this session",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()
    mode = args.mode or config.default_mode
    residents_path = resolve_repo_path(config.residents_path)
    runtime_dir = resolve_repo_path(config.runtime_dir)
    resident_directory = None

    if residents_path.exists():
        resident_directory = ResidentDirectory.from_yaml_like_file(residents_path)

    decision = decide_from_text(args.text, resident_directory)

    if mode == "session-replay":
        session = InMemorySessionFactory().create(
            caller_id=args.caller_id,
            transcript=args.text,
        )
        routed = CallRouter(resident_directory=resident_directory).route(session)
        print(json.dumps(routed, ensure_ascii=True, indent=2))
        return 0

    if mode == "audio-file":
        routed = AudioFileFlow(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        ).run(
            caller_id=args.caller_id,
            audio_file=args.audio_file,
        )
        print(json.dumps(routed, ensure_ascii=True, indent=2))
        return 0

    if mode == "sip-preview":
        preview = SipAdapter().build_preview(args.caller_id)
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "conversation-turn":
        store = ConversationStore(runtime_dir)
        prior_state = store.load(args.session_id) if args.session_id else None
        session = InMemorySessionFactory().create(
            caller_id=args.caller_id,
            transcript=args.text,
            session_id=args.session_id or None,
            prior_turn_count=prior_state.turn_count if prior_state else 0,
        )
        routed = CallRouter(
            resident_directory=resident_directory,
            conversation_store=store,
        ).route(session)
        print(json.dumps(routed, ensure_ascii=True, indent=2))
        return 0

    if mode == "turn-evaluation":
        session_id = args.session_id or "turn-eval-demo"
        result = TurnEvaluator(
            resident_directory=resident_directory,
            conversation_store=ConversationStore(runtime_dir),
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        ).evaluate_turn(
            TurnInput(
                session_id=session_id,
                caller_id=args.caller_id,
                transcript=args.text,
                face_match_resident_id=args.face_resident_id,
                face_match_display_name=args.face_display_name,
                face_match_confidence=args.face_confidence,
                face_match_trusted=args.face_trusted,
                face_check_performed=args.face_checked,
            )
        )
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0

    if mode == "sip-session":
        preview = SipAdapter().simulate_session(args.caller_id)
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "baresip-preview":
        preview = SipAdapter().build_baresip_preview(args.caller_id)
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "baresip-inbox":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        if args.audio_file:
            preview = pipeline.process_audio_file(args.audio_file, args.caller_id)
        else:
            preview = pipeline.process_latest()
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "baresip-watch-once":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        preview = pipeline.process_new_files_once()
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "hybrid-decision":
        preview = evaluate_hybrid_decision(
            args.text,
            resident_directory,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    output = {
        "mode": mode,
        "decision": asdict(decision),
        "spoken_response": build_spoken_response(decision),
    }

    if mode == "dry-run":
        output["gate_action"] = DryRunGate().handle(decision)

    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

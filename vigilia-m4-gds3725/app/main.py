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
from services.telephony.department_authorization_runtime import DepartmentAuthorizationRuntime
from services.telephony.department_authorization_service import DepartmentAuthorizationService
from services.telephony.baresip_pipeline import BaresipPipeline
from services.telephony.audio_file_flow import AudioFileFlow
from services.telephony.call_router import CallRouter
from services.telephony.in_memory import InMemorySessionFactory
from services.telephony.matia_call_service import MatiaCallServiceRuntime, MatiaDepartmentCallService
from services.transcription.service import TranscriptionService
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
            "department-watch-once",
            "department-request-list",
            "department-respond",
            "department-submit-response",
            "department-call-run-preview",
            "department-call-service-demo",
            "department-call-service-status",
            "department-call-service-enqueue",
            "department-call-service-run-once",
            "department-call-service-reply",
            "department-call-service-reply-audio",
            "department-call-service-timeout",
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
    parser.add_argument(
        "--department-status",
        default="",
        help="Department authorization result: approved, denied or no_response",
    )
    parser.add_argument(
        "--registered-visit-code",
        default="",
        help="Expected 4-digit authorization code for a pre-registered visit",
    )
    parser.add_argument(
        "--department-target",
        default="",
        help="Department target label for MatIA outgoing department-call previews",
    )
    parser.add_argument(
        "--live-call",
        action="store_true",
        help="Execute the outgoing department call without dry-run safeguards",
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
            conversation_store=ConversationStore(runtime_dir),
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
                department_authorization_status=args.department_status,
                registered_visit_code=args.registered_visit_code,
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

    if mode == "department-watch-once":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        preview = pipeline.process_department_responses_once()
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-request-list":
        service = DepartmentAuthorizationService(
            DepartmentAuthorizationRuntime(resolve_repo_path(config.runtime_dir) / "baresip")
        )
        pending = service.list_pending_requests()
        print(
            json.dumps(
                {
                    "mode": "department-request-list",
                    "pending_count": len(pending),
                    "pending": [asdict(item) for item in pending],
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0

    if mode == "department-respond":
        service = DepartmentAuthorizationService(
            DepartmentAuthorizationRuntime(resolve_repo_path(config.runtime_dir) / "baresip")
        )
        preview = service.create_response(
            session_id=args.session_id,
            status=args.department_status,
            caller_id=args.caller_id,
        )
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-submit-response":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        preview = pipeline.submit_department_response(
            session_id=args.session_id,
            status=args.department_status,
            caller_id=args.caller_id,
            producer="matia",
        )
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-call-run-preview":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        department_target = args.department_target or "Departamento 1"
        preview = pipeline.preview_department_call_run(
            request_payload={
                "session_id": args.session_id or "department-call-preview",
                "caller_id": args.caller_id,
                "resident_candidate": args.text,
                "department_target": department_target,
            },
            call_plan={
                "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                "opening_text": "Hola. Habla MatIA de Vigilia.",
                "authorization_question": "Indica aprobado, rechazado o sin respuesta.",
                "no_response_strategy": "Si no hay respuesta, se informa a la visita y puede pedirse codigo de 4 digitos.",
            },
            dry_run=True,
        )
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-call-service-demo":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        service = MatiaDepartmentCallService(
            pipeline,
            MatiaCallServiceRuntime.from_workdir(resolve_repo_path(config.runtime_dir) / "baresip"),
        )
        department_target = args.department_target or "Departamento 1"
        session_id = args.session_id or "department-call-service-demo"
        call_plan = {
            "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
            "opening_text": "Hola. Habla MatIA de Vigilia.",
            "authorization_question": "Indica aprobado, rechazado o sin respuesta.",
            "no_response_strategy": "Si no hay respuesta, se informa a la visita y puede pedirse codigo de 4 digitos.",
        }
        started = service.start_call(
            request_payload={
                "session_id": session_id,
                "caller_id": args.caller_id,
                "resident_candidate": args.text,
                "department_target": department_target,
            },
            call_plan=call_plan,
            dry_run=True,
        )
        status_after_start = service.get_status(session_id)
        finished = service.finish_call(session_id)
        print(
            json.dumps(
                {
                    "mode": "department-call-service-demo",
                    "started": started,
                    "status_after_start": status_after_start,
                    "finished": finished,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0

    if mode == "department-call-service-status":
        runtime = MatiaCallServiceRuntime.from_workdir(resolve_repo_path(config.runtime_dir) / "baresip")
        status = runtime.load_status(args.session_id)
        print(
            json.dumps(
                {
                    "mode": "department-call-service-status",
                    "session_id": args.session_id,
                    "status": status,
                },
                ensure_ascii=True,
                indent=2,
            )
        )
        return 0

    if mode == "department-call-service-enqueue":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        service = MatiaDepartmentCallService(
            pipeline,
            MatiaCallServiceRuntime.from_workdir(resolve_repo_path(config.runtime_dir) / "baresip"),
        )
        department_target = args.department_target or "Departamento 1"
        session_id = args.session_id or "department-call-service-queued"
        preview = service.enqueue_call(
            request_payload={
                "session_id": session_id,
                "caller_id": args.caller_id,
                "resident_candidate": args.text,
                "department_target": department_target,
            },
            call_plan={
                "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                "opening_text": "Hola. Habla MatIA de Vigilia.",
                "authorization_question": "Indica aprobado, rechazado o sin respuesta.",
                "no_response_strategy": "Si no hay respuesta, se informa a la visita y puede pedirse codigo de 4 digitos.",
            },
            dry_run=not args.live_call,
        )
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-call-service-run-once":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        service = MatiaDepartmentCallService(
            pipeline,
            MatiaCallServiceRuntime.from_workdir(resolve_repo_path(config.runtime_dir) / "baresip"),
        )
        preview = service.run_once()
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-call-service-reply":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        service = MatiaDepartmentCallService(
            pipeline,
            MatiaCallServiceRuntime.from_workdir(resolve_repo_path(config.runtime_dir) / "baresip"),
        )
        preview = service.submit_department_reply_text(
            args.session_id,
            args.text,
        )
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-call-service-reply-audio":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        service = MatiaDepartmentCallService(
            pipeline,
            MatiaCallServiceRuntime.from_workdir(resolve_repo_path(config.runtime_dir) / "baresip"),
            transcription_service=TranscriptionService(
                backend_name=config.transcription_backend,
                whisper_model=config.whisper_model,
            ),
        )
        preview = service.submit_department_reply_audio(
            args.session_id,
            args.audio_file,
        )
        print(json.dumps(preview, ensure_ascii=True, indent=2))
        return 0

    if mode == "department-call-service-timeout":
        pipeline = BaresipPipeline(
            resident_directory=resident_directory,
            transcription_backend_name=config.transcription_backend,
            whisper_model=config.whisper_model,
            model_backend_name=config.model_backend,
            ollama_model=config.ollama_model,
            ollama_timeout_seconds=config.ollama_timeout_seconds,
        )
        service = MatiaDepartmentCallService(
            pipeline,
            MatiaCallServiceRuntime.from_workdir(resolve_repo_path(config.runtime_dir) / "baresip"),
        )
        preview = service.submit_no_response(args.session_id)
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

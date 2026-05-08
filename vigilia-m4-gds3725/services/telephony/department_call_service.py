from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from services.decision.resident_directory import ResidentDirectory
from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_transport import BaresipTransport
from services.telephony.baresip_outgoing_call_executor import BaresipOutgoingCallExecutor
from services.telephony.baresip_outgoing_call_runner import BaresipOutgoingCallRunner
from services.telephony.sip_config import SipEndpointConfig
from services.telephony.sip_uri import build_sip_uri


@dataclass(frozen=True)
class DepartmentCallExecutionPlan:
    session_id: str
    resident_candidate: str
    department_target: str
    target_uri: str
    local_uri: str
    reply_audio_capture: dict[str, object]
    reply_audio_hook: dict[str, object]
    invite_preview: dict[str, object]
    baresip_execution_preview: dict[str, object]
    voice_plan: dict[str, object]
    opening_text: str
    authorization_question: str
    no_response_strategy: str

    def as_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "resident_candidate": self.resident_candidate,
            "department_target": self.department_target,
            "target_uri": self.target_uri,
            "local_uri": self.local_uri,
            "reply_audio_capture": dict(self.reply_audio_capture),
            "reply_audio_hook": dict(self.reply_audio_hook),
            "invite_preview": self.invite_preview,
            "baresip_execution_preview": self.baresip_execution_preview,
            "voice_plan": self.voice_plan,
            "opening_text": self.opening_text,
            "authorization_question": self.authorization_question,
            "no_response_strategy": self.no_response_strategy,
        }


class DepartmentCallService:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None,
        sip_config: SipEndpointConfig | None = None,
        baresip_config: BaresipConfig | None = None,
        transport: BaresipTransport | None = None,
        outgoing_executor: BaresipOutgoingCallExecutor | None = None,
        outgoing_runner: BaresipOutgoingCallRunner | None = None,
    ) -> None:
        self._baresip_config = baresip_config or BaresipConfig.from_env()
        self._resident_directory = resident_directory
        self._sip_config = sip_config or SipEndpointConfig(
            device_label="gds3725",
            local_user="vigilia",
            local_domain="127.0.0.1",
        )
        self._transport = transport or BaresipTransport(self._baresip_config)
        self._outgoing_executor = outgoing_executor or BaresipOutgoingCallExecutor(self._baresip_config)
        self._outgoing_runner = outgoing_runner or BaresipOutgoingCallRunner()

    def _resolve_target_uri(self, resident_candidate: str, department_target: str) -> str:
        if self._resident_directory is None:
            return ""

        resident = None
        if resident_candidate:
            resident = self._resident_directory.resolve(resident_candidate) or self._resident_directory.resolve_partial(
                resident_candidate
            )
        if resident is None and department_target:
            resident = self._resident_directory.resolve(department_target) or self._resident_directory.resolve_partial(
                department_target
            )
        if resident is None:
            return ""
        return resident.department_sip_uri

    def _build_reply_audio_capture(self, session_id: str, target_uri: str) -> dict[str, object]:
        workdir = Path(self._baresip_config.workdir)
        root = workdir / "matia_call_service" / "reply_audio_inbox"
        audio_file = root / f"{session_id}.wav"
        metadata_file = root / f"{session_id}.json"
        return {
            "audio_file": str(audio_file),
            "metadata_file": str(metadata_file),
            "transport_contract": "baresip-live-reply-audio",
            "target_uri": target_uri,
        }

    def _build_reply_audio_hook(self, session_id: str) -> dict[str, object]:
        workdir = Path(self._baresip_config.workdir)
        repo_root = workdir.parent.parent if workdir.name == "baresip" and workdir.parent.name == "runtime" else Path(".")
        capture_root = workdir / "matia_call_service" / "reply_audio_capture_tmp"
        capture_audio_file = capture_root / f"{session_id}.wav"
        deposit_script = repo_root / "scripts" / "deposit_department_reply_audio.sh"
        return {
            "capture_temp_audio_file": str(capture_audio_file),
            "invoke_moment": "after_call_audio_capture_complete",
            "deposit_command": [
                str(deposit_script),
                session_id,
                str(capture_audio_file),
            ],
            "watch_command": [
                "python3",
                "-m",
                "app.main",
                "--mode",
                "department-call-service-reply-audio-watch-once",
            ],
        }

    def build_execution_plan(
        self,
        request_payload: dict[str, object],
        call_plan: dict[str, object],
    ) -> DepartmentCallExecutionPlan:
        resident_candidate = str(request_payload.get("resident_candidate", ""))
        department_target = str(request_payload.get("department_target", ""))
        target_uri = self._resolve_target_uri(resident_candidate, department_target)
        reply_audio_capture = self._build_reply_audio_capture(
            str(request_payload.get("session_id", "")),
            target_uri,
        )
        reply_audio_hook = self._build_reply_audio_hook(str(request_payload.get("session_id", "")))
        local_uri = build_sip_uri(
            user=self._sip_config.local_user,
            domain=self._sip_config.local_domain,
            port=self._sip_config.local_port,
            transport=self._sip_config.transport,
        )
        invite_preview = self._transport.invite(
            caller_id=str(request_payload.get("caller_id", "matia-department-call")),
            from_uri=local_uri,
            to_uri=target_uri,
        )
        execution_preview = self._outgoing_executor.build_execution(
            target_uri,
            reply_audio_path=str(reply_audio_capture["audio_file"]),
            reply_audio_metadata_path=str(reply_audio_capture["metadata_file"]),
            reply_audio_hook=reply_audio_hook,
        ).as_dict()
        return DepartmentCallExecutionPlan(
            session_id=str(request_payload.get("session_id", "")),
            resident_candidate=resident_candidate,
            department_target=department_target,
            target_uri=target_uri,
            local_uri=local_uri,
            reply_audio_capture=reply_audio_capture,
            reply_audio_hook=reply_audio_hook,
            invite_preview=invite_preview,
            baresip_execution_preview=execution_preview,
            voice_plan=dict(call_plan.get("voice_plan", {})),
            opening_text=str(call_plan.get("opening_text", "")),
            authorization_question=str(call_plan.get("authorization_question", "")),
            no_response_strategy=str(call_plan.get("no_response_strategy", "")),
        )

    def run_execution_plan(
        self,
        execution_plan: DepartmentCallExecutionPlan,
        *,
        dry_run: bool = True,
        timeout_seconds: float = 5.0,
    ) -> dict[str, object]:
        run_result = self._outgoing_runner.run_preview(
            execution_plan.baresip_execution_preview,
            dry_run=dry_run,
            timeout_seconds=timeout_seconds,
        )
        return {
            "session_id": execution_plan.session_id,
            "department_target": execution_plan.department_target,
            "target_uri": execution_plan.target_uri,
            "reply_audio_capture": execution_plan.reply_audio_capture,
            "reply_audio_hook": execution_plan.reply_audio_hook,
            "run_result": run_result.as_dict(),
        }

    def start_execution_session(
        self,
        execution_plan: DepartmentCallExecutionPlan,
        *,
        dry_run: bool = True,
    ) -> dict[str, object]:
        session = self._outgoing_runner.start_session(
            execution_plan.session_id,
            execution_plan.baresip_execution_preview,
            dry_run=dry_run,
        )
        return {
            "session_id": execution_plan.session_id,
            "department_target": execution_plan.department_target,
            "target_uri": execution_plan.target_uri,
            "reply_audio_capture": execution_plan.reply_audio_capture,
            "reply_audio_hook": execution_plan.reply_audio_hook,
            "call_session": session.as_dict(),
        }

    def finish_execution_session(
        self,
        session_id: str,
        *,
        timeout_seconds: float = 5.0,
    ) -> dict[str, object]:
        run_result = self._outgoing_runner.finish_session(
            session_id,
            timeout_seconds=timeout_seconds,
        )
        return {
            "session_id": session_id,
            "run_result": run_result.as_dict(),
        }

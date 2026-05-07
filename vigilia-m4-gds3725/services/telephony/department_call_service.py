from __future__ import annotations

from dataclasses import dataclass

from services.decision.resident_directory import ResidentDirectory
from services.telephony.baresip_transport import BaresipTransport
from services.telephony.sip_config import SipEndpointConfig
from services.telephony.sip_uri import build_sip_uri


@dataclass(frozen=True)
class DepartmentCallExecutionPlan:
    session_id: str
    resident_candidate: str
    department_target: str
    target_uri: str
    local_uri: str
    invite_preview: dict[str, object]
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
            "invite_preview": self.invite_preview,
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
        transport: BaresipTransport | None = None,
    ) -> None:
        self._resident_directory = resident_directory
        self._sip_config = sip_config or SipEndpointConfig(
            device_label="gds3725",
            local_user="vigilia",
            local_domain="127.0.0.1",
        )
        self._transport = transport or BaresipTransport()

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

    def build_execution_plan(
        self,
        request_payload: dict[str, object],
        call_plan: dict[str, object],
    ) -> DepartmentCallExecutionPlan:
        resident_candidate = str(request_payload.get("resident_candidate", ""))
        department_target = str(request_payload.get("department_target", ""))
        target_uri = self._resolve_target_uri(resident_candidate, department_target)
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
        return DepartmentCallExecutionPlan(
            session_id=str(request_payload.get("session_id", "")),
            resident_candidate=resident_candidate,
            department_target=department_target,
            target_uri=target_uri,
            local_uri=local_uri,
            invite_preview=invite_preview,
            voice_plan=dict(call_plan.get("voice_plan", {})),
            opening_text=str(call_plan.get("opening_text", "")),
            authorization_question=str(call_plan.get("authorization_question", "")),
            no_response_strategy=str(call_plan.get("no_response_strategy", "")),
        )

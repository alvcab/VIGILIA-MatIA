from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from services.telephony.department_authorization_runtime import DepartmentAuthorizationRuntime


@dataclass(frozen=True)
class DepartmentAuthorizationRequest:
    session_id: str
    caller_id: str
    device_label: str
    transport: str
    resident_candidate: str
    department_target: str
    current_intent: str
    registered_visit_available: bool


class DepartmentAuthorizationService:
    def __init__(self, runtime: DepartmentAuthorizationRuntime) -> None:
        self._runtime = runtime

    def list_pending_requests(self) -> list[DepartmentAuthorizationRequest]:
        return [
            DepartmentAuthorizationRequest(
                session_id=str(item.get("session_id", "")),
                caller_id=str(item.get("caller_id", "")),
                device_label=str(item.get("device_label", "gds3725")),
                transport=str(item.get("transport", "sip-udp")),
                resident_candidate=str(item.get("resident_candidate", "")),
                department_target=str(item.get("department_target", "")),
                current_intent=str(item.get("current_intent", "")),
                registered_visit_available=bool(item.get("registered_visit_available", False)),
            )
            for item in self._runtime.list_pending_requests()
        ]

    def create_response(
        self,
        session_id: str,
        status: str,
        *,
        caller_id: str = "",
        device_label: str = "",
        transport: str = "",
    ) -> dict[str, object]:
        normalized_status = status.strip().lower()
        if normalized_status not in {"approved", "denied", "no_response"}:
            raise ValueError("status must be one of: approved, denied, no_response")

        request = self._runtime.load_request(session_id) or {}
        payload = {
            "session_id": session_id,
            "caller_id": caller_id or str(request.get("caller_id", "department-authorization")),
            "device_label": device_label or str(request.get("device_label", "gds3725")),
            "transport": transport or str(request.get("transport", "sip-udp")),
            "department_authorization": {
                "status": normalized_status,
                "department_target": str(request.get("department_target", "")),
                "resident_candidate": str(request.get("resident_candidate", "")),
            },
        }
        response_path = self._runtime.save_response(session_id, payload)
        return {
            "mode": "department-respond",
            "session_id": session_id,
            "status": normalized_status,
            "response_path": str(response_path),
            "request_found": bool(request),
            "payload": payload,
        }

    def create_matia_response(
        self,
        session_id: str,
        status: str,
        *,
        caller_id: str = "",
        device_label: str = "",
        transport: str = "",
        producer: str = "matia",
    ) -> dict[str, object]:
        result = self.create_response(
            session_id=session_id,
            status=status,
            caller_id=caller_id,
            device_label=device_label,
            transport=transport,
        )
        payload = dict(result["payload"])
        payload["producer"] = producer
        response_path = self._runtime.save_response(session_id, payload)
        result["mode"] = "department-respond-matia"
        result["response_path"] = str(response_path)
        result["payload"] = payload
        return result

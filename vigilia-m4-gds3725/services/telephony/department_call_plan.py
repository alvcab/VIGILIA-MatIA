from __future__ import annotations

from dataclasses import asdict, dataclass

from services.tts.matia_voice import build_department_voice_plan


@dataclass(frozen=True)
class DepartmentCallRequest:
    session_id: str
    caller_id: str
    resident_candidate: str
    department_target: str
    current_intent: str
    registered_visit_available: bool


@dataclass(frozen=True)
class DepartmentCallPlan:
    session_id: str
    target_label: str
    opening_text: str
    authorization_question: str
    no_response_strategy: str
    voice_plan: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def build_department_call_plan(request: DepartmentCallRequest) -> DepartmentCallPlan:
    visitor_reason = "una visita" if request.current_intent != "delivery" else "una entrega"
    identified_as = request.resident_candidate or request.department_target
    opening_text = (
        f"Hola. Habla MatIA de Vigilia. Tengo {visitor_reason} para {identified_as} en el acceso."
    )
    authorization_question = (
        "Necesito confirmar si autorizas el ingreso. "
        "Responde aprobado, rechazado o sin respuesta."
    )
    no_response_strategy = (
        "Si no contestan y existe visita registrada, MatIA debe pedir codigo de 4 digitos a la visita."
        if request.registered_visit_available
        else "Si no contestan, MatIA debe informar que no tiene respuesta del departamento."
    )
    voice_plan = build_department_voice_plan(f"{opening_text} {authorization_question}").as_dict()
    return DepartmentCallPlan(
        session_id=request.session_id,
        target_label=request.department_target,
        opening_text=opening_text,
        authorization_question=authorization_question,
        no_response_strategy=no_response_strategy,
        voice_plan=voice_plan,
    )

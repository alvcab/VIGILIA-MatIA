from __future__ import annotations

from services.decision.policy import Decision


def build_spoken_response(decision: Decision) -> str:
    if decision.reason == "trusted_face_match":
        return ""
    if decision.reason in {"department_denied_access", "registered_visit_code_invalid"}:
        return "Lo siento, no esta autorizado."
    if decision.reason == "department_no_response":
        return f"No tengo respuesta del {decision.department_target.lower()}."
    if decision.reason == "department_no_response_registered_visit":
        return (
            f"No tengo respuesta del {decision.department_target.lower()}. "
            "Si tienes un codigo de autorizacion de 4 digitos, indicalo ahora."
        )
    if decision.reason == "greeting_after_no_face_match":
        return "Hola. No reconozco tu rostro. A que residente vienes a ver?"
    if decision.reason == "insufficient_context_after_no_face_match":
        return "No reconozco tu rostro. Indica a que residente o departamento vienes."
    if decision.reason == "authorization_claim_without_resident":
        return "Entendido. Indica que residente o departamento autorizo tu ingreso."
    if decision.action == "contact_department":
        return f"Un momento. Llamare al {decision.department_target.lower()}."
    if decision.action == "open":
        return "Abriendo."
    if decision.action == "ask_retry":
        return "No pude escucharte bien."
    if decision.action == "escalate_urgent":
        return "Entendido. Intentare derivar la urgencia de inmediato."
    if decision.action == "reset_interaction":
        return "Entendido. Puedes volver a intentarlo cuando quieras."
    if decision.action == "clarify_authorization":
        return "Indica a que residente vienes a ver o quien autorizo tu ingreso."
    if decision.action == "request_resident_confirmation":
        return f"Entendido. Confirmare con {decision.resident_hint} antes de abrir."
    if decision.action == "announce_resident":
        return f"Entendido. Avisare a {decision.resident_hint}."
    if decision.action == "announce_delivery":
        return f"Entendido. Avisare a {decision.resident_hint} por la entrega."
    if decision.action == "clarify_delivery_recipient":
        return "Indica para que residente o departamento es la entrega."
    if decision.action == "greet_and_clarify":
        return "Hola. A que residente vienes a ver?"
    return "Indica a que residente o departamento vienes."

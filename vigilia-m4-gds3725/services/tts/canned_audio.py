from __future__ import annotations

from services.decision.policy import Decision


def build_spoken_response(decision: Decision) -> str:
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
        return "Indica para que residente es la entrega."
    if decision.action == "greet_and_clarify":
        return "Hola. A que residente vienes a ver?"
    return "Indica a que residente vienes a ver."

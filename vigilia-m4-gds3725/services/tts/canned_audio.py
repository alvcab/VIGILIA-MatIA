from __future__ import annotations

from services.decision.policy import Decision


def build_spoken_response(decision: Decision) -> str:
    if decision.action == "open":
        return "Abriendo."
    if decision.action == "ask_retry":
        return "No pude escucharte bien."
    if decision.action == "greet_and_clarify":
        return "Hola. A que residente vienes a ver?"
    return "Indica a que residente vienes a ver."

from __future__ import annotations

from services.decision.prompt_context import PromptContext


def build_follow_up_prompt(context: PromptContext) -> str:
    if context.next_step == "ask_resident_confirmation":
        return (
            f"Visita identificada para {context.resident_display_name or context.resident_hint}. "
            "Solicita confirmacion breve antes de autorizar ingreso."
        )
    if context.next_step == "ask_delivery_recipient":
        return "Solicita que indique para que residente o unidad viene la entrega."
    if context.next_step == "clarify_authorization":
        return "Solicita residente o autorizacion explicita antes de abrir."
    if context.next_step == "urgent_escalation":
        return "Indica que la situacion urgente debe ser derivada de inmediato."
    return "Solicita aclaracion breve del motivo de la visita."

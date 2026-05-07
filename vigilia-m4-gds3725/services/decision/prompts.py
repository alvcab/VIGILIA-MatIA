from __future__ import annotations

from services.decision.prompt_context import PromptContext


def _prepend_summary(context: PromptContext, instruction: str) -> str:
    if not context.conversation_summary:
        return instruction
    return f"Contexto previo: {context.conversation_summary}\n{instruction}"


def build_follow_up_prompt(context: PromptContext) -> str:
    if context.face_recognition_result == "no_match" and context.next_step == "clarify_resident":
        return _prepend_summary(
            context,
            "No hubo match facial confiable. Solicita de forma breve el residente o el departamento al que viene.",
        )
    if context.next_step == "ask_resident_confirmation":
        return _prepend_summary(
            context,
            (
            f"Visita identificada para {context.resident_display_name or context.resident_hint}. "
            "Solicita confirmacion breve antes de autorizar ingreso."
            ),
        )
    if context.next_step == "ask_delivery_recipient":
        return _prepend_summary(
            context,
            "Solicita que indique para que residente o departamento viene la entrega.",
        )
    if context.next_step == "clarify_resident_for_authorization":
        return _prepend_summary(
            context,
            "La visita dice que esta autorizada o que la esperan. Solicita el residente o el departamento que autoriza el ingreso.",
        )
    if context.next_step == "clarify_authorization":
        return _prepend_summary(
            context,
            "Solicita residente o autorizacion explicita antes de abrir.",
        )
    if context.next_step == "urgent_escalation":
        return _prepend_summary(
            context,
            "Indica que la situacion urgente debe ser derivada de inmediato.",
        )
    if context.next_step == "clarify_resident":
        return _prepend_summary(
            context,
            "Solicita de forma breve a que residente o departamento viene.",
        )
    return _prepend_summary(context, "Solicita aclaracion breve del motivo de la visita.")

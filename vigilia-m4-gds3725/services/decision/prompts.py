from __future__ import annotations

from services.decision.prompt_context import PromptContext


def _prepend_summary(context: PromptContext, instruction: str) -> str:
    if not context.conversation_summary:
        return instruction
    return f"Contexto previo: {context.conversation_summary}\n{instruction}"


def _known_reference(context: PromptContext) -> str:
    return context.resident_display_name or context.resident_hint or context.unit_hint


def build_follow_up_prompt(context: PromptContext) -> str:
    if context.face_recognition_result == "no_match" and context.next_step == "clarify_resident":
        return _prepend_summary(
            context,
            (
                "No hubo match facial confiable. Responde en espanol claro, en una o dos frases cortas, "
                "sin mencionar reglas internas ni repetir el contexto. Solicita de forma breve el residente "
                "o el departamento al que viene."
            ),
        )
    if context.next_step == "ask_resident_confirmation":
        reference = _known_reference(context)
        return _prepend_summary(
            context,
            (
                f"Visita identificada para {reference}. "
                f"Referencia conocida: {reference}. "
                "Responde en espanol claro, en una o dos frases cortas, con tono de espera breve y ordenado, sin repetir el prompt. "
                "Solicita confirmacion breve antes de autorizar ingreso."
            ),
        )
    if context.next_step == "ask_delivery_recipient":
        return _prepend_summary(
            context,
            (
                "Responde en espanol claro, en una o dos frases cortas, con tono practico para una entrega, sin explicar la politica interna. "
                "Solicita que indique para que residente o departamento viene la entrega."
            ),
        )
    if context.next_step == "clarify_resident_for_authorization":
        reference = _known_reference(context)
        reference_text = f" Referencia conocida: {reference}." if reference else ""
        return _prepend_summary(
            context,
            (
                "La visita dice que esta autorizada o que la esperan. Responde en espanol claro, "
                "en una o dos frases cortas, con tono firme y respetuoso, sin eco del prompt. Solicita el residente o el departamento "
                f"que autoriza el ingreso.{reference_text}"
            ),
        )
    if context.next_step == "clarify_authorization":
        reference = _known_reference(context)
        reference_text = f" Referencia conocida: {reference}." if reference else ""
        return _prepend_summary(
            context,
            (
                "Responde en espanol claro, en una o dos frases cortas, con tono de control de acceso, sin repetir el contexto. "
                f"Solicita residente o autorizacion explicita antes de abrir.{reference_text}"
            ),
        )
    if context.next_step == "urgent_escalation":
        return _prepend_summary(
            context,
            (
                "Responde en espanol claro, en una o dos frases cortas, con tono calmo pero rapido. "
                "Indica que la situacion urgente debe ser derivada de inmediato."
            ),
        )
    if context.next_step == "clarify_resident":
        return _prepend_summary(
            context,
            (
                "Responde en espanol claro, en una o dos frases cortas, aptas para TTS, con tono de recepcion breve. "
                "Solicita de forma breve a que residente o departamento viene."
            ),
        )
    return _prepend_summary(
        context,
        (
            "Responde en espanol claro, en una o dos frases cortas, sin repetir el prompt. "
            "Solicita aclaracion breve del motivo de la visita."
        ),
    )

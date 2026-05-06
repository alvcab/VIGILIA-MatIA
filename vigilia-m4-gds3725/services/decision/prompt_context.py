from __future__ import annotations

from dataclasses import dataclass

from services.decision.intent import IntentExtraction


@dataclass(frozen=True)
class PromptContext:
    normalized_text: str
    resident_hint: str
    resident_display_name: str
    unit_hint: str
    visitor_intent: str
    next_step: str


def build_prompt_context(intent: IntentExtraction, visitor_intent: str, next_step: str) -> PromptContext:
    resident_display_name = ""
    if intent.resident_match is not None:
        resident_display_name = intent.resident_match.display_name
    elif intent.resident_hint:
        resident_display_name = intent.resident_hint

    return PromptContext(
        normalized_text=intent.normalized_text,
        resident_hint=intent.resident_hint,
        resident_display_name=resident_display_name,
        unit_hint=intent.unit_hint,
        visitor_intent=visitor_intent,
        next_step=next_step,
    )

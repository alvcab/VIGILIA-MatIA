from __future__ import annotations

from dataclasses import dataclass

from services.decision.intent import extract_intent
from services.decision.prompt_context import build_prompt_context
from services.decision.prompts import build_follow_up_prompt
from services.decision.resident_directory import ResidentDirectory
from services.decision.turn_state import TurnState


@dataclass(frozen=True)
class Decision:
    action: str
    should_open: bool
    reason: str
    confidence: str
    resident_hint: str = ""
    visitor_intent: str = "unknown"
    next_step: str = "complete"
    follow_up_prompt: str = ""
    turn_index: int = 1


def decide_from_text(text: str, resident_directory: ResidentDirectory | None = None) -> Decision:
    intent = extract_intent(text, resident_directory)

    if not intent.normalized_text:
        return Decision(
            action="ask_retry",
            should_open=False,
            reason="empty_text",
            confidence="high",
            visitor_intent="retry",
            next_step="ask_retry",
        )

    if intent.has_urgent_intent:
        next_step = "urgent_escalation"
        return Decision(
            action="escalate_urgent",
            should_open=False,
            reason="urgent_intent_detected",
            confidence="high",
            resident_hint=intent.resident_match.display_name if intent.resident_match else intent.resident_hint,
            visitor_intent="urgent",
            next_step=next_step,
            follow_up_prompt=build_follow_up_prompt(build_prompt_context(intent, "urgent", next_step)),
        )

    if intent.has_negative_or_reset_intent:
        return Decision(
            action="reset_interaction",
            should_open=False,
            reason="negative_or_reset_intent_detected",
            confidence="high",
            visitor_intent="reset",
            next_step="reset",
        )

    resolved_name = ""
    if intent.resident_match:
        resolved_name = intent.resident_match.display_name
    elif intent.resident_hint:
        resolved_name = intent.resident_hint
    elif intent.unit_hint:
        resolved_name = intent.unit_hint

    if intent.has_explicit_open:
        if not (intent.resident_match or intent.has_authorization_language):
            next_step = "clarify_authorization"
            return Decision(
                action="clarify_authorization",
                should_open=False,
                reason="open_request_without_resident_or_authorization",
                confidence="high",
                resident_hint=resolved_name,
                visitor_intent="access_request",
                next_step=next_step,
                follow_up_prompt=build_follow_up_prompt(
                    build_prompt_context(intent, "access_request", next_step)
                ),
            )
        if intent.resident_match and not intent.resident_match.allows_voice_open:
            next_step = "ask_resident_confirmation"
            return Decision(
                action="request_resident_confirmation",
                should_open=False,
                reason="resident_requires_confirmation",
                confidence="high",
                resident_hint=resolved_name,
                visitor_intent="access_request",
                next_step=next_step,
                follow_up_prompt=build_follow_up_prompt(
                    build_prompt_context(intent, "access_request", next_step)
                ),
                turn_index=2,
            )
        return Decision(
            action="open",
            should_open=True,
            reason="explicit_open_request",
            confidence="medium",
            resident_hint=resolved_name,
            visitor_intent="access_request",
        )

    if intent.has_delivery_intent and (intent.resident_hint or intent.unit_hint):
        if intent.resident_match and not intent.resident_match.accepts_delivery:
            next_step = "ask_delivery_recipient"
            return Decision(
                action="clarify_delivery_recipient",
                should_open=False,
                reason="resident_does_not_accept_delivery",
                confidence="high",
                resident_hint=resolved_name,
                visitor_intent="delivery",
                next_step=next_step,
                follow_up_prompt=build_follow_up_prompt(
                    build_prompt_context(intent, "delivery", next_step)
                ),
                turn_index=2,
            )
        return Decision(
            action="announce_delivery",
            should_open=False,
            reason="delivery_with_resident_hint",
            confidence="high",
            resident_hint=resolved_name,
            visitor_intent="delivery",
            next_step="notify_resident",
        )

    if intent.has_delivery_intent:
        next_step = "ask_delivery_recipient"
        return Decision(
            action="clarify_delivery_recipient",
            should_open=False,
            reason="delivery_without_resident_hint",
            confidence="high",
            visitor_intent="delivery",
            next_step=next_step,
            follow_up_prompt=build_follow_up_prompt(build_prompt_context(intent, "delivery", next_step)),
            turn_index=2,
        )

    if intent.resident_hint or intent.unit_hint:
        next_step = "ask_resident_confirmation" if intent.resident_match else "clarify_resident"
        return Decision(
            action="announce_resident",
            should_open=False,
            reason="resident_or_unit_hint_detected",
            confidence="high",
            resident_hint=resolved_name,
            visitor_intent="visit",
            next_step=next_step,
            follow_up_prompt=build_follow_up_prompt(build_prompt_context(intent, "visit", next_step)),
            turn_index=2 if intent.resident_match else 1,
        )

    if intent.has_greeting:
        return Decision(
            action="greet_and_clarify",
            should_open=False,
            reason="greeting_without_access_request",
            confidence="high",
            visitor_intent="greeting",
            next_step="clarify_resident",
            follow_up_prompt=build_follow_up_prompt(build_prompt_context(intent, "greeting", "clarify_resident")),
            turn_index=2,
        )

    return Decision(
        action="clarify_resident",
        should_open=False,
        reason="insufficient_context",
        confidence="medium",
        visitor_intent="unknown",
        next_step="clarify_resident",
        follow_up_prompt=build_follow_up_prompt(build_prompt_context(intent, "unknown", "clarify_resident")),
        turn_index=2,
    )

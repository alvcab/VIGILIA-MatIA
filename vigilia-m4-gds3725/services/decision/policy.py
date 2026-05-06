from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    action: str
    should_open: bool
    reason: str


def decide_from_text(text: str) -> Decision:
    normalized = " ".join(text.lower().split())

    if not normalized:
        return Decision(
            action="ask_retry",
            should_open=False,
            reason="empty_text",
        )

    if "abre" in normalized or "abrir" in normalized:
        return Decision(
            action="open",
            should_open=True,
            reason="explicit_open_request",
        )

    if "hola" in normalized or "buenas" in normalized:
        return Decision(
            action="greet_and_clarify",
            should_open=False,
            reason="greeting_without_access_request",
        )

    return Decision(
        action="clarify_resident",
        should_open=False,
        reason="insufficient_context",
    )

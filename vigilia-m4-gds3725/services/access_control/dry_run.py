from __future__ import annotations

from services.decision.policy import Decision


class DryRunGate:
    def handle(self, decision: Decision) -> dict[str, object]:
        return {
            "mode": "dry-run",
            "would_open": decision.should_open,
            "reason": decision.reason,
        }

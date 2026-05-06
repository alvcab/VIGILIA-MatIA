from __future__ import annotations

from dataclasses import asdict

from services.decision.model_backend import DecisionModelBackend, build_model_backend
from services.decision.policy import Decision, decide_from_text
from services.decision.resident_directory import ResidentDirectory


def evaluate_hybrid_decision(
    text: str,
    resident_directory: ResidentDirectory | None = None,
    model_backend_name: str = "stub",
    model_backend: DecisionModelBackend | None = None,
    ollama_model: str = "vigilia-mini",
    ollama_timeout_seconds: float = 8.0,
) -> dict[str, object]:
    decision = decide_from_text(text, resident_directory)
    resolved_backend = model_backend or build_model_backend(
        model_backend_name,
        ollama_model=ollama_model,
        ollama_timeout_seconds=ollama_timeout_seconds,
    )

    result: dict[str, object] = {
        "decision": asdict(decision),
        "rule_engine": {
            "applied": True,
            "reason": decision.reason,
            "confidence": decision.confidence,
        },
    }

    if decision.follow_up_prompt:
        generated = resolved_backend.generate_follow_up(decision.follow_up_prompt)
        result["model_guidance"] = {
            "enabled": True,
            "prompt": decision.follow_up_prompt,
            "next_step": decision.next_step,
            "turn_index": decision.turn_index,
            "backend": generated.backend,
            "generated_text": generated.generated_text,
        }
    else:
        result["model_guidance"] = {
            "enabled": False,
            "prompt": "",
            "next_step": decision.next_step,
            "turn_index": decision.turn_index,
            "backend": "",
            "generated_text": "",
        }

    return result

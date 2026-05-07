from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from services.decision.resident_directory import Resident, ResidentDirectory


def normalize_text(text: str) -> str:
    lowered = " ".join(text.lower().split())
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def extract_resident_hint(text: str) -> str:
    patterns = [
        r"(?:vengo donde|vengo a ver a|vengo a visitar a)\s+([a-z0-9]+(?:\s+[a-z0-9]+)?)",
        r"(?:donde)\s+([a-z0-9]+(?:\s+[a-z0-9]+)?)",
        r"(?:busco a|para)\s+([a-z0-9]+(?:\s+[a-z0-9]+)?)",
        r"(?:soy visita de)\s+([a-z0-9]+(?:\s+[a-z0-9]+)?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def extract_authorization_code(text: str) -> str:
    match = re.search(r"\b(\d{4})\b", text)
    if not match:
        return ""
    return match.group(1)


@dataclass(frozen=True)
class IntentExtraction:
    normalized_text: str
    resident_hint: str
    resident_match: Resident | None
    unit_hint: str
    has_delivery_intent: bool
    has_greeting: bool
    has_explicit_open: bool
    has_urgent_intent: bool
    has_negative_or_reset_intent: bool
    has_authorization_language: bool


def extract_unit_hint(text: str) -> str:
    patterns = [
        r"(?:casa|depto|departamento|unidad)\s+([a-z0-9]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return ""


def extract_intent(text: str, resident_directory: ResidentDirectory | None = None) -> IntentExtraction:
    normalized = normalize_text(text)
    resident_hint = extract_resident_hint(normalized)
    unit_hint = extract_unit_hint(normalized)
    resident_match = None

    if resident_directory:
        if resident_hint:
            resident_match = resident_directory.resolve(resident_hint) or resident_directory.resolve_partial(
                resident_hint
            )
        if resident_match is None and unit_hint:
            resident_match = resident_directory.resolve(unit_hint) or resident_directory.resolve_partial(unit_hint)
        if resident_match is None and not resident_hint and not unit_hint and normalized:
            resident_match = resident_directory.resolve(normalized) or resident_directory.resolve_partial(normalized)
            if resident_match is not None:
                resident_hint = normalized

    return IntentExtraction(
        normalized_text=normalized,
        resident_hint=resident_hint,
        resident_match=resident_match,
        unit_hint=unit_hint,
        has_delivery_intent=any(
            token in normalized
            for token in [
                "delivery",
                "paquete",
                "pedido",
                "encomienda",
                "rappi",
                "uber",
                "mercado libre",
            ]
        ),
        has_greeting=any(
            token in normalized
            for token in ["hola", "buenas", "buenos dias", "buenas tardes"]
        ),
        has_explicit_open=any(
            token in normalized
            for token in [
                "abre",
                "abrir",
                "abran",
                "abreme",
                "abra",
                "puedes abrir",
                "me abre",
            ]
        ),
        has_urgent_intent=any(
            token in normalized
            for token in ["ayuda", "auxilio", "emergencia", "urgente", "socorro"]
        ),
        has_negative_or_reset_intent=any(
            token in normalized
            for token in ["equivocado", "me confundi", "error", "no era", "olvide"]
        ),
        has_authorization_language=any(
            token in normalized
            for token in [
                "me autorizaron",
                "me estan esperando",
                "tengo autorizacion",
                "soy conocido",
            ]
        ),
    )

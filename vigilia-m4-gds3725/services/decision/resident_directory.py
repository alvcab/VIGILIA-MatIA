from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import unicodedata


def _normalize_value(value: str) -> str:
    lowered = " ".join(value.lower().split())
    normalized = unicodedata.normalize("NFKD", lowered)
    return "".join(char for char in normalized if not unicodedata.combining(char))


@dataclass(frozen=True)
class Resident:
    resident_id: str
    display_name: str
    unit: str
    aliases: tuple[str, ...]
    department_sip_uri: str = ""
    allows_voice_open: bool = False
    accepts_delivery: bool = True
    requires_resident_confirmation: bool = True


class ResidentDirectory:
    def __init__(self, residents: list[Resident]) -> None:
        self._residents = residents

    @property
    def residents(self) -> tuple[Resident, ...]:
        return tuple(self._residents)

    def get_by_id(self, resident_id: str) -> Resident | None:
        normalized_id = _normalize_value(resident_id)
        for resident in self._residents:
            if _normalize_value(resident.resident_id) == normalized_id:
                return resident
        return None

    def resolve(self, hint: str) -> Resident | None:
        normalized_hint = _normalize_value(hint)
        for resident in self._residents:
            for alias in resident.aliases:
                if normalized_hint == _normalize_value(alias):
                    return resident
        return None

    def resolve_partial(self, hint: str) -> Resident | None:
        normalized_hint = _normalize_value(hint)
        if not normalized_hint:
            return None

        for resident in self._residents:
            if normalized_hint in _normalize_value(resident.display_name):
                return resident
            if normalized_hint in _normalize_value(resident.unit):
                return resident
            for alias in resident.aliases:
                normalized_alias = _normalize_value(alias)
                if normalized_hint in normalized_alias or normalized_alias in normalized_hint:
                    return resident
        return None

    @classmethod
    def from_yaml_like_file(cls, path: str | Path) -> "ResidentDirectory":
        lines = Path(path).read_text(encoding="utf-8").splitlines()
        residents: list[Resident] = []
        current: dict[str, object] | None = None
        in_aliases = False

        for raw_line in lines:
            line = raw_line.rstrip()
            stripped = line.strip()

            if not stripped or stripped.startswith("#") or stripped == "residents:":
                continue

            if stripped.startswith("- id:"):
                if current:
                    residents.append(
                        Resident(
                            resident_id=str(current.get("id", "")),
                            display_name=str(current.get("display_name", current.get("id", ""))),
                            unit=str(current.get("unit", "")),
                            aliases=tuple(current.get("aliases", [])),
                            department_sip_uri=str(current.get("department_sip_uri", "")),
                            allows_voice_open=bool(current.get("allows_voice_open", False)),
                            accepts_delivery=bool(current.get("accepts_delivery", True)),
                            requires_resident_confirmation=bool(
                                current.get("requires_resident_confirmation", True)
                            ),
                        )
                    )
                current = {"id": stripped.split(":", 1)[1].strip(), "aliases": []}
                in_aliases = False
                continue

            if current is None:
                continue

            if stripped.startswith("display_name:"):
                current["display_name"] = stripped.split(":", 1)[1].strip()
                continue

            if stripped.startswith("unit:"):
                current["unit"] = stripped.split(":", 1)[1].strip()
                continue

            if stripped.startswith("department_sip_uri:"):
                current["department_sip_uri"] = stripped.split(":", 1)[1].strip()
                continue

            if stripped.startswith("aliases:"):
                in_aliases = True
                continue

            if stripped.startswith("allows_voice_open:"):
                current["allows_voice_open"] = stripped.split(":", 1)[1].strip().lower() == "true"
                continue

            if stripped.startswith("accepts_delivery:"):
                current["accepts_delivery"] = stripped.split(":", 1)[1].strip().lower() == "true"
                continue

            if stripped.startswith("requires_resident_confirmation:"):
                current["requires_resident_confirmation"] = (
                    stripped.split(":", 1)[1].strip().lower() == "true"
                )
                continue

            if in_aliases and stripped.startswith("- "):
                aliases = list(current.get("aliases", []))
                aliases.append(stripped[2:].strip())
                current["aliases"] = aliases

        if current:
            residents.append(
                Resident(
                    resident_id=str(current.get("id", "")),
                    display_name=str(current.get("display_name", current.get("id", ""))),
                    unit=str(current.get("unit", "")),
                    aliases=tuple(current.get("aliases", [])),
                    department_sip_uri=str(current.get("department_sip_uri", "")),
                    allows_voice_open=bool(current.get("allows_voice_open", False)),
                    accepts_delivery=bool(current.get("accepts_delivery", True)),
                    requires_resident_confirmation=bool(
                        current.get("requires_resident_confirmation", True)
                    ),
                )
            )

        return cls(residents)

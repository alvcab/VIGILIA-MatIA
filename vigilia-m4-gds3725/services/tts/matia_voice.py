from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class VoiceProfile:
    profile_id: str
    language: str
    tone: str
    speaking_rate: str
    delivery_mode: str


@dataclass(frozen=True)
class VoicePlan:
    audience: str
    profile: VoiceProfile
    text: str
    interruptible: bool

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["profile"] = asdict(self.profile)
        return payload


VISITOR_PROFILE = VoiceProfile(
    profile_id="matia-visitor-es-cl",
    language="es-CL",
    tone="calmado_y_breve",
    speaking_rate="normal",
    delivery_mode="tts_or_canned",
)

DEPARTMENT_PROFILE = VoiceProfile(
    profile_id="matia-department-es-cl",
    language="es-CL",
    tone="formal_y_claro",
    speaking_rate="normal",
    delivery_mode="tts_live",
)


def build_visitor_voice_plan(text: str, *, interruptible: bool = True) -> VoicePlan:
    return VoicePlan(
        audience="visitor",
        profile=VISITOR_PROFILE,
        text=text.strip(),
        interruptible=interruptible,
    )


def build_department_voice_plan(text: str, *, interruptible: bool = False) -> VoicePlan:
    return VoicePlan(
        audience="department",
        profile=DEPARTMENT_PROFILE,
        text=text.strip(),
        interruptible=interruptible,
    )

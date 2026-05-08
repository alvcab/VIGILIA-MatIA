from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re
import subprocess


@dataclass(frozen=True)
class ModelResponse:
    backend: str
    generated_text: str
    prompt_used: str


def _extract_known_reference(prompt: str) -> str:
    match = re.search(r"referencia conocida:\s*([^\.\n]+)", prompt, flags=re.IGNORECASE)
    if not match:
        return ""
    return " ".join(match.group(1).strip().split())


def _humanize_reference(reference: str) -> str:
    compact = " ".join(reference.strip().split())
    if not compact:
        return ""
    if compact == compact.lower():
        return " ".join(token.capitalize() for token in compact.split())
    return compact


def sanitize_follow_up_response(generated_text: str, *, prompt: str, fallback_text: str) -> str:
    normalized = " ".join(generated_text.strip().split())
    if not normalized:
        return fallback_text

    lowered = normalized.lower()
    prompt_lowered = " ".join(prompt.strip().split()).lower()
    if prompt_lowered and (lowered == prompt_lowered or lowered.startswith("contexto previo:") or lowered.startswith("[echo]")):
        return fallback_text

    if len(normalized) > 160:
        return fallback_text

    sentence_count = len(re.findall(r"[.!?]+", normalized))
    if sentence_count > 2:
        return fallback_text

    if "solicita" in lowered and "responde en espanol" in lowered:
        return fallback_text

    return normalized


class DecisionModelBackend(ABC):
    @abstractmethod
    def generate_follow_up(self, prompt: str) -> ModelResponse:
        raise NotImplementedError


class StubModelBackend(DecisionModelBackend):
    def generate_follow_up(self, prompt: str) -> ModelResponse:
        lowered = prompt.lower()
        known_reference = _humanize_reference(_extract_known_reference(prompt))
        if "no hubo match facial" in lowered:
            text = "No reconozco tu rostro. Dime a que residente o departamento vienes."
        elif "la visita dice que esta autorizada" in lowered or "la esperan" in lowered:
            if known_reference:
                if known_reference.lower().startswith(("depto", "departamento", "unidad", "casa")):
                    text = f"Indica si vienes al {known_reference} o quien autorizo tu ingreso."
                else:
                    text = f"Indica si vienes donde {known_reference} o quien autorizo tu ingreso."
            else:
                text = "Indica que residente o departamento autorizo tu ingreso."
        elif "confirmacion breve" in lowered:
            if known_reference:
                text = f"Un momento. Voy a confirmar con {known_reference}."
            else:
                text = "Un momento. Voy a confirmar con el residente."
        elif "tono practico para una entrega" in lowered:
            text = "Indica para que residente o departamento es la entrega."
        elif "tono de control de acceso" in lowered:
            if known_reference:
                if known_reference.lower().startswith(("depto", "departamento", "unidad", "casa")):
                    text = f"Indica si vienes al {known_reference} o quien autorizo tu ingreso."
                else:
                    text = f"Indica si vienes donde {known_reference} o quien autorizo tu ingreso."
            else:
                text = "Indica a que residente vienes a ver o quien autorizo tu ingreso."
        elif "autorizacion explicita" in lowered:
            text = "Indica a que residente vienes a ver o quien autorizo tu ingreso."
        elif "tono calmo pero rapido" in lowered:
            text = "Entendido. Voy a derivar la situacion urgente de inmediato."
        elif "tono de recepcion breve" in lowered:
            text = "Hola. Dime a que residente o departamento vienes."
        else:
            text = "Necesito un poco mas de informacion para continuar."

        return ModelResponse(
            backend="stub-model",
            generated_text=text,
            prompt_used=prompt,
        )


class EchoModelBackend(DecisionModelBackend):
    def generate_follow_up(self, prompt: str) -> ModelResponse:
        return ModelResponse(
            backend="echo-model",
            generated_text=f"[echo] {prompt}",
            prompt_used=prompt,
        )


class OllamaModelBackend(DecisionModelBackend):
    def __init__(self, model_name: str, timeout_seconds: float = 8.0) -> None:
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._fallback = StubModelBackend()

    def generate_follow_up(self, prompt: str) -> ModelResponse:
        try:
            result = subprocess.run(
                ["ollama", "run", self._model_name, prompt],
                capture_output=True,
                text=True,
                check=False,
                timeout=self._timeout_seconds,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            fallback_response = self._fallback.generate_follow_up(prompt)
            return ModelResponse(
                backend="ollama-fallback-stub",
                generated_text=fallback_response.generated_text,
                prompt_used=prompt,
            )

        output = (result.stdout or "").strip()
        if result.returncode != 0 or not output:
            fallback_response = self._fallback.generate_follow_up(prompt)
            return ModelResponse(
                backend="ollama-fallback-stub",
                generated_text=fallback_response.generated_text,
                prompt_used=prompt,
            )

        return ModelResponse(
            backend=f"ollama:{self._model_name}",
            generated_text=output,
            prompt_used=prompt,
        )


def build_model_backend(
    backend_name: str,
    *,
    ollama_model: str = "vigilia-mini",
    ollama_timeout_seconds: float = 8.0,
) -> DecisionModelBackend:
    normalized = backend_name.strip().lower()
    if normalized == "echo":
        return EchoModelBackend()
    if normalized == "ollama":
        return OllamaModelBackend(
            model_name=ollama_model,
            timeout_seconds=ollama_timeout_seconds,
        )
    return StubModelBackend()

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import subprocess


@dataclass(frozen=True)
class ModelResponse:
    backend: str
    generated_text: str
    prompt_used: str


class DecisionModelBackend(ABC):
    @abstractmethod
    def generate_follow_up(self, prompt: str) -> ModelResponse:
        raise NotImplementedError


class StubModelBackend(DecisionModelBackend):
    def generate_follow_up(self, prompt: str) -> ModelResponse:
        lowered = prompt.lower()
        if "no hubo match facial" in lowered:
            text = "No reconozco tu rostro. Indica a que residente o departamento vienes."
        elif "dic e que esta autorizada" in lowered or "la visita dice que esta autorizada" in lowered or "la esperan" in lowered:
            text = "Indica que residente o departamento autorizo tu ingreso."
        elif "confirmacion breve" in lowered:
            text = "Voy a confirmar con el residente antes de autorizar el ingreso."
        elif "entrega" in lowered:
            text = "Necesito que indiques para que residente o departamento es la entrega."
        elif "autorizacion explicita" in lowered:
            text = "Indica a que residente vienes a ver o que departamento autorizo tu ingreso."
        elif "urgente" in lowered:
            text = "Entendido. Voy a derivar la situacion urgente de inmediato."
        elif "residente o departamento viene" in lowered:
            text = "Indica a que residente o departamento vienes."
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

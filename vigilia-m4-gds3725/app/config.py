from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    environment: str = "development"
    default_mode: str = "dry-run"
    runtime_dir: str = "runtime"
    log_level: str = "INFO"
    residents_path: str = "config/residents.example.yaml"
    model_backend: str = "stub"
    transcription_backend: str = "sidecar"
    whisper_model: str = "tiny"
    ollama_model: str = "vigilia-mini"
    ollama_timeout_seconds: float = 8.0


def load_config() -> AppConfig:
    return AppConfig(
        environment=os.getenv("VIGILIA_ENV", "development"),
        default_mode=os.getenv("VIGILIA_MODE", "dry-run"),
        runtime_dir=os.getenv("VIGILIA_RUNTIME_DIR", "runtime"),
        log_level=os.getenv("VIGILIA_LOG_LEVEL", "INFO"),
        residents_path=os.getenv("VIGILIA_RESIDENTS_PATH", "config/residents.example.yaml"),
        model_backend=os.getenv("VIGILIA_MODEL_BACKEND", "stub"),
        transcription_backend=os.getenv("VIGILIA_TRANSCRIPTION_BACKEND", "sidecar"),
        whisper_model=os.getenv("VIGILIA_WHISPER_MODEL", "tiny"),
        ollama_model=os.getenv("VIGILIA_OLLAMA_MODEL", "vigilia-mini"),
        ollama_timeout_seconds=float(os.getenv("VIGILIA_OLLAMA_TIMEOUT_SECONDS", "8")),
    )


def resolve_repo_path(relative_or_absolute_path: str) -> Path:
    candidate = Path(relative_or_absolute_path)
    if candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parents[1] / candidate

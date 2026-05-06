from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    environment: str = "development"
    default_mode: str = "dry-run"
    runtime_dir: str = "runtime"
    log_level: str = "INFO"


def load_config() -> AppConfig:
    return AppConfig(
        environment=os.getenv("VIGILIA_ENV", "development"),
        default_mode=os.getenv("VIGILIA_MODE", "dry-run"),
        runtime_dir=os.getenv("VIGILIA_RUNTIME_DIR", "runtime"),
        log_level=os.getenv("VIGILIA_LOG_LEVEL", "INFO"),
    )

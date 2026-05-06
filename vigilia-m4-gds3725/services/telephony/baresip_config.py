from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BaresipConfig:
    binary: str
    config_path: str
    accounts_path: str
    audio_path: str
    workdir: str

    @classmethod
    def from_env(cls) -> "BaresipConfig":
        return cls(
            binary=os.getenv("VIGILIA_BARESIP_BINARY", "baresip"),
            config_path=os.getenv("VIGILIA_BARESIP_CONFIG_PATH", "runtime/baresip/config"),
            accounts_path=os.getenv("VIGILIA_BARESIP_ACCOUNTS_PATH", "runtime/baresip/accounts"),
            audio_path=os.getenv("VIGILIA_BARESIP_AUDIO_PATH", "runtime/baresip/audio"),
            workdir=os.getenv("VIGILIA_BARESIP_WORKDIR", "runtime/baresip"),
        )

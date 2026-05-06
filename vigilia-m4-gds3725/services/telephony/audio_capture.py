from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioCapture:
    source_path: str
    format: str
    transport: str

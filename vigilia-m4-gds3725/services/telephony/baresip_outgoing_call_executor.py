from __future__ import annotations

from dataclasses import dataclass

from services.telephony.baresip_config import BaresipConfig


@dataclass(frozen=True)
class BaresipOutgoingCallExecution:
    binary: str
    config_path: str
    target_uri: str
    reply_audio_path: str
    reply_audio_metadata_path: str
    startup_command: list[str]
    dial_command: str
    hangup_command: str
    quit_command: str

    def as_dict(self) -> dict[str, object]:
        return {
            "binary": self.binary,
            "config_path": self.config_path,
            "target_uri": self.target_uri,
            "reply_audio_capture": {
                "audio_file": self.reply_audio_path,
                "metadata_file": self.reply_audio_metadata_path,
            },
            "startup_command": list(self.startup_command),
            "dial_command": self.dial_command,
            "hangup_command": self.hangup_command,
            "quit_command": self.quit_command,
            "stdin_sequence": [
                self.dial_command,
                self.hangup_command,
                self.quit_command,
            ],
        }


class BaresipOutgoingCallExecutor:
    def __init__(self, config: BaresipConfig | None = None) -> None:
        self._config = config or BaresipConfig.from_env()

    def build_execution(
        self,
        target_uri: str,
        *,
        reply_audio_path: str = "",
        reply_audio_metadata_path: str = "",
    ) -> BaresipOutgoingCallExecution:
        normalized_target = target_uri.strip()
        return BaresipOutgoingCallExecution(
            binary=self._config.binary,
            config_path=self._config.config_path,
            target_uri=normalized_target,
            reply_audio_path=reply_audio_path,
            reply_audio_metadata_path=reply_audio_metadata_path,
            startup_command=[self._config.binary, "-f", self._config.config_path],
            dial_command=f"/dial {normalized_target}",
            hangup_command="/hangup",
            quit_command="/quit",
        )

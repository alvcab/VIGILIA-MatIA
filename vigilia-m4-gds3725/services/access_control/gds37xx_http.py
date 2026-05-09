from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import HTTPBasicAuthHandler, HTTPPasswordMgrWithDefaultRealm, build_opener

from services.decision.policy import Decision


@dataclass(frozen=True)
class Gds37xxHttpGateConfig:
    base_url: str
    username: str
    password: str
    remote_pin: str
    open_type: int = 1
    timeout_seconds: float = 5.0

    @classmethod
    def from_env(cls) -> "Gds37xxHttpGateConfig":
        return cls(
            base_url=os.getenv("VIGILIA_GDS_BASE_URL", "").rstrip("/"),
            username=os.getenv("VIGILIA_GDS_USERNAME", ""),
            password=os.getenv("VIGILIA_GDS_PASSWORD", ""),
            remote_pin=os.getenv("VIGILIA_GDS_REMOTE_PIN", ""),
            open_type=int(os.getenv("VIGILIA_GDS_OPEN_TYPE", "1")),
            timeout_seconds=float(os.getenv("VIGILIA_GDS_TIMEOUT_SECONDS", "5")),
        )


class Gds37xxHttpGate:
    def __init__(self, config: Gds37xxHttpGateConfig | None = None) -> None:
        self._config = config or Gds37xxHttpGateConfig.from_env()

    def build_open_url(self) -> str:
        self._validate_config()
        query = urlencode(
            {
                "remotepin": self._config.remote_pin,
                "type": str(self._config.open_type),
            }
        )
        return f"{self._config.base_url}/goform/apicmd?{query}"

    def handle(self, decision: Decision) -> dict[str, object]:
        if not decision.should_open:
            return {
                "mode": "gds37xx-http",
                "opened": False,
                "reason": decision.reason,
                "skipped": "decision_did_not_authorize_open",
            }

        url = self.build_open_url()
        password_manager = HTTPPasswordMgrWithDefaultRealm()
        password_manager.add_password(
            None,
            self._config.base_url,
            self._config.username,
            self._config.password,
        )
        opener = build_opener(HTTPBasicAuthHandler(password_manager))

        try:
            with opener.open(url, timeout=self._config.timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace")
        except URLError as exc:
            return {
                "mode": "gds37xx-http",
                "opened": False,
                "reason": decision.reason,
                "error": str(exc),
            }

        return {
            "mode": "gds37xx-http",
            "opened": "<ResCode>0</ResCode>" in body,
            "reason": decision.reason,
            "response_body": body,
        }

    def _validate_config(self) -> None:
        missing = [
            name
            for name, value in (
                ("VIGILIA_GDS_BASE_URL", self._config.base_url),
                ("VIGILIA_GDS_USERNAME", self._config.username),
                ("VIGILIA_GDS_PASSWORD", self._config.password),
                ("VIGILIA_GDS_REMOTE_PIN", self._config.remote_pin),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing GDS37xx HTTP gate config: {', '.join(missing)}")

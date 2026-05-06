from __future__ import annotations

from abc import ABC, abstractmethod


class SipTransport(ABC):
    @abstractmethod
    def register(self, local_uri: str) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def invite(self, caller_id: str, from_uri: str, to_uri: str) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def accept(self, call_id: str) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def hangup(self, call_id: str) -> dict[str, object]:
        raise NotImplementedError

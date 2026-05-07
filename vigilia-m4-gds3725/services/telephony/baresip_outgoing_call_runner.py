from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Protocol


class BaresipProcessLike(Protocol):
    stdin: object | None

    def communicate(self, input: str | None = None, timeout: float | None = None) -> tuple[str, str]:
        ...

    def poll(self) -> int | None:
        ...


class BaresipProcessFactory(Protocol):
    def __call__(self, command: list[str]) -> BaresipProcessLike:
        ...


def _default_process_factory(command: list[str]) -> BaresipProcessLike:
    return subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


@dataclass(frozen=True)
class BaresipOutgoingCallRunResult:
    mode: str
    started: bool
    startup_command: list[str]
    stdin_sequence: list[str]
    exit_code: int | None
    stdout: str
    stderr: str

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "started": self.started,
            "startup_command": list(self.startup_command),
            "stdin_sequence": list(self.stdin_sequence),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


class BaresipOutgoingCallRunner:
    def __init__(self, process_factory: BaresipProcessFactory | None = None) -> None:
        self._process_factory = process_factory or _default_process_factory

    def run_preview(
        self,
        execution_preview: dict[str, object],
        *,
        dry_run: bool = True,
        timeout_seconds: float = 5.0,
    ) -> BaresipOutgoingCallRunResult:
        startup_command = [str(part) for part in execution_preview.get("startup_command", [])]
        stdin_sequence = [str(part) for part in execution_preview.get("stdin_sequence", [])]

        if dry_run:
            return BaresipOutgoingCallRunResult(
                mode="dry-run",
                started=False,
                startup_command=startup_command,
                stdin_sequence=stdin_sequence,
                exit_code=None,
                stdout="",
                stderr="",
            )

        process = self._process_factory(startup_command)
        stdin_payload = "".join(f"{line}\n" for line in stdin_sequence)
        stdout, stderr = process.communicate(input=stdin_payload, timeout=timeout_seconds)

        return BaresipOutgoingCallRunResult(
            mode="executed",
            started=True,
            startup_command=startup_command,
            stdin_sequence=stdin_sequence,
            exit_code=process.poll(),
            stdout=stdout,
            stderr=stderr,
        )

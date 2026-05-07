from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Protocol


class BaresipStdinLike(Protocol):
    def write(self, data: str) -> object:
        ...

    def flush(self) -> object:
        ...


class BaresipProcessLike(Protocol):
    stdin: BaresipStdinLike | None

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


@dataclass
class BaresipOutgoingCallSession:
    session_id: str
    startup_command: list[str]
    target_uri: str
    dry_run: bool
    process: BaresipProcessLike | None = None
    sent_commands: list[str] = field(default_factory=list)
    started: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "startup_command": list(self.startup_command),
            "target_uri": self.target_uri,
            "dry_run": self.dry_run,
            "started": self.started,
            "sent_commands": list(self.sent_commands),
        }


class BaresipOutgoingCallRunner:
    def __init__(self, process_factory: BaresipProcessFactory | None = None) -> None:
        self._process_factory = process_factory or _default_process_factory
        self._sessions: dict[str, BaresipOutgoingCallSession] = {}

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

    def start_session(
        self,
        session_id: str,
        execution_preview: dict[str, object],
        *,
        dry_run: bool = True,
    ) -> BaresipOutgoingCallSession:
        startup_command = [str(part) for part in execution_preview.get("startup_command", [])]
        target_uri = str(execution_preview.get("target_uri", ""))
        dial_command = str(execution_preview.get("dial_command", ""))

        session = BaresipOutgoingCallSession(
            session_id=session_id,
            startup_command=startup_command,
            target_uri=target_uri,
            dry_run=dry_run,
        )

        if dry_run:
            session.started = True
            session.sent_commands.append(dial_command)
            self._sessions[session_id] = session
            return session

        process = self._process_factory(startup_command)
        session.process = process
        session.started = True
        self._send_command(session, dial_command)
        self._sessions[session_id] = session
        return session

    def send_command(self, session_id: str, command: str) -> BaresipOutgoingCallSession:
        session = self._sessions[session_id]
        self._send_command(session, command)
        return session

    def finish_session(
        self,
        session_id: str,
        *,
        hangup_command: str = "/hangup",
        quit_command: str = "/quit",
        timeout_seconds: float = 5.0,
    ) -> BaresipOutgoingCallRunResult:
        session = self._sessions.pop(session_id)

        if session.dry_run:
            session.sent_commands.extend([hangup_command, quit_command])
            return BaresipOutgoingCallRunResult(
                mode="dry-run-session",
                started=session.started,
                startup_command=session.startup_command,
                stdin_sequence=session.sent_commands,
                exit_code=None,
                stdout="",
                stderr="",
            )

        self._send_command(session, hangup_command)
        self._send_command(session, quit_command)
        stdout, stderr = session.process.communicate(timeout=timeout_seconds) if session.process else ("", "")
        exit_code = session.process.poll() if session.process else None
        return BaresipOutgoingCallRunResult(
            mode="executed-session",
            started=session.started,
            startup_command=session.startup_command,
            stdin_sequence=session.sent_commands,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
        )

    def get_session(self, session_id: str) -> BaresipOutgoingCallSession | None:
        return self._sessions.get(session_id)

    def _send_command(self, session: BaresipOutgoingCallSession, command: str) -> None:
        normalized_command = command.strip()
        if not normalized_command:
            return

        session.sent_commands.append(normalized_command)
        if session.dry_run:
            return

        if session.process is None or session.process.stdin is None:
            raise RuntimeError("baresip process stdin is not available")

        session.process.stdin.write(f"{normalized_command}\n")
        session.process.stdin.flush()

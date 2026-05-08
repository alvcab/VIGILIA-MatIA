from __future__ import annotations

import unittest

from services.telephony.baresip_outgoing_call_runner import BaresipOutgoingCallRunner


class _FakeProcess:
    def __init__(self, expected_command: list[str]) -> None:
        self.expected_command = expected_command
        self.stdin = self
        self._captured_input = ""
        self._writes: list[str] = []

    def write(self, data: str) -> None:
        self._writes.append(data)

    def flush(self) -> None:
        return None

    def communicate(self, input: str | None = None, timeout: float | None = None) -> tuple[str, str]:
        self._captured_input = input or ""
        return ("ok", "")

    def poll(self) -> int | None:
        return 0


class BaresipOutgoingCallRunnerTests(unittest.TestCase):
    def test_run_preview_returns_dry_run_result_by_default(self) -> None:
        runner = BaresipOutgoingCallRunner()
        result = runner.run_preview(
            {
                "startup_command": ["baresip", "-f", "runtime/baresip/config"],
                "stdin_sequence": ["/dial sip:depto1@192.168.100.71:5060;transport=udp", "/hangup", "/quit"],
            }
        ).as_dict()

        self.assertEqual(result["mode"], "dry-run")
        self.assertFalse(result["started"])
        self.assertIsNone(result["exit_code"])

    def test_run_preview_can_execute_with_process_factory(self) -> None:
        captured: dict[str, object] = {}

        def factory(command: list[str]) -> _FakeProcess:
            captured["command"] = list(command)
            process = _FakeProcess(command)
            captured["process"] = process
            return process

        runner = BaresipOutgoingCallRunner(process_factory=factory)
        result = runner.run_preview(
            {
                "startup_command": ["baresip", "-f", "runtime/baresip/config"],
                "stdin_sequence": ["/dial sip:depto1@192.168.100.71:5060;transport=udp", "/hangup", "/quit"],
            },
            dry_run=False,
        ).as_dict()

        self.assertEqual(result["mode"], "executed")
        self.assertTrue(result["started"])
        self.assertEqual(captured["command"], ["baresip", "-f", "runtime/baresip/config"])
        self.assertEqual(
            captured["process"]._captured_input,  # type: ignore[attr-defined]
            "/dial sip:depto1@192.168.100.71:5060;transport=udp\n/hangup\n/quit\n",
        )
        self.assertEqual(result["stdout"], "ok")

    def test_session_lifecycle_can_start_and_finish_in_dry_run(self) -> None:
        runner = BaresipOutgoingCallRunner()
        started = runner.start_session(
            "session-1",
            {
                "startup_command": ["baresip", "-f", "runtime/baresip/config"],
                "target_uri": "sip:depto1@192.168.100.71:5060;transport=udp",
                "reply_audio_capture": {
                    "audio_file": "runtime/baresip/matia_call_service/reply_audio_inbox/session-1.wav",
                    "metadata_file": "runtime/baresip/matia_call_service/reply_audio_inbox/session-1.json",
                },
                "dial_command": "/dial sip:depto1@192.168.100.71:5060;transport=udp",
            },
            dry_run=True,
        )
        commands_after_start = list(started.sent_commands)
        finished = runner.finish_session("session-1").as_dict()

        self.assertTrue(started.started)
        self.assertEqual(
            started.reply_audio_path,
            "runtime/baresip/matia_call_service/reply_audio_inbox/session-1.wav",
        )
        self.assertEqual(commands_after_start, ["/dial sip:depto1@192.168.100.71:5060;transport=udp"])
        self.assertEqual(finished["mode"], "dry-run-session")
        self.assertEqual(
            finished["stdin_sequence"],
            ["/dial sip:depto1@192.168.100.71:5060;transport=udp", "/hangup", "/quit"],
        )

    def test_session_lifecycle_can_start_and_finish_with_process_factory(self) -> None:
        captured: dict[str, object] = {}

        def factory(command: list[str]) -> _FakeProcess:
            captured["command"] = list(command)
            process = _FakeProcess(command)
            captured["process"] = process
            return process

        runner = BaresipOutgoingCallRunner(process_factory=factory)
        started = runner.start_session(
            "session-2",
            {
                "startup_command": ["baresip", "-f", "runtime/baresip/config"],
                "target_uri": "sip:depto1@192.168.100.71:5060;transport=udp",
                "reply_audio_capture": {
                    "audio_file": "runtime/baresip/matia_call_service/reply_audio_inbox/session-2.wav",
                    "metadata_file": "runtime/baresip/matia_call_service/reply_audio_inbox/session-2.json",
                },
                "dial_command": "/dial sip:depto1@192.168.100.71:5060;transport=udp",
            },
            dry_run=False,
        )
        finished = runner.finish_session("session-2").as_dict()

        self.assertTrue(started.started)
        self.assertEqual(
            started.reply_audio_metadata_path,
            "runtime/baresip/matia_call_service/reply_audio_inbox/session-2.json",
        )
        self.assertEqual(
            captured["process"]._writes,  # type: ignore[attr-defined]
            [
                "/dial sip:depto1@192.168.100.71:5060;transport=udp\n",
                "/hangup\n",
                "/quit\n",
            ],
        )
        self.assertEqual(finished["mode"], "executed-session")
        self.assertEqual(finished["stdout"], "ok")


if __name__ == "__main__":
    unittest.main()

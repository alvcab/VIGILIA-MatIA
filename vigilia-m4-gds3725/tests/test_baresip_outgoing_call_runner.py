from __future__ import annotations

import unittest

from services.telephony.baresip_outgoing_call_runner import BaresipOutgoingCallRunner


class _FakeProcess:
    def __init__(self, expected_command: list[str]) -> None:
        self.expected_command = expected_command
        self.stdin = object()
        self._captured_input = ""

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


if __name__ == "__main__":
    unittest.main()

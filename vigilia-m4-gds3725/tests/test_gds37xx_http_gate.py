import unittest
from unittest.mock import MagicMock, patch

from services.access_control.gds37xx_http import Gds37xxHttpGate, Gds37xxHttpGateConfig
from services.decision.policy import Decision


class Gds37xxHttpGateTests(unittest.TestCase):
    def test_build_open_url_uses_remote_pin_and_open_type(self) -> None:
        gate = Gds37xxHttpGate(
            Gds37xxHttpGateConfig(
                base_url="http://192.168.100.245",
                username="admin",
                password="secret",
                remote_pin="1234",
                open_type=1,
            )
        )

        self.assertEqual(
            gate.build_open_url(),
            "http://192.168.100.245/goform/apicmd?remotepin=1234&type=1",
        )

    def test_handle_skips_when_decision_does_not_authorize_open(self) -> None:
        gate = Gds37xxHttpGate(
            Gds37xxHttpGateConfig(
                base_url="http://192.168.100.245",
                username="admin",
                password="secret",
                remote_pin="1234",
            )
        )
        decision = Decision(
            action="deny_access",
            should_open=False,
            reason="department_denied_access",
            confidence="high",
        )

        result = gate.handle(decision)

        self.assertFalse(result["opened"])
        self.assertEqual(result["skipped"], "decision_did_not_authorize_open")

    def test_handle_opens_when_device_returns_success(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"<ResCode>0</ResCode>"
        opener = MagicMock()
        opener.open.return_value = response
        decision = Decision(
            action="open",
            should_open=True,
            reason="department_authorized_access",
            confidence="high",
        )

        with patch("services.access_control.gds37xx_http.build_opener", return_value=opener):
            result = Gds37xxHttpGate(
                Gds37xxHttpGateConfig(
                    base_url="http://192.168.100.245",
                    username="admin",
                    password="secret",
                    remote_pin="1234",
                )
            ).handle(decision)

        self.assertTrue(result["opened"])
        opener.open.assert_called_once_with(
            "http://192.168.100.245/goform/apicmd?remotepin=1234&type=1",
            timeout=5.0,
        )


if __name__ == "__main__":
    unittest.main()

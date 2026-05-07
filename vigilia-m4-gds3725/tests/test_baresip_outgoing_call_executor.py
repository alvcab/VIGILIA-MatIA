import unittest

from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_outgoing_call_executor import BaresipOutgoingCallExecutor


class BaresipOutgoingCallExecutorTests(unittest.TestCase):
    def test_build_execution_creates_interactive_baresip_sequence(self) -> None:
        executor = BaresipOutgoingCallExecutor(
            BaresipConfig(
                binary="baresip",
                config_path="runtime/baresip/config",
                accounts_path="runtime/baresip/accounts",
                audio_path="runtime/baresip/audio",
                workdir="runtime/baresip",
            )
        )

        execution = executor.build_execution("sip:depto1@192.168.100.71:5060;transport=udp").as_dict()

        self.assertEqual(execution["startup_command"], ["baresip", "-f", "runtime/baresip/config"])
        self.assertEqual(execution["dial_command"], "/dial sip:depto1@192.168.100.71:5060;transport=udp")
        self.assertEqual(execution["hangup_command"], "/hangup")
        self.assertEqual(execution["quit_command"], "/quit")
        self.assertEqual(
            execution["stdin_sequence"],
            [
                "/dial sip:depto1@192.168.100.71:5060;transport=udp",
                "/hangup",
                "/quit",
            ],
        )


if __name__ == "__main__":
    unittest.main()

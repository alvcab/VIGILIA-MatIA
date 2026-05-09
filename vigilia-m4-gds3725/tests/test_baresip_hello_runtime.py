import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.telephony.baresip_hello_runtime import BaresipHelloRuntimeBuilder, BaresipHelloRuntimeConfig


class BaresipHelloRuntimeBuilderTests(unittest.TestCase):
    def test_prepare_writes_auto_answer_config_and_account(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config = BaresipHelloRuntimeConfig(
                workdir=Path(tmpdir) / "runtime" / "baresip-hello",
                local_user="door",
                local_domain="192.168.100.234",
                local_port=5060,
                module_path="/tmp/modules",
            )

            with patch("services.telephony.baresip_hello_runtime.subprocess.run") as run:
                result = BaresipHelloRuntimeBuilder(config).prepare()

            account_text = Path(result["accounts_path"]).read_text(encoding="utf-8")
            config_text = Path(result["config_path"]).read_text(encoding="utf-8")

        self.assertIn("<sip:door@192.168.100.234:5060;transport=udp>", account_text)
        self.assertIn("answermode=auto", account_text)
        self.assertIn("audio_source=aufile,", account_text)
        self.assertIn("sip_listen 192.168.100.234:5060", config_text)
        self.assertIn("module_path /tmp/modules", config_text)
        self.assertEqual(result["listen_uri"], "sip:door@192.168.100.234:5060")
        self.assertEqual(result["gds_call_target"], "door@192.168.100.234")
        self.assertEqual(result["captured_audio_file"], str(config.workdir / "gds-rx.wav"))
        self.assertEqual(result["process_capture_command"], ["python3", "-m", "app.main", "--mode", "gds-capture-process"])
        self.assertEqual(result["run_command"][0:3], ["baresip", "-s", "-f"])
        self.assertEqual(run.call_count, 2)

    def test_from_env_uses_detected_lan_ip_when_no_domain_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict("os.environ", {}, clear=True), patch(
                "services.telephony.baresip_hello_runtime.detect_lan_ip",
                return_value="192.168.100.234",
            ):
                config = BaresipHelloRuntimeConfig.from_env(Path(tmpdir) / "runtime")

        self.assertEqual(config.local_user, "door")
        self.assertEqual(config.local_domain, "192.168.100.234")
        self.assertEqual(config.local_port, 5060)

    def test_detect_lan_ip_prefers_private_ifconfig_address(self) -> None:
        from services.telephony import baresip_hello_runtime

        ifconfig_output = """
lo0: flags=8049<UP,LOOPBACK,RUNNING,MULTICAST>
    inet 127.0.0.1 netmask 0xff000000
en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST>
    inet 192.168.100.234 netmask 0xffffff00 broadcast 192.168.100.255
"""
        socket_instance = patch("services.telephony.baresip_hello_runtime.socket.socket").start().return_value.__enter__.return_value
        socket_instance.getsockname.return_value = ("127.0.0.1", 12345)
        completed = type("Completed", (), {"stdout": ifconfig_output})()

        try:
            with patch("services.telephony.baresip_hello_runtime.subprocess.run", return_value=completed):
                self.assertEqual(baresip_hello_runtime.detect_lan_ip(), "192.168.100.234")
        finally:
            patch.stopall()


if __name__ == "__main__":
    unittest.main()

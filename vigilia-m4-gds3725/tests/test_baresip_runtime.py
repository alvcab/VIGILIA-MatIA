import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_runtime import BaresipRuntimeBuilder
from services.telephony.sip_config import SipEndpointConfig


class BaresipRuntimeBuilderTests(unittest.TestCase):
    def test_prepare_writes_config_and_accounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "runtime" / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            sip = SipEndpointConfig(
                device_label="gds3725",
                local_user="vigilia",
                local_domain="192.168.1.10",
                local_port=5062,
                transport="udp",
                device_user="door",
                device_domain="192.168.1.20",
                device_port=5060,
            )

            result = BaresipRuntimeBuilder(config, sip).prepare()

            self.assertTrue(Path(result["config_path"]).exists())
            self.assertTrue(Path(result["accounts_path"]).exists())
            self.assertTrue(Path(result["department_requests_path"]).exists())
            self.assertTrue(Path(result["department_responses_path"]).exists())
            self.assertTrue(Path(result["department_processed_path"]).exists())
            self.assertEqual(
                result["account_line"],
                "<sip:vigilia@192.168.1.10:5062;transport=udp>;regint=0",
            )

    def test_sip_config_reads_runtime_values_from_env(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "VIGILIA_SIP_DEVICE_LABEL": "front-gds",
                "VIGILIA_SIP_LOCAL_USER": "matia",
                "VIGILIA_SIP_LOCAL_DOMAIN": "192.168.100.100",
                "VIGILIA_SIP_LOCAL_PORT": "5070",
                "VIGILIA_SIP_TRANSPORT": "tcp",
                "VIGILIA_SIP_DEVICE_USER": "door-main",
                "VIGILIA_SIP_DEVICE_DOMAIN": "192.168.100.60",
                "VIGILIA_SIP_DEVICE_PORT": "5064",
            },
        ):
            config = SipEndpointConfig.from_env()

        self.assertEqual(config.device_label, "front-gds")
        self.assertEqual(config.local_user, "matia")
        self.assertEqual(config.local_domain, "192.168.100.100")
        self.assertEqual(config.local_port, 5070)
        self.assertEqual(config.transport, "tcp")
        self.assertEqual(config.device_user, "door-main")
        self.assertEqual(config.device_domain, "192.168.100.60")
        self.assertEqual(config.device_port, 5064)


if __name__ == "__main__":
    unittest.main()

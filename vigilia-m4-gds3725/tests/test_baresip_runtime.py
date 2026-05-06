import tempfile
import unittest
from pathlib import Path

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
            self.assertEqual(
                result["account_line"],
                "<sip:vigilia@192.168.1.10:5062;transport=udp>;regint=0",
            )


if __name__ == "__main__":
    unittest.main()

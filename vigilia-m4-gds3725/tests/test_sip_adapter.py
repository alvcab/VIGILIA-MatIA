import unittest

from services.telephony.sip_adapter import SipAdapter
from services.telephony.sip_config import SipEndpointConfig


class SipAdapterTests(unittest.TestCase):
    def test_build_preview_contains_local_and_device_uris(self) -> None:
        adapter = SipAdapter(
            SipEndpointConfig(
                device_label="gds3725",
                local_user="vigilia",
                local_domain="192.168.1.10",
                local_port=5062,
                transport="udp",
                device_user="door",
                device_domain="192.168.1.20",
                device_port=5060,
            )
        )

        result = adapter.build_preview("gds-front-door")

        self.assertEqual(result["mode"], "sip-preview")
        self.assertEqual(
            result["local_endpoint"]["uri"],
            "sip:vigilia@192.168.1.10:5062;transport=udp",
        )
        self.assertEqual(
            result["device_endpoint"]["uri"],
            "sip:door@192.168.1.20:5060;transport=udp",
        )

    def test_simulate_session_returns_full_lifecycle(self) -> None:
        adapter = SipAdapter(
            SipEndpointConfig(
                device_label="gds3725",
                local_user="vigilia",
                local_domain="192.168.1.10",
                local_port=5062,
                transport="udp",
                device_user="door",
                device_domain="192.168.1.20",
                device_port=5060,
            )
        )

        result = adapter.simulate_session("gds-front-door")

        self.assertEqual(result["mode"], "sip-session")
        self.assertEqual(len(result["lifecycle"]), 4)
        self.assertEqual(result["lifecycle"][0]["action"], "register")
        self.assertEqual(result["lifecycle"][1]["action"], "invite")
        self.assertEqual(result["lifecycle"][2]["action"], "accept")
        self.assertEqual(result["lifecycle"][3]["action"], "hangup")

    def test_build_baresip_preview_contains_account_line(self) -> None:
        adapter = SipAdapter(
            SipEndpointConfig(
                device_label="gds3725",
                local_user="vigilia",
                local_domain="192.168.1.10",
                local_port=5062,
                transport="udp",
                device_user="door",
                device_domain="192.168.1.20",
                device_port=5060,
            )
        )

        result = adapter.build_baresip_preview("gds-front-door")

        self.assertEqual(result["mode"], "baresip-preview")
        self.assertEqual(
            result["baresip"]["account_line"],
            "<sip:vigilia@192.168.1.10:5062;transport=udp>;regint=0",
        )


if __name__ == "__main__":
    unittest.main()

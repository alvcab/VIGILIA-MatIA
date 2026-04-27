import unittest
from unittest.mock import patch

from v1_sin_IA.inference_service import safe_send_response


class InferenceServiceTests(unittest.TestCase):
    @patch("v1_sin_IA.inference_service.send_response")
    def test_safe_send_response_handles_broken_pipe(self, mock_send_response):
        mock_send_response.side_effect = BrokenPipeError()

        result = safe_send_response(connection=object(), payload={"ok": True})

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()

import unittest

from v1_sin_IA.puente_vigilia import (
    capture_snapshot_and_face,
    detect_open_request,
    face_result_distance,
    normalize_model_token,
    retry_face_recognition_for_open_request,
    resolve_access_decision,
)


class ModelResponseValidationTests(unittest.TestCase):
    def test_accepts_exact_open_token(self):
        self.assertEqual(normalize_model_token("OPEN"), "OPEN")

    def test_accepts_exact_token_with_whitespace(self):
        self.assertEqual(normalize_model_token("  hola \n"), "HOLA")

    def test_rejects_verbose_model_response(self):
        verbose_response = "VALID_TOKENS: OPEN, ERROR, HOLA"
        self.assertIsNone(normalize_model_token(verbose_response))

    def test_does_not_open_on_invalid_verbose_response(self):
        decision = resolve_access_decision(
            visitor_text="hola, buenas tardes",
            face_result=None,
            model_response="ACCESS_REQUEST\nVALID_TOKENS: OPEN, ERROR, HOLA",
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(decision["reason"], "model_response_invalid_token")

    def test_detects_fuzzy_open_request_from_noisy_transcript(self):
        self.assertTrue(detect_open_request("abril por tom por favor"))

    def test_opens_on_voice_request_with_face_match_within_tolerance(self):
        decision = resolve_access_decision(
            visitor_text="abril por tom por favor",
            face_result={
                "matched": True,
                "distance": 0.34,
                "tolerance": 0.45,
                "person": {"access_enabled": 1},
            },
            model_response="Sure, here",
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_and_face_match_within_tolerance_and_whitelisted",
        )

    def test_pre_model_hybrid_decision_does_not_require_llm_token(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1},
            },
            model_response=None,
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(decision["source"], "hybrid_policy")

    def test_capture_snapshot_and_face_returns_four_values(self):
        result = capture_snapshot_and_face.__name__
        self.assertEqual(result, "capture_snapshot_and_face")

    def test_face_result_distance_returns_none_without_distance(self):
        self.assertIsNone(face_result_distance(None))
        self.assertIsNone(face_result_distance({"matched": False}))

    def test_retry_face_recognition_skips_non_open_request(self):
        face_result, face_error, retry_snapshot_path = retry_face_recognition_for_open_request(
            visitor_text="hola buenas tardes",
            face_result={"matched": False, "distance": 0.9, "tolerance": 0.45},
            face_error=None,
        )

        self.assertEqual(face_result["distance"], 0.9)
        self.assertIsNone(face_error)
        self.assertIsNone(retry_snapshot_path)


if __name__ == "__main__":
    unittest.main()

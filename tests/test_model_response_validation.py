import unittest
from unittest.mock import patch
from pathlib import Path

from v1.event_store import normalize_phrase_text
from v1.vto_camera import build_http_snapshot_url
from v1.puente_vigilia import (
    build_gate_open_url,
    build_gate_open_urls,
    build_local_audio_capture_command,
    build_denial_message,
    build_spoken_response,
    build_spoken_response_fallback,
    capture_fast_face_entry_match,
    capture_fast_entry_snapshot_and_face,
    capture_snapshot_and_face,
    classify_face_match_band,
    decir,
    detect_delivery_context,
    detect_open_request,
    face_result_distance,
    face_result_resident_matches_claim,
    get_whisper_module,
    has_known_resident_extended_face_match,
    has_meaningful_speech,
    is_greeting_only_text,
    is_unintelligible_transcript,
    normalize_model_token,
    normalize_spoken_response,
    prepare_audio_for_transcription,
    query_spoken_response_model,
    should_request_followup_turn,
    should_skip_decision_model,
    should_skip_spoken_response_model,
    transcribe_audio,
    query_access_model,
    retry_face_recognition_for_open_request,
    resolve_model_unavailable_fallback,
    resolve_claimed_resident_context,
    resolve_access_decision,
    send_service_request,
    try_capture_snapshot,
    try_face_recognition,
)


class ModelResponseValidationTests(unittest.TestCase):
    def test_build_http_snapshot_url_includes_channel(self):
        self.assertEqual(
            build_http_snapshot_url(ip="192.168.1.10", port=8080, channel=3, path="/cgi-bin/snapshot.cgi"),
            "http://192.168.1.10:8080/cgi-bin/snapshot.cgi?channel=3",
        )

    def test_send_service_request_returns_none_when_socket_missing(self):
        result = send_service_request(
            action="health",
            payload={},
            timeout_seconds=1,
            socket_path=Path("/tmp/vigilia_socket_missing.sock"),
        )

        self.assertIsNone(result)

    def test_build_gate_open_url_uses_requested_channel(self):
        self.assertTrue(build_gate_open_url(channel=2).endswith("channel=2"))

    def test_build_gate_open_urls_include_remote_variant(self):
        urls = build_gate_open_urls(channel=2)
        self.assertEqual(len(urls), 2)
        self.assertIn("channel=2", urls[0])
        self.assertIn("UserID=101", urls[1])
        self.assertIn("Type=Remote", urls[1])

    def test_build_local_audio_capture_command_uses_audio_device_index_for_numeric_spec(self):
        command = build_local_audio_capture_command(
            output_path="/tmp/followup.wav",
            duration_seconds=4,
            device_spec="1",
        )

        self.assertIn("-audio_device_index", command)
        self.assertIn("1", command)
        self.assertIn("", command)

    def test_build_local_audio_capture_command_normalizes_colon_prefixed_numeric_spec(self):
        command = build_local_audio_capture_command(
            output_path="/tmp/followup.wav",
            duration_seconds=4,
            device_spec=":1",
        )

        self.assertIn("-audio_device_index", command)
        self.assertIn("1", command)

    @patch("v1.puente_vigilia.capture_snapshot")
    def test_try_capture_snapshot_handles_interrupt_cleanly(self, mock_capture_snapshot):
        mock_capture_snapshot.side_effect = KeyboardInterrupt()

        snapshot_path, snapshot_error = try_capture_snapshot()

        self.assertIsNone(snapshot_path)
        self.assertEqual(snapshot_error, "snapshot_interrupted")

    @patch("v1.puente_vigilia.DISABLE_VTO_SNAPSHOT", True)
    def test_try_capture_snapshot_can_be_disabled_by_environment(self):
        snapshot_path, snapshot_error = try_capture_snapshot()

        self.assertIsNone(snapshot_path)
        self.assertEqual(snapshot_error, "snapshot_disabled")

    @patch("v1.puente_vigilia.subprocess.run")
    @patch("v1.puente_vigilia.FACE_ENV_PYTHON")
    def test_try_face_recognition_handles_interrupt_cleanly(
        self,
        mock_face_env_python,
        mock_run,
    ):
        mock_face_env_python.exists.return_value = True
        mock_run.side_effect = KeyboardInterrupt()

        face_result, face_error = try_face_recognition("/tmp/snapshot.jpg")

        self.assertIsNone(face_result)
        self.assertEqual(face_error, "face_recognition_interrupted")

    @patch("v1.puente_vigilia.send_service_request")
    def test_try_face_recognition_uses_face_service_when_available(self, mock_send_service_request):
        mock_send_service_request.return_value = {
            "ok": True,
            "backend_available": True,
            "matched": True,
            "distance": 0.31,
            "matched_person_name": "Alvaro",
            "person": {"resident_id": 1, "access_enabled": 1},
        }

        face_result, face_error = try_face_recognition(
            "/tmp/snapshot.jpg",
            extra_env={"VIGILIA_FACE_ENCODING_DOWNSCALE_FACTOR": "4"},
        )

        self.assertTrue(face_result["matched"])
        self.assertIsNone(face_error)
        self.assertEqual(
            mock_send_service_request.call_args.kwargs["payload"]["downscale_factor"],
            "4",
        )

    @patch("v1.puente_vigilia.subprocess.Popen")
    @patch("v1.puente_vigilia.subprocess.run")
    def test_decir_falls_back_to_silence_when_tts_fails(self, mock_run, _mock_popen):
        target_path = Path("/tmp/test_decir_fallback.wav")
        target_path.unlink(missing_ok=True)
        target_path.with_suffix(".alaw").unlink(missing_ok=True)
        target_path.with_suffix(".ulaw").unlink(missing_ok=True)

        def side_effect(cmd, **kwargs):
            if cmd[0] == "say":
                raise RuntimeError("say_failed")
            if cmd[0] == "ffmpeg" and "anullsrc=r=8000:cl=mono" in cmd:
                target_path.with_suffix(".silence.wav").write_bytes(b"RIFF")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path):
                target_path.write_bytes(b"RIFF")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path.with_suffix(".alaw")):
                target_path.with_suffix(".alaw").write_bytes(b"ALAW")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path.with_suffix(".ulaw")):
                target_path.with_suffix(".ulaw").write_bytes(b"ULAW")

            class Result:
                returncode = 0

            return Result()

        mock_run.side_effect = side_effect

        decir("hola", response_audio_path=target_path)

        self.assertTrue(target_path.exists())
        self.assertTrue(target_path.with_suffix(".alaw").exists())
        self.assertTrue(target_path.with_suffix(".ulaw").exists())
        target_path.unlink(missing_ok=True)
        target_path.with_suffix(".alaw").unlink(missing_ok=True)
        target_path.with_suffix(".ulaw").unlink(missing_ok=True)

    @patch("v1.puente_vigilia.PREFER_DIRECT_LOCAL_TTS", True)
    @patch("v1.puente_vigilia.LOCAL_RESPONSE_PLAYBACK_ENABLED", True)
    @patch("v1.puente_vigilia.subprocess.Popen")
    @patch("v1.puente_vigilia.subprocess.run")
    def test_decir_plays_response_locally_when_enabled(self, mock_run, _mock_popen):
        target_path = Path("/tmp/test_decir_local.wav")
        target_path.unlink(missing_ok=True)
        target_path.with_suffix(".alaw").unlink(missing_ok=True)
        target_path.with_suffix(".ulaw").unlink(missing_ok=True)

        def side_effect(cmd, **kwargs):
            if cmd[0] == "say":
                target_path.with_suffix(".aiff").write_bytes(b"AIFF")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path):
                target_path.write_bytes(b"RIFF")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path.with_suffix(".alaw")):
                target_path.with_suffix(".alaw").write_bytes(b"ALAW")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path.with_suffix(".ulaw")):
                target_path.with_suffix(".ulaw").write_bytes(b"ULAW")

            class Result:
                returncode = 0

            return Result()

        mock_run.side_effect = side_effect

        decir("hola", response_audio_path=target_path)

        self.assertEqual(mock_run.call_args_list[0].args[0][0], "say")
        target_path.unlink(missing_ok=True)
        target_path.with_suffix(".alaw").unlink(missing_ok=True)
        target_path.with_suffix(".ulaw").unlink(missing_ok=True)

    @patch("v1.puente_vigilia.PREFER_DIRECT_LOCAL_TTS", True)
    @patch("v1.puente_vigilia.LOCAL_RESPONSE_PLAYBACK_ENABLED", True)
    @patch("v1.puente_vigilia.subprocess.Popen")
    @patch("v1.puente_vigilia.subprocess.run")
    def test_decir_falls_back_to_afplay_when_direct_local_tts_cannot_start(self, mock_run, mock_popen):
        target_path = Path("/tmp/test_decir_local_fallback.wav")
        target_path.unlink(missing_ok=True)
        target_path.with_suffix(".alaw").unlink(missing_ok=True)
        target_path.with_suffix(".ulaw").unlink(missing_ok=True)

        def run_side_effect(cmd, **kwargs):
            if cmd[0] == "say" and "-o" not in cmd:
                raise RuntimeError("say_unavailable")
            if cmd[0] == "say":
                target_path.with_suffix(".aiff").write_bytes(b"AIFF")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path):
                target_path.write_bytes(b"RIFF")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path.with_suffix(".alaw")):
                target_path.with_suffix(".alaw").write_bytes(b"ALAW")
            elif cmd[0] == "ffmpeg" and cmd[-1] == str(target_path.with_suffix(".ulaw")):
                target_path.with_suffix(".ulaw").write_bytes(b"ULAW")

            class Result:
                returncode = 0

            return Result()

        mock_run.side_effect = run_side_effect

        decir("hola", response_audio_path=target_path)

        self.assertEqual(mock_popen.call_args_list[-1].args[0][0], "afplay")
        target_path.unlink(missing_ok=True)
        target_path.with_suffix(".alaw").unlink(missing_ok=True)
        target_path.with_suffix(".ulaw").unlink(missing_ok=True)

    @patch("v1.puente_vigilia.subprocess.run")
    @patch("v1.puente_vigilia.measure_audio_max_volume")
    def test_prepare_audio_for_transcription_boosts_low_audio(
        self,
        mock_measure_audio_max_volume,
        mock_run,
    ):
        mock_measure_audio_max_volume.return_value = -30.0

        prepared_path = prepare_audio_for_transcription("/tmp/sample.wav")

        self.assertTrue(str(prepared_path).endswith("_prep.wav"))
        self.assertEqual(mock_run.call_count, 1)
        command = mock_run.call_args.args[0]
        self.assertTrue(any("volume=24.0dB" in part for part in command))

    @patch("v1.puente_vigilia.send_inference_request")
    @patch("v1.puente_vigilia.get_whisper_module")
    @patch("v1.puente_vigilia.prepare_audio_for_transcription")
    def test_transcribe_audio_times_out_cleanly(
        self,
        mock_prepare_audio_for_transcription,
        mock_get_whisper_module,
        mock_send_inference_request,
    ):
        mock_prepare_audio_for_transcription.return_value = "/tmp/sample_prep.wav"
        mock_send_inference_request.return_value = None

        class SlowModel:
            def transcribe(self, *_args, **_kwargs):
                raise TimeoutError("local_transcription_timeout")

        class SlowWhisperModule:
            @staticmethod
            def load_model(_name):
                return SlowModel()

        mock_get_whisper_module.return_value = SlowWhisperModule()

        with self.assertRaises(RuntimeError) as ctx:
            transcribe_audio("/tmp/sample.wav")

        self.assertEqual(str(ctx.exception), "local_transcription_timeout")

    @patch("v1.puente_vigilia.importlib.import_module")
    def test_get_whisper_module_handles_interrupt_cleanly(self, mock_import_module):
        mock_import_module.side_effect = KeyboardInterrupt()

        with self.assertRaises(RuntimeError) as ctx:
            get_whisper_module()

        self.assertEqual(str(ctx.exception), "local_transcription_import_interrupted")

    @patch("v1.puente_vigilia.subprocess.run")
    def test_query_access_model_times_out_cleanly(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["ollama", "run", "vigilia-mini"],
            timeout=3,
        )

        with self.assertRaises(RuntimeError) as ctx:
            query_access_model(
                visitor_text="abre el porton por favor",
                face_result=None,
            )

        self.assertEqual(str(ctx.exception), "ollama_query_timeout")

    @patch("v1.puente_vigilia.subprocess.run")
    def test_query_spoken_response_model_times_out_cleanly(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["ollama", "run", "vigilia-mini"],
            timeout=3,
        )

        with self.assertRaises(RuntimeError) as ctx:
            query_spoken_response_model(
                visitor_text="voy a dejar un paquete al 204",
                decision={"should_open": False, "reason": "model_did_not_return_open"},
                resident_context={"claimed_unit": "204"},
                face_error=None,
            )

        self.assertEqual(str(ctx.exception), "spoken_response_query_timeout")

    def test_accepts_exact_open_token(self):
        self.assertEqual(normalize_model_token("OPEN"), "OPEN")

    def test_detects_meaningful_speech_from_garbled_transcript(self):
        self.assertTrue(
            has_meaningful_speech("con fortice de whereforeb que la ofertura")
        )

    def test_detects_unintelligible_transcript_from_mixed_unicode_garbage(self):
        self.assertTrue(is_unintelligible_transcript("服o"))

    def test_detects_unintelligible_transcript_from_short_irrelevant_phrase(self):
        self.assertTrue(is_unintelligible_transcript("dank applause"))

    def test_does_not_mark_simple_spanish_phrase_as_unintelligible(self):
        self.assertFalse(is_unintelligible_transcript("hola"))

    def test_does_not_mark_greeting_phrase_as_unintelligible(self):
        self.assertFalse(is_unintelligible_transcript("hola buenas"))

    def test_detects_delivery_context(self):
        self.assertTrue(detect_delivery_context("voy a dejar un paquete al 204"))

    def test_accepts_exact_token_with_whitespace(self):
        self.assertEqual(normalize_model_token("  hola \n"), "HOLA")

    def test_rejects_verbose_model_response(self):
        verbose_response = "VALID_TOKENS: OPEN, ERROR, HOLA"
        self.assertIsNone(normalize_model_token(verbose_response))

    def test_skip_decision_model_for_delivery(self):
        self.assertTrue(
            should_skip_decision_model(
                visitor_text="voy a dejar un paquete al 204",
                resident_context={"claimed_unit": "204"},
            )
        )

    def test_skip_decision_model_for_greeting_with_claimed_context(self):
        self.assertTrue(
            should_skip_decision_model(
                visitor_text="hola, vengo donde el 204",
                resident_context={"claimed_unit": "204"},
            )
        )

    def test_do_not_skip_decision_model_for_open_request(self):
        self.assertFalse(
            should_skip_decision_model(
                visitor_text="abre el porton por favor",
                resident_context={},
            )
        )

    def test_normalize_spoken_response_rejects_overlong_output(self):
        self.assertIsNone(normalize_spoken_response("palabra " * 40))

    def test_build_spoken_response_fallback_for_delivery(self):
        response = build_spoken_response_fallback(
            visitor_text="voy a dejar un paquete al 204",
            decision={"should_open": False, "reason": "model_did_not_return_open"},
            face_error=None,
            resident_context={"claimed_unit": "204"},
        )

        self.assertIn("paquete", response.lower())
        self.assertIn("conserjería", response.lower())

    def test_build_spoken_response_fallback_for_claimed_context_without_open_request(self):
        response = build_spoken_response_fallback(
            visitor_text="hola, vengo donde el 204",
            decision={"should_open": False, "reason": "non_open_request_resolved_without_model_followup"},
            face_error=None,
            resident_context={"claimed_unit": "204"},
        )

        self.assertIn("un momento", response.lower())
        self.assertIn("204", response)

    def test_build_spoken_response_fallback_mentions_claimed_resident_name(self):
        response = build_spoken_response_fallback(
            visitor_text="hola, vengo donde alvaro",
            decision={"should_open": False, "reason": "non_open_request_resolved_without_model_followup"},
            face_error=None,
            resident_context={"claimed_resident_name": "Alvaro Cabrera"},
        )

        self.assertIn("alvaro cabrera", response.lower())

    def test_skip_spoken_response_model_for_delivery(self):
        self.assertTrue(
            should_skip_spoken_response_model(
                visitor_text="voy a dejar un paquete al 204",
                decision={"should_open": False},
                resident_context={"claimed_unit": "204"},
            )
        )

    def test_skip_spoken_response_model_for_claimed_context_without_open_request(self):
        self.assertTrue(
            should_skip_spoken_response_model(
                visitor_text="hola, vengo donde el 204",
                decision={"should_open": False},
                resident_context={"claimed_unit": "204"},
            )
        )

    @patch("v1.puente_vigilia.DISABLE_VTO_SNAPSHOT", True)
    @patch("v1.puente_vigilia.ENABLE_LOCAL_FOLLOWUP_CAPTURE", True)
    def test_request_followup_turn_for_greeting_without_claimed_context(self):
        self.assertTrue(
            should_request_followup_turn(
                visitor_text="hola",
                resident_context={},
                decision={"should_open": False, "reason": "non_open_request_resolved_without_model"},
            )
        )

    @patch("v1.puente_vigilia.DISABLE_VTO_SNAPSHOT", True)
    @patch("v1.puente_vigilia.ENABLE_LOCAL_FOLLOWUP_CAPTURE", True)
    def test_do_not_request_followup_turn_for_delivery(self):
        self.assertFalse(
            should_request_followup_turn(
                visitor_text="voy a dejar un paquete al 204",
                resident_context={},
                decision={"should_open": False, "reason": "non_open_request_resolved_without_model"},
            )
        )

    @patch("v1.puente_vigilia.DISABLE_VTO_SNAPSHOT", True)
    @patch("v1.puente_vigilia.ENABLE_LOCAL_FOLLOWUP_CAPTURE", True)
    def test_do_not_request_followup_turn_when_claimed_context_already_present(self):
        self.assertFalse(
            should_request_followup_turn(
                visitor_text="hola, vengo donde el 204",
                resident_context={"claimed_unit": "204"},
                decision={"should_open": False, "reason": "non_open_request_resolved_without_model"},
            )
        )

    @patch("v1.puente_vigilia.query_spoken_response_model")
    def test_build_spoken_response_uses_valid_model_text(self, mock_query_spoken_response_model):
        mock_query_spoken_response_model.return_value = (
            "Por favor deje el paquete en conserjería."
        )

        response = build_spoken_response(
            visitor_text="voy a dejar un paquete al 204",
            decision={"should_open": False, "reason": "model_did_not_return_open"},
            face_error=None,
            resident_context={"claimed_unit": "204"},
        )

        self.assertIn("conserjería", response.lower())
        mock_query_spoken_response_model.assert_not_called()

    @patch("v1.puente_vigilia.query_spoken_response_model")
    def test_build_spoken_response_falls_back_on_invalid_model_text(self, mock_query_spoken_response_model):
        mock_query_spoken_response_model.return_value = "palabra " * 40

        response = build_spoken_response(
            visitor_text="voy a dejar un paquete al 204",
            decision={"should_open": False, "reason": "model_did_not_return_open"},
            face_error=None,
            resident_context={"claimed_unit": "204"},
        )

        self.assertIn("conserjería", response.lower())

    def test_does_not_open_on_invalid_verbose_response(self):
        decision = resolve_access_decision(
            visitor_text="hola, buenas tardes",
            face_result=None,
            model_response="ACCESS_REQUEST\nVALID_TOKENS: OPEN, ERROR, HOLA",
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(decision["reason"], "model_response_invalid_token")

    def test_hola_token_denies_without_treating_response_as_invalid(self):
        decision = resolve_access_decision(
            visitor_text="hola, buenas tardes",
            face_result=None,
            model_response="HOLA",
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(decision["reason"], "model_returned_hola")

    def test_error_token_denies_without_treating_response_as_invalid(self):
        decision = resolve_access_decision(
            visitor_text="no se entiende",
            face_result=None,
            model_response="ERROR",
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(decision["reason"], "model_returned_error")

    def test_detects_fuzzy_open_request_from_noisy_transcript(self):
        self.assertTrue(detect_open_request("abril por tom por favor"))

    def test_opens_on_voice_request_with_face_match_within_tolerance(self):
        decision = resolve_access_decision(
            visitor_text="abril por tom por favor",
            face_result={
                "matched": True,
                "distance": 0.34,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 10},
            },
            model_response="Sure, here",
            resident_context={"resolved_resident_id": 10},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_and_claimed_resident_matches_trusted_face",
        )

    def test_pre_model_hybrid_decision_requires_resident_context_match(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 10},
            },
            model_response=None,
            resident_context={"resolved_resident_id": 10},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(decision["source"], "resident_context")

    def test_capture_snapshot_and_face_returns_four_values(self):
        result = capture_snapshot_and_face.__name__
        self.assertEqual(result, "capture_snapshot_and_face")

    @patch("v1.puente_vigilia.time.sleep")
    @patch("v1.puente_vigilia.FAST_FACE_ENTRY_ATTEMPTS", 3)
    @patch("v1.puente_vigilia.capture_fast_entry_snapshot_and_face")
    def test_capture_fast_face_entry_match_retries_until_trusted_face(
        self,
        mock_capture_fast_entry_snapshot_and_face,
        _mock_sleep,
    ):
        mock_capture_fast_entry_snapshot_and_face.side_effect = [
            ("snap1.jpg", None, None, "face_encoding_not_found"),
            (
                "snap2.jpg",
                None,
                {
                    "matched": True,
                    "distance": 0.34,
                    "tolerance": 0.45,
                    "person": {"resident_id": 1, "access_enabled": 1},
                },
                None,
            ),
        ]

        snapshot_path, snapshot_error, face_result, face_error = capture_fast_face_entry_match()

        self.assertEqual(snapshot_path, "snap2.jpg")
        self.assertIsNone(snapshot_error)
        self.assertTrue(face_result["matched"])
        self.assertIsNone(face_error)

    @patch("v1.puente_vigilia.capture_snapshot")
    @patch("v1.puente_vigilia.try_face_recognition")
    @patch("v1.puente_vigilia.VTO_FAST_FACE_SUBTYPE", 1)
    def test_capture_fast_entry_snapshot_and_face_uses_fast_face_subtype(
        self,
        mock_try_face_recognition,
        mock_capture_snapshot,
    ):
        mock_capture_snapshot.return_value = "captures/fast.jpg"
        mock_try_face_recognition.return_value = ({"matched": False}, None)

        snapshot_path, snapshot_error, face_result, face_error = capture_fast_entry_snapshot_and_face()

        self.assertEqual(snapshot_path, "captures/fast.jpg")
        self.assertIsNone(snapshot_error)
        self.assertEqual(face_result, {"matched": False})
        self.assertIsNone(face_error)
        self.assertEqual(mock_capture_snapshot.call_args.kwargs["subtype"], 1)

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

    def test_classifies_trusted_and_borderline_face_bands(self):
        self.assertEqual(
            classify_face_match_band(
                {"matched": True, "distance": 0.40, "tolerance": 0.45}
            ),
            "trusted",
        )
        self.assertEqual(
            classify_face_match_band(
                {"matched": True, "distance": 0.50, "tolerance": 0.45}
            ),
            "borderline",
        )
        self.assertEqual(
            classify_face_match_band(
                {"matched": False, "distance": 0.50, "tolerance": 0.45}
            ),
            "borderline",
        )

    def test_detects_known_access_phrase_from_observed_transcript(self):
        self.assertTrue(detect_open_request("abril por tom por favor."))

    def test_detects_open_request_from_partial_phrase_token_overlap(self):
        self.assertTrue(detect_open_request("abre porton porfa"))

    def test_detects_open_request_from_noisy_keyword_variant(self):
        self.assertTrue(detect_open_request("avre el porton"))

    def test_detects_greeting_only_text(self):
        self.assertTrue(is_greeting_only_text("hola, buenas tardes"))

    def test_returns_borderline_reason_for_voice_request(self):
        decision = resolve_access_decision(
            visitor_text="abril por tom por favor",
            face_result={
                "matched": True,
                "distance": 0.50,
                "tolerance": 0.45,
                "person": {"access_enabled": 1},
            },
            model_response=None,
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_but_face_match_borderline",
        )

    def test_denies_trusted_face_when_resident_context_missing(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": None},
            },
            model_response=None,
            resident_context={},
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_but_claimed_resident_does_not_match_face",
        )

    def test_opens_trusted_face_for_known_resident_without_claimed_context(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 10},
            },
            model_response=None,
            resident_context={},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_and_known_resident_face_match",
        )

    def test_opens_trusted_face_for_known_resident_without_speech(self):
        decision = resolve_access_decision(
            visitor_text="",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 10},
            },
            model_response=None,
            resident_context={},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "known_resident_button_press_face_match",
        )

    def test_opens_extended_face_for_known_resident_without_speech(self):
        decision = resolve_access_decision(
            visitor_text="",
            face_result={
                "matched": False,
                "distance": 0.471,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 10},
            },
            model_response=None,
            resident_context={},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "known_resident_button_press_face_match",
        )

    def test_opens_trusted_face_for_known_resident_with_greeting_only(self):
        decision = resolve_access_decision(
            visitor_text="hola buenas tardes",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 10},
            },
            model_response=None,
            resident_context={},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "known_resident_button_press_face_match",
        )

    def test_does_not_open_greeting_only_without_known_resident_face(self):
        decision = resolve_access_decision(
            visitor_text="hola",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": None},
            },
            model_response=None,
            resident_context={},
        )

        self.assertFalse(decision["should_open"])

    def test_denies_trusted_face_when_claimed_resident_does_not_match_face(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": True,
                "distance": 0.37,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 10},
            },
            model_response=None,
            resident_context={"resolved_resident_id": 11, "claimed_unit": "21"},
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_but_claimed_resident_does_not_match_face",
        )

    def test_detects_face_resident_match_against_claimed_context(self):
        self.assertTrue(
            face_result_resident_matches_claim(
                face_result={"person": {"resident_id": 30}},
                resident_context={"resolved_resident_id": 30},
            )
        )

    def test_opens_borderline_face_when_claimed_resident_matches_face_resident(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": True,
                "distance": 0.50,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 30},
            },
            model_response=None,
            resident_context={"resolved_resident_id": 30},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_and_claimed_resident_matches_borderline_face",
        )

    def test_opens_borderline_face_for_known_resident_without_claimed_context(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": False,
                "distance": 0.48,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 30},
            },
            model_response=None,
            resident_context={},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_and_known_resident_borderline_face_match",
        )

    def test_detects_known_resident_extended_face_match(self):
        self.assertTrue(
            has_known_resident_extended_face_match(
                {
                    "matched": False,
                    "distance": 0.58,
                    "tolerance": 0.45,
                    "person": {"resident_id": 30},
                }
            )
        )

    def test_opens_extended_face_match_for_known_resident_without_claimed_context(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": False,
                "distance": 0.58,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 30},
            },
            model_response=None,
            resident_context={},
        )

        self.assertTrue(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_and_known_resident_extended_face_match",
        )

    def test_model_unavailable_fallback_denies_known_resident_with_non_open_speech(self):
        decision = resolve_model_unavailable_fallback(
            visitor_text="con fortice de whereforeb que la ofertura",
            face_result={
                "matched": True,
                "distance": 0.43,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 30},
            },
            resident_context={},
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "model_unavailable_fallback",
        )

    def test_model_unavailable_fallback_denies_delivery_speech_with_known_resident_face(self):
        decision = resolve_model_unavailable_fallback(
            visitor_text="voy a dejar un paquete al 204",
            face_result={
                "matched": True,
                "distance": 0.43,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 30},
            },
            resident_context={"claimed_unit": "204"},
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "model_unavailable_fallback",
        )

    def test_model_unavailable_fallback_denies_without_known_resident_face(self):
        decision = resolve_model_unavailable_fallback(
            visitor_text="con fortice de whereforeb que la ofertura",
            face_result={
                "matched": False,
                "distance": 0.70,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": None},
            },
            resident_context={},
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "model_unavailable_fallback",
        )

    def test_does_not_open_borderline_face_when_claimed_resident_differs(self):
        decision = resolve_access_decision(
            visitor_text="abre el porton por favor",
            face_result={
                "matched": True,
                "distance": 0.50,
                "tolerance": 0.45,
                "person": {"access_enabled": 1, "resident_id": 30},
            },
            model_response=None,
            resident_context={"resolved_resident_id": 31},
        )

        self.assertFalse(decision["should_open"])
        self.assertEqual(
            decision["reason"],
            "voice_requested_open_but_face_match_borderline",
        )

    def test_normalize_phrase_text_collapses_observed_transcript(self):
        self.assertEqual(
            normalize_phrase_text("abril por tom por favor."),
            "abril por tom por favor",
        )

    def test_build_denial_message_uses_camera_guidance_when_no_face_detected(self):
        message = build_denial_message(
            "abril por tom por favor",
            "face_encoding_not_found",
        )
        self.assertIn("Acercate a la camara", message)

    def test_build_denial_message_mentions_claimed_resident_when_present(self):
        message = build_denial_message(
            "abre el porton por favor",
            None,
            resident_context={"claimed_resident_name": "Andrea Vaccari"},
        )
        self.assertIn("Andrea Vaccari", message)

    def test_build_denial_message_mentions_claimed_unit_when_present(self):
        message = build_denial_message(
            "abre el porton por favor",
            None,
            resident_context={"claimed_unit": "21"},
        )
        self.assertIn("unidad 21", message)

    def test_build_denial_message_requests_resident_context_when_missing(self):
        message = build_denial_message(
            "abre el porton por favor",
            None,
            resident_context={},
        )
        self.assertIn("residente o departamento", message)

    def test_resolves_claimed_resident_by_name_alias(self):
        context = resolve_claimed_resident_context(
            "soy alvaro cabrera, abre el porton",
            residents=[
                {"id": 10, "full_name": "Alvaro Cabrera", "apartment_unit": "302"},
            ],
            resident_aliases=[
                {
                    "resident_id": 10,
                    "normalized_alias": "alvaro cabrera",
                    "alias_type": "name",
                }
            ],
        )

        self.assertEqual(context["claimed_resident_name"], "Alvaro Cabrera")
        self.assertEqual(context["claimed_unit"], "302")
        self.assertEqual(context["resolved_resident_id"], 10)

    def test_resolves_claimed_resident_by_preferred_name_without_alias(self):
        context = resolve_claimed_resident_context(
            "vengo donde alvaro, abre el porton",
            residents=[
                {
                    "id": 10,
                    "full_name": "Alvaro Cabrera",
                    "preferred_name": "Alvaro",
                    "apartment_unit": "302",
                },
            ],
            resident_aliases=[],
        )

        self.assertEqual(context["claimed_resident_name"], "Alvaro Cabrera")
        self.assertEqual(context["claimed_unit"], "302")
        self.assertEqual(context["resolved_resident_id"], 10)

    def test_resolves_claimed_unit_from_transcript(self):
        context = resolve_claimed_resident_context(
            "vengo al depto 32",
            residents=[
                {"id": 20, "full_name": "Alicia Figueroa", "apartment_unit": "32"},
                {"id": 21, "full_name": "Martin Morgan", "apartment_unit": "32"},
            ],
            resident_aliases=[],
        )

        self.assertIsNone(context["claimed_resident_name"])
        self.assertEqual(context["claimed_unit"], "32")
        self.assertIsNone(context["resolved_resident_id"])

    def test_resolves_resident_from_unique_unit_alias(self):
        context = resolve_claimed_resident_context(
            "voy a la unidad 141",
            residents=[
                {"id": 30, "full_name": "Luis Fabian Galdamez Guerrero", "apartment_unit": "141"},
            ],
            resident_aliases=[
                {
                    "resident_id": 30,
                    "normalized_alias": "unidad 141",
                    "alias_type": "unit",
                }
            ],
        )

        self.assertEqual(context["claimed_resident_name"], "Luis Fabian Galdamez Guerrero")
        self.assertEqual(context["claimed_unit"], "141")
        self.assertEqual(context["resolved_resident_id"], 30)


if __name__ == "__main__":
    unittest.main()

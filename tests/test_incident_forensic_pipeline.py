import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.incident_forensic_pipeline import start_new

class TestIncidentForensicPipeline(unittest.TestCase):

    def test_start_new_execution_flow(self):
        rand_incident_id = uuid.uuid4().hex
        rand_telemetry_source = f"stream_{uuid.uuid4().hex[:8]}"
        rand_metric_threshold = random.uniform(10.0, 99.9)

        mock_telemetry_data = f"metric_id={rand_incident_id}&source={rand_telemetry_source}&val={rand_metric_threshold}"
        mock_stream = io.BytesIO(mock_telemetry_data.encode('utf-8'))

        with patch('skills.incident_forensic_pipeline.telemetry_streamer') as mock_streamer, \
             patch('skills.incident_forensic_pipeline.system_health_telemetry_collector') as mock_collector, \
             patch('skills.incident_forensic_pipeline.incident_impact_analyzer') as mock_analyzer:

            mock_streamer.return_value = mock_stream
            mock_collector.collect.return_value = {
                "incident_ref": rand_incident_id,
                "status": "active"
            }
            mock_analyzer.evaluate.return_value = {
                "severity_score": rand_metric_threshold,
                "target_id": rand_incident_id
            }

            result = start_new(rand_incident_id, source=rand_telemetry_source)

            self.assertIsNotNone(result)
            self.assertIsInstance(result, dict)
            self.assertIn("incident_ref", result)
            self.assertEqual(result["incident_ref"], rand_incident_id)

    def test_start_new_anomaly_handling(self):
        rand_error_code = "".join(random.choices(string.ascii_uppercase, k=6))
        rand_payload = uuid.uuid4().hex

        with patch('skills.incident_forensic_pipeline.telemetry_anomaly_evaluator_core') as mock_evaluator, \
             patch('skills.incident_forensic_pipeline.error_recovery_hub') as mock_recovery:

            mock_evaluator.detect.return_value = {
                "error_code": rand_error_code,
                "anomaly_detected": True,
                "payload": rand_payload
            }
            mock_recovery.dispatch.return_value = {
                "status": "recovered",
                "handled_error": rand_error_code
            }

            outcome = start_new(rand_payload, mode="audit")

            self.assertIsInstance(outcome, dict)
            self.assertEqual(outcome.get("handled_error"), rand_error_code)
            mock_evaluator.detect.assert_called_once()
            mock_recovery.dispatch.assert_called_once()

    def test_start_new_invalid_payload_rejection(self):
        rand_invalid_token = uuid.uuid4().hex

        with patch('skills.incident_forensic_pipeline.system_health_audit_pipeline') as mock_audit:
            mock_audit.run_audit.side_effect = ValueError(f"Corrupted token: {rand_invalid_token}")

            with self.assertRaises(ValueError) as ctx:
                start_new(rand_invalid_token, strict=True)

            self.assertIn(rand_invalid_token, str(ctx.exception))
            mock_audit.run_audit.assert_called_once()

    def test_start_new_with_randomized_telemetry_stream(self):
        rand_stream_id = uuid.uuid4().hex
        random_bytes_payload = os_random_bytes = bytes(random.getrandbits(8) for _ in range(64))

        mock_file_obj = io.BytesIO(random_bytes_payload)

        with patch('skills.incident_forensic_pipeline.telemetry_processor') as mock_processor, \
             patch('skills.incident_forensic_pipeline.incident_aggregator') as mock_aggregator:

            mock_processor.process_stream.return_value = {
                "stream_id": rand_stream_id,
                "bytes_processed": len(random_bytes_payload)
            }
            mock_aggregator.aggregate.return_value = {
                "final_id": rand_stream_id,
                "state": "compiled"
            }

            res = start_new(mock_file_obj, stream_mode=True)

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("final_id"), rand_stream_id)
            mock_processor.process_stream.assert_called_once()
            mock_aggregator.aggregate.assert_called_once()
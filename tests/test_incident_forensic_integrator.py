import unittest
from unittest.mock import patch
import io
import uuid
import random
from skills import incident_forensic_integrator

class TestIncidentForensicIntegratorArchitect(unittest.TestCase):

    def test_start_new_raises_on_invalid_identifier(self):
        rand_invalid = random.choice([None, ""])
        with self.assertRaises(ValueError):
            incident_forensic_integrator.start_new(incident_id=rand_invalid, incident_uuid=rand_invalid)

    def test_start_new_success_aggregation(self):
        inc_id = uuid.uuid4().hex
        stream_tok = uuid.uuid4().hex
        rand_bytes = uuid.uuid4().bytes

        with patch("skills.telemetry_streamer.stream") as mock_stream, \
             patch("skills.telemetry_processor.process") as mock_proc, \
             patch("skills.incident_aggregator.aggregate") as mock_agg:

            mock_stream.return_value = io.BytesIO(rand_bytes)
            mock_proc.return_value = io.BytesIO(rand_bytes)
            mock_agg.return_value = {"status": "ok", "incident_id": inc_id}

            res = incident_forensic_integrator.start_new(
                incident_uuid=inc_id,
                stream_token=stream_tok
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("incident_id"), inc_id)
            mock_stream.assert_called_once_with(token=stream_tok)
            mock_proc.assert_called_once()
            mock_agg.assert_called_once()

    def test_start_new_handles_malformed_telemetry_stream(self):
        inc_id = uuid.uuid4().hex
        rand_bytes = uuid.uuid4().bytes

        with patch("skills.telemetry_processor.process") as mock_proc, \
             patch("skills.incident_aggregator.aggregate") as mock_agg:

            mock_proc.return_value = io.BytesIO(rand_bytes)
            mock_agg.return_value = "raw_string_data"

            res = incident_forensic_integrator.start_new(
                incident_id=inc_id
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("incident_id"), inc_id)
            self.assertEqual(res.get("data"), "raw_string_data")

    def test_start_new_invokes_severity_evaluator(self):
        inc_id = uuid.uuid4().hex
        rand_bytes = uuid.uuid4().bytes
        sev_val = random.choice(["HIGH", "CRITICAL", "LOW", "MEDIUM"])

        with patch("skills.telemetry_processor.process") as mock_proc, \
             patch("skills.incident_aggregator.aggregate") as mock_agg, \
             patch("skills.incident_severity_evaluator.evaluate") as mock_eval:

            mock_proc.return_value = io.BytesIO(rand_bytes)
            mock_agg.return_value = {"incident_id": inc_id}
            mock_eval.return_value = sev_val

            res = incident_forensic_integrator.start_new(
                incident_id=inc_id,
                deep_inspection=True
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("severity"), sev_val)
            mock_eval.assert_called_once_with(inc_id)

if __name__ == "__main__":
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine, escalate_incident_automatically

class TestIncidentAutoEscalationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.incident_id = uuid.uuid4().hex
        self.error_message = uuid.uuid4().hex
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.error_code = random.randint(1000, 9999)

    def test_escalate_critical_incident(self):
        mock_agg_result = {"aggregated": True, "id": self.incident_id}
        mock_pipeline_result = {"patched": True, "status": "success"}

        with patch("skills.incident_auto_escalation_engine.incident_aggregator.aggregate_incident") as mock_agg, \
             patch("skills.incident_auto_escalation_engine.auto_patch_pipeline.execute_pipeline") as mock_pipe:

            mock_agg.return_value = mock_agg_result
            mock_pipe.return_value = mock_pipeline_result

            result = self.engine.escalate_critical_incident(self.incident_id, self.error_message, self.severity_level)

            mock_agg.assert_called_once_with(self.incident_id, self.error_message)
            mock_pipe.assert_called_once_with(mock_agg_result)

            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["aggregator_result"], mock_agg_result)
            self.assertEqual(result["pipeline_result"], mock_pipeline_result)
            self.assertEqual(result["status"], "escalated")

    def test_process_incident_log_stream_with_process_stream(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        expected_output = {"processed": True, "bytes": len(random_bytes)}

        with patch("skills.incident_auto_escalation_engine.incident_aggregator", create=True) as mock_agg:
            mock_agg.process_stream = MagicMock(return_value=expected_output)

            result = self.engine.process_incident_log_stream(stream)

            mock_agg.process_stream.assert_called_once_with(stream)
            self.assertEqual(result, expected_output)

    def test_process_incident_log_stream_fallback(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)

        with patch("skills.incident_auto_escalation_engine.incident_aggregator", create=True) as mock_agg:
            if hasattr(mock_agg, 'process_stream'):
                delattr(mock_agg, 'process_stream')

            result = self.engine.process_incident_log_stream(stream)

            self.assertEqual(result, {"processed_bytes": len(random_bytes)})

    def test_escalate_incident_automatically(self):
        aggregated_incident = {
            "incident_id": self.incident_id,
            "error_code": self.error_code,
            "payload": self.error_message
        }

        with patch("skills.incident_auto_escalation_engine.incident_aggregator.aggregate_incident") as mock_agg:
            result = escalate_incident_automatically(aggregated_incident)

            mock_agg.assert_called_once_with(self.incident_id, self.error_message)
            self.assertEqual(result["status"], "escalated")
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["error_code"], self.error_code)
            self.assertEqual(result["payload"], self.error_message)

if __name__ == "__main__":
    unittest.main()
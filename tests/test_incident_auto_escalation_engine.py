import unittest
from unittest.mock import patch
import io
import uuid
import random
import string

from skills.incident_auto_escalation_engine import (
    escalate_incident,
    evaluate_and_escalate
)


class TestIncidentAutoEscalationEngine(unittest.TestCase):

    def test_escalate_incident_execution(self):
        rand_id = uuid.uuid4().hex
        rand_system = "".join(random.choices(string.ascii_lowercase, k=8))
        rand_severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])

        mock_target = "skills.incident_auto_escalation_engine.incident_aggregator"
        with patch(mock_target) as mock_aggregator:
            mock_aggregator.return_value = {
                "id": rand_id,
                "system": rand_system,
                "severity": rand_severity,
                "status": "escalated"
            }

            result = escalate_incident(rand_id, rand_system, rand_severity)

            mock_aggregator.assert_called_once_with(rand_id, rand_system, rand_severity)
            self.assertEqual(result["id"], rand_id)
            self.assertEqual(result["system"], rand_system)
            self.assertEqual(result["severity"], rand_severity)
            self.assertEqual(result["status"], "escalated")

    def test_evaluate_and_escalate_trigger(self):
        rand_id = uuid.uuid4().hex
        threshold = random.randint(50, 100)
        metric_value = threshold + random.randint(1, 50)

        prefix = "".join(random.choices(string.ascii_lowercase, k=5))
        stream_content = f"{prefix}:{rand_id}:{metric_value}".encode('utf-8')
        stream_data = io.BytesIO(stream_content)

        mock_target = "skills.incident_auto_escalation_engine.incident_aggregator"
        with patch(mock_target) as mock_aggregator:
            expected_payload = {
                "incident_id": rand_id,
                "escalated": True
            }
            mock_aggregator.return_value = expected_payload

            result = evaluate_and_escalate(stream_data, threshold)

            mock_aggregator.assert_called_once_with(rand_id, "default_system", "CRITICAL")
            self.assertEqual(result, expected_payload)

    def test_evaluate_and_escalate_below_threshold(self):
        rand_id = uuid.uuid4().hex
        threshold = random.randint(50, 100)
        metric_value = threshold - random.randint(1, 49)

        prefix = "".join(random.choices(string.ascii_lowercase, k=5))
        stream_content = f"{prefix}:{rand_id}:{metric_value}".encode('utf-8')
        stream_data = io.BytesIO(stream_content)

        mock_target = "skills.incident_auto_escalation_engine.incident_aggregator"
        with patch(mock_target) as mock_aggregator:
            result = evaluate_and_escalate(stream_data, threshold)

            mock_aggregator.assert_not_called()
            self.assertIsNone(result)

    def test_evaluate_and_escalate_malformed_stream(self):
        threshold = random.randint(10, 50)
        bad_content = "".join(random.choices(string.ascii_letters, k=15)).encode('utf-8')
        stream_data = io.BytesIO(bad_content)

        mock_target = "skills.incident_auto_escalation_engine.incident_aggregator"
        with patch(mock_target) as mock_aggregator:
            result = evaluate_and_escalate(stream_data, threshold)

            mock_aggregator.assert_not_called()
            self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import tempfile
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine

class TestIncidentAutoEscalationEngine(unittest.TestCase):
    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.severity_score = round(random.uniform(1.0, 10.0), 2)
        self.failure_history_count = random.randint(1, 100)
        self.escalation_tier = f"tier_{random.randint(1, 5)}"
        self.evaluated_score = round(self.severity_score * random.uniform(1.1, 2.0), 2)

        self.aggregator_mock = MagicMock()
        self.severity_evaluator_mock = MagicMock()
        self.trend_analyzer_mock = MagicMock()

        self.severity_evaluator_mock.evaluate.return_value = self.evaluated_score
        self.trend_analyzer_mock.determine_escalation_tier.return_value = self.escalation_tier

        self.engine = IncidentAutoEscalationEngine(
            incident_aggregator=self.aggregator_mock,
            severity_evaluator=self.severity_evaluator_mock,
            trend_analyzer=self.trend_analyzer_mock
        )

    def test_process_escalation_flow(self):
        incident_details = {
            "severity_score": self.severity_score,
            "failure_history_count": self.failure_history_count
        }
        self.aggregator_mock.get_incident_details.return_value = incident_details

        result = self.engine.process_escalation(self.incident_id)

        self.aggregator_mock.get_incident_details.assert_called_once_with(self.incident_id)
        self.severity_evaluator_mock.evaluate.assert_called_once_with(self.severity_score)
        self.trend_analyzer_mock.determine_escalation_tier.assert_called_once_with(self.failure_history_count)
        self.aggregator_mock.update_status.assert_called_once_with(
            self.incident_id, "escalated", tier=self.escalation_tier
        )

        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertEqual(result["escalation_tier"], self.escalation_tier)
        self.assertEqual(result["severity_score"], self.evaluated_score)

    def test_handle_stream_escalation(self):
        payload = {
            "stream_id": str(uuid.uuid4()),
            "metric": random.choice(["cpu", "memory", "disk"]),
            "value": random.randint(50, 100)
        }
        expected_response = {"ingested": True, "token": uuid.uuid4().hex}
        self.aggregator_mock.ingest_raw_stream.return_value = expected_response

        result = self.engine.handle_stream_escalation(payload)

        self.aggregator_mock.ingest_raw_stream.assert_called_once_with(payload)
        self.assertEqual(result, expected_response)

    def test_evaluate_and_escalate_success_with_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            metric_value = round(random.uniform(10.0, 500.0), 2)
            incident_details = {
                "metric_value": metric_value,
                "storage_path": tmpdir
            }
            self.aggregator_mock.get_incident_details.return_value = incident_details

            result = self.engine.evaluate_and_escalate(self.incident_id)

            self.assertTrue(result["escalated"])
            self.assertEqual(result["target_incident_id"], self.incident_id)

            marker_file = os.path.join(tmpdir, f"escalation_{self.incident_id}.lock")
            self.assertTrue(os.path.exists(marker_file))
            with open(marker_file, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(str(metric_value), content)

    def test_evaluate_and_escalate_empty_details(self):
        self.aggregator_mock.get_incident_details.return_value = {}

        result = self.engine.evaluate_and_escalate(self.incident_id)

        self.assertTrue(result["escalated"])
        self.assertEqual(result["target_incident_id"], self.incident_id)
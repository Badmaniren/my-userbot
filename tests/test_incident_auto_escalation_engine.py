import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    incident_auto_escalation_engine
)

class TestIncidentAutoEscalationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.incident_id = uuid.uuid4().hex
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.trend_score = round(random.uniform(1.0, 10.0), 2)

    def test_evaluate_and_escalate_structure(self):
        payload = {
            "id": self.incident_id,
            "severity": self.severity,
            "trend": self.trend_score
        }
        result = self.engine.evaluate_and_escalate(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertEqual(result.get("severity"), self.severity)
        self.assertEqual(result.get("trend_score"), self.trend_score)
        self.assertEqual(result.get("status"), "SUCCESS")
        self.assertIn("escalated_to", result)

    def test_evaluate_and_escalate_defaults(self):
        payload = {}
        result = self.engine.evaluate_and_escalate(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("severity"), "MEDIUM")
        self.assertEqual(result.get("trend_score"), 1.0)
        self.assertEqual(result.get("status"), "SUCCESS")

    def test_process_stream_valid_data(self):
        random_prefix = uuid.uuid4().hex[:6]
        stream_content = f"STATUS:OK,INCIDENT_ID:{self.incident_id},METRIC:{random_prefix}"
        stream_mock = io.BytesIO(stream_content.encode('utf-8'))

        result = self.engine.process_stream(stream_mock)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("stream_id"), self.incident_id)
        self.assertTrue(result.get("processed"))
        self.assertEqual(result.get("action"), "AUTO_ESCALATE")

    def test_process_stream_missing_id(self):
        stream_content = f"STATUS:ERROR,DATA:{uuid.uuid4().hex}"
        stream_mock = io.BytesIO(stream_content.encode('utf-8'))

        result = self.engine.process_stream(stream_mock)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("stream_id"), "")
        self.assertTrue(result.get("processed"))

    def test_analyze_trends(self):
        result = self.engine.analyze_trends(self.incident_id)
        self.assertIsInstance(result, dict)
        self.assertIn("trend_score", result)
        self.assertIsInstance(result["trend_score"], (int, float))

    def test_functional_incident_auto_escalation_engine(self):
        severity_result = {"severity": self.severity}
        trend_result = {"trend_score": self.trend_score}

        result = incident_auto_escalation_engine(severity_result, trend_result)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("escalate"))
        self.assertEqual(result.get("destination"), "devops_team")
        self.assertEqual(result.get("severity"), self.severity)
        self.assertEqual(result.get("trend_score"), self.trend_score)

if __name__ == '__main__':
    unittest.main()
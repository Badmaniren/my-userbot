import unittest
import uuid
import random
from skills.telemetry_anomaly_response_bridge import (
    TelemetryAnomalyResponseBridge,
    auto_escalate_incident
)
from skills.telemetry_anomaly_evaluator_core import TelemetryAnomalyEvaluatorCore
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine


class TestTelemetryAnomalyResponseBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.bridge = TelemetryAnomalyResponseBridge()
        self.unique_incident_id = f"inc-{uuid.uuid4()}"
        self.random_metric_value = random.randint(9000, 99999)

    def test_handle_telemetry_and_respond_integration(self):
        payload = {
            "is_anomaly": True,
            "incident_id": self.unique_incident_id,
            "metric_value": self.random_metric_value,
            "source": "integration_test_stream"
        }

        result = self.bridge.handle_telemetry_and_respond(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("evaluation", result)
        self.assertIn("escalation", result)

        evaluation = result["evaluation"]
        self.assertIsInstance(evaluation, dict)
        self.assertTrue(evaluation.get("is_anomaly"))
        self.assertEqual(evaluation.get("incident_id"), self.unique_incident_id)

        escalation = result["escalation"]
        self.assertIsNotNone(escalation)
        self.assertIsInstance(escalation, dict)

    def test_process_stream_and_mitigate_integration(self):
        class MockStreamSource:
            def __init__(self, data):
                self.data = data.encode('utf-8')
            def read(self):
                return self.data

        stream_data = f'{{"anomaly_detected": true, "payload_id": "{uuid.uuid4()}"}}'
        stream_source = MockStreamSource(stream_data)

        result = self.bridge.process_stream_and_mitigate(stream_source)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("stream_evaluated"))
        self.assertIn("patching_triggered", result)
        self.assertIsInstance(result["patching_triggered"], bool)

    def test_auto_escalate_incident_helper_integration(self):
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severity_levels)

        result = auto_escalate_incident(
            incident_id=self.unique_incident_id,
            severity=chosen_severity,
            workspace_dir=None
        )

        self.assertIsInstance(result, dict)
        if "status" in result:
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["incident_id"], self.unique_incident_id)


if __name__ == "__main__":
    unittest.main()
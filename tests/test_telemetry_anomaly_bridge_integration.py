import unittest
import uuid
import random
import io
from skills.telemetry_anomaly_bridge import TelemetryAnomalyBridge


class TestTelemetryAnomalyBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.bridge = TelemetryAnomalyBridge()
        self.random_metric_id = f"metric-{uuid.uuid4()}"
        self.random_value = random.uniform(100.0, 1000.0)

    def test_process_telemetry_payload_integration(self):
        payload = {
            "metric_id": self.random_metric_id,
            "value": self.random_value,
            "trigger_incident": True
        }

        result = self.bridge.process_telemetry_payload(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("evaluation", result)
        self.assertIn("escalation", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "PROCESSED")

        evaluation = result["evaluation"]
        self.assertIsInstance(evaluation, dict)
        self.assertTrue(evaluation.get("incident_triggered"))
        self.assertEqual(evaluation.get("evaluated_stream"), self.random_metric_id)

        if result["status"] == "PROCESSED":
            self.assertIsNotNone(result["escalation"])
            self.assertIsInstance(result["escalation"], dict)

    def test_process_stream_integration(self):
        stream_data = f"metric_id:{self.random_metric_id},value:{self.random_value}".encode("utf-8")
        stream_io = io.BytesIO(stream_data)

        result = self.bridge.process_stream(stream_io)

        self.assertIsInstance(result, dict)
        self.assertIn("stream_evaluation", result)
        self.assertIn("escalation_response", result)
        self.assertIsInstance(result["stream_evaluation"], dict)

    def test_evaluate_and_patch_risks_integration(self):
        result = self.bridge.evaluate_and_patch_risks()

        self.assertIsInstance(result, dict)
        self.assertIn("risk_report", result)
        self.assertIn("patch_triggered", result)
        self.assertIsInstance(result["risk_report"], dict)
        self.assertIsInstance(result["patch_triggered"], bool)

    def test_process_and_escalate_integration(self):
        payload = {
            "metric_id": self.random_metric_id,
            "anomaly_score": random.randint(50, 100)
        }

        result = self.bridge.process_and_escalate(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("escalation_status"), "escalated")
        self.assertIn("incident_id", result)
        self.assertIn("evaluation", result)

    def test_handle_stream_payload_integration(self):
        raw_data = uuid.uuid4().bytes + str(self.random_value).encode("utf-8")

        result = self.bridge.handle_stream_payload(raw_data)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("escalated"))
        self.assertEqual(result.get("status"), "handled")
        self.assertIn("incident_id", result)
        self.assertIn("escalation", result)
        self.assertIn("stream_evaluation", result)


if __name__ == "__main__":
    unittest.main()
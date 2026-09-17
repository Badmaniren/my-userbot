import unittest
import uuid
import random
from skills.telemetry_incident_trigger import TelemetryIncidentTrigger, TelemetryTriggerException


class TestTelemetryIncidentTriggerIntegration(unittest.TestCase):
    def setUp(self):
        self.trigger = TelemetryIncidentTrigger(module_name=f"test_module_{uuid.uuid4().hex[:8]}")

    def test_process_telemetry_normal_flow(self):
        random_metric_val = random.uniform(10.0, 50.0)
        payload = {
            "metric": "cpu_load",
            "value": random_metric_val,
            "unit": "percent",
            "timestamp": uuid.uuid4().hex
        }

        result = self.trigger.process_telemetry(payload)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success"))
        self.assertIn("incident_triggered", result)

    def test_process_telemetry_anomaly_flow(self):
        random_incident_id = f"INC-{random.randint(10000, 99999)}"
        anomaly_payload = {
            "metric": "memory_leak_critical",
            "value": 999.99,
            "force_anomaly": True,
            "incident_id": random_incident_id,
            "reason": f"Critical spike generated at {uuid.uuid4()}"
        }

        result = self.trigger.process_telemetry(anomaly_payload)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success"))

        if result.get("incident_triggered"):
            self.assertEqual(result.get("incident_id"), random_incident_id)

    def test_evaluate_stream_integration(self):
        from io import StringIO
        stream_data = StringIO(f"metric,value\ncore_temp,{random.randint(70, 120)}\n")

        result = self.trigger.evaluate_stream(stream_data)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success"))
        self.assertIn("anomalies_found", result)
        self.assertIn("stream_processed", result)


if __name__ == "__main__":
    unittest.main()
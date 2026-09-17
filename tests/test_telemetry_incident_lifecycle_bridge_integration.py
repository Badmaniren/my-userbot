import unittest
import os
import tempfile
import uuid
import random
from skills.telemetry_incident_lifecycle_bridge import (
    TelemetryIncidentLifecycleBridge,
    BridgeException
)


class TestTelemetryIncidentLifecycleBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.bridge = TelemetryIncidentLifecycleBridge(workspace_dir=self.test_dir)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_process_lifecycle_event_integration(self):
        rand_id = str(uuid.uuid4())
        metric_value = random.randint(100, 9999)
        
        telemetry_payload = {
            "source_id": rand_id,
            "metric": "cpu_load",
            "value": metric_value,
            "status": "ANOMALY_DETECTED"
        }

        response = self.bridge.process_lifecycle_event(telemetry_payload)

        self.assertIsInstance(response, dict)
        self.assertIn("incident_id", response)
        self.assertEqual(response["incident_id"], f"incident_{rand_id}")
        self.assertIn("lifecycle_status", response)

        expected_artifact_path = os.path.join(self.test_dir, f"incident_{rand_id}.json")
        self.assertTrue(os.path.exists(expected_artifact_path))

        with open(expected_artifact_path, "r") as f:
            content = f.read()
            self.assertIn(rand_id, content)
            self.assertIn(str(metric_value), content)

    def test_bridge_exception_handling(self):
        invalid_payload = None
        with self.assertRaises(BridgeException):
            self.bridge.process_lifecycle_event(invalid_payload)


if __name__ == "__main__":
    unittest.main()
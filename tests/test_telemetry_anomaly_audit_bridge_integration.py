import unittest
import tempfile
import os
import uuid
import random
from skills.telemetry_anomaly_audit_bridge import TelemetryAnomalyAuditBridge, AnomalyAuditBridgeException

class TestTelemetryAnomalyAuditBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.bridge = TelemetryAnomalyAuditBridge(workspace_dir=self.test_dir.name)
        self.incident_id = f"INC-{uuid.uuid4()}"
        self.epic_id = f"EPIC-{random.randint(1000, 9999)}"
        self.stream_name = f"stream-{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_audit_health_after_incident_integration(self):
        telemetry_payload = {
            "incident_id": self.incident_id,
            "status": "active",
            "metric_value": random.uniform(50.0, 500.0)
        }

        result = self.bridge.audit_health_after_incident(
            telemetry_payload=telemetry_payload,
            epic_id=self.epic_id,
            stream=self.stream_name
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertIn("lifecycle_closed", result)
        self.assertIn("audit_report", result)
        self.assertIn("epic_finalized", result)

    def test_process_anomaly_and_audit_integration(self):
        telemetry_payload = {
            "incident_id": self.incident_id,
            "anomaly_score": random.random()
        }
        audit_data = {
            "vulnerability_count": random.randint(0, 10),
            "check_status": "PASSED"
        }

        result = self.bridge.process_anomaly_and_audit(
            telemetry_payload=telemetry_payload,
            audit_data=audit_data
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), self.incident_id)
        self.assertEqual(result.get("lifecycle_status"), "PROCESSED")
        self.assertIsNotNone(result.get("audit_report"))

    def test_generate_epic_health_export_integration(self):
        output_file = os.path.join(self.test_dir.name, f"report_{uuid.uuid4().hex}.json")
        payload = {
            "epic_id": self.epic_id,
            "metrics": [random.randint(1, 100) for _ in range(3)]
        }

        export_result = self.bridge.generate_epic_health_export(payload, output_file)
        
        self.assertIsNotNone(export_result)
        self.assertTrue(os.path.exists(output_file))


if __name__ == "__main__":
    unittest.main()
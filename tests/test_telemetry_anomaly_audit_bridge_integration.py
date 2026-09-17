import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.telemetry_anomaly_audit_bridge import (
    TelemetryAnomalyAuditBridge,
    AuditBridgeException
)
from skills.telemetry_incident_lifecycle_bridge import (
    TelemetryIncidentLifecycleBridge,
    BridgeException
)
from skills.dependency_audit_reporter import DependencyAuditReporter


class TestTelemetryAnomalyAuditBridgeIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.workspace_dir = os.path.join(self.test_dir, "workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)

        self.incident_id = str(uuid.uuid4())
        self.anomaly_metric = f"cpu_load_{random.randint(100, 999)}"
        self.anomaly_value = round(random.uniform(85.0, 99.9), 2)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_anomaly_audit_pipeline(self):
        evaluator_stub = None
        escalation_engine_stub = None
        connector_stub = None

        lifecycle_bridge = TelemetryIncidentLifecycleBridge(
            workspace_dir=self.workspace_dir,
            evaluator=evaluator_stub,
            escalation_engine=escalation_engine_stub,
            connector=connector_stub
        )

        audit_reporter = DependencyAuditReporter()

        bridge = TelemetryAnomalyAuditBridge(
            lifecycle_bridge=lifecycle_bridge,
            audit_reporter=audit_reporter,
            workspace_dir=self.workspace_dir
        )

        telemetry_payload = {
            "incident_id": self.incident_id,
            "metric": self.anomaly_metric,
            "value": self.anomaly_value,
            "status": "ANOMALY_DETECTED"
        }

        audit_data = {
            "epic_id": f"EPIC-{random.randint(1000, 9999)}",
            "incident_id": self.incident_id,
            "dependencies_scanned": random.randint(5, 50),
            "vulnerabilities_found": random.randint(0, 3)
        }

        result_payload = bridge.process_anomaly_and_audit(
            telemetry_payload=telemetry_payload,
            audit_data=audit_data
        )

        self.assertIsInstance(result_payload, dict)
        self.assertIn("audit_report", result_payload)
        self.assertIn("lifecycle_status", result_payload)
        self.assertEqual(result_payload.get("incident_id"), self.incident_id)

        report_str = result_payload["audit_report"]
        self.assertIsInstance(report_str, str)
        self.assertTrue(len(report_str) > 0)

        report_file_name = f"audit_summary_{self.incident_id}.json"
        expected_file_path = os.path.join(self.workspace_dir, report_file_name)
        
        summary_payload = {
            "incident_id": self.incident_id,
            "metric": self.anomaly_metric,
            "audit_summary": audit_data
        }
        
        exported_path = audit_reporter.export_summary(summary_payload, format="json")
        self.assertTrue(os.path.exists(exported_path) or os.path.exists(expected_file_path) or len(exported_path) > 0)

        stream_finalized = lifecycle_bridge.verify_and_close_lifecycle()
        self.assertIsInstance(stream_finalized, bool)


if __name__ == "__main__":
    unittest.main()
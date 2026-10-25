import unittest
import os
import tempfile
import uuid
import random

from skills.anomaly_alert_dispatcher import dispatch_alert
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyAlertDispatcherIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.json")
        self.repo_path = self.test_dir.name
        
        self.source = f"service_{uuid.uuid4().hex[:8]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_value = round(random.uniform(10.0, 500.0), 2)
        
        self.details = {
            "error_code": random.randint(500, 599),
            "message": f"Random failure event {uuid.uuid4()}"
        }
        self.telemetry = {
            "cpu_usage": round(random.uniform(50.0, 99.9), 1),
            "memory_mb": random.randint(1024, 8192)
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_alert_integration_real_flow(self):
        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=random.uniform(50.0, 100.0)
        )
        
        hub.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot=self.telemetry
        )
        
        hub.aggregate_and_report(
            metric_name=self.metric_name,
            value=self.metric_value
        )

        dispatch_result = dispatch_alert(
            audit_hub=hub,
            target_service=self.source,
            dispatch_id=str(uuid.uuid4())
        )

        self.assertTrue(os.path.exists(self.log_path), "Integration failed: Audit log file was not created on disk.")
        
        logger = AnomalyLogger(log_path=self.log_path)
        recorded_anomalies = logger.get_anomalies()
        
        self.assertGreaterEqual(len(recorded_anomalies), 1, "Integration failed: No anomalies recorded by AnomalyLogger.")
        
        latest_anomaly = recorded_anomalies[-1]
        self.assertEqual(latest_anomaly.get("source"), self.source)
        self.assertEqual(latest_anomaly.get("severity"), self.severity)
        self.assertEqual(latest_anomaly.get("details", {}).get("error_code"), self.details["error_code"])

        self.assertIsNotNone(dispatch_result, "Integration failed: dispatch_alert did not return a valid payload.")

if __name__ == "__main__":
    unittest.main()
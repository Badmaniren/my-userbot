import unittest
import uuid
import random
import tempfile
import os

from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_alert_dispatcher import AnomalyAlertDispatcher, AnomalyAlertDispatcherError, dispatch_alert


class TestAnomalyAlertDispatcherIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"test_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.temp_dir.name
        
        self.threshold = random.randint(5, 20)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        
        self.source = f"service_{uuid.uuid4().hex[:6]}"
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.details = f"Anomaly detected by integration test: {uuid.uuid4().hex}"
        self.telemetry = {"cpu_load": random.uniform(80.0, 99.9), "memory": random.randint(1024, 8192)}
        
        self.audit_hub.log_anomaly(
            source=self.source,
            severity=self.severity,
            details=self.details,
            telemetry_snapshot=self.telemetry
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dispatch_alert_integration_with_audit_hub(self):
        dispatch_id = f"dispatch-{uuid.uuid4()}"
        target_service = f"target-{uuid.uuid4().hex[:8]}"
        
        payload = dispatch_alert(
            audit_hub=self.audit_hub,
            target_service=target_service,
            dispatch_id=dispatch_id
        )
        
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("dispatch_id"), dispatch_id)
        self.assertEqual(payload.get("target_service"), target_service)
        self.assertEqual(payload.get("status"), "dispatched")
        
        anomalies = payload.get("anomalies")
        self.assertIsInstance(anomalies, list)
        self.assertGreaterEqual(len(anomalies), 1)
        
        logged_anomaly = anomalies[0]
        self.assertEqual(logged_anomaly.get("source"), self.source)
        self.assertEqual(logged_anomaly.get("severity"), self.severity)
        self.assertEqual(logged_anomaly.get("details"), self.details)
        self.assertEqual(logged_anomaly.get("telemetry_snapshot"), self.telemetry)

    def test_anomaly_alert_dispatcher_invalid_endpoint(self):
        dispatcher = AnomalyAlertDispatcher(endpoint="")
        with self.assertRaises(AnomalyAlertDispatcherError):
            dispatcher.dispatch_alert(
                severity=self.severity,
                message=self.details,
                telemetry=self.telemetry
            )


if __name__ == "__main__":
    unittest.main()
import unittest
import uuid
import random
import tempfile
import os
from skills.anomaly_alert_dispatcher import AnomalyAlertDispatcher, dispatch_alert, AnomalyAlertDispatcherError
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAlertDispatcherIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"test_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.temp_dir.name
        
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=random.uniform(0.1, 0.9)
        )
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_dispatch_flow_with_audit_hub(self):
        random_source = f"service_{uuid.uuid4().hex[:6]}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = {"error_code": random.randint(500, 599), "reason": uuid.uuid4().hex}
        random_telemetry = {"cpu_load": random.uniform(80.0, 99.9)}
        
        self.audit_hub.log_anomaly(
            source=random_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot=random_telemetry
        )

        dispatch_id = uuid.uuid4().hex
        target_service = f"external_webhook_{uuid.uuid4().hex[:4]}"

        payload = dispatch_alert(
            audit_hub=self.audit_hub,
            target_service=target_service,
            dispatch_id=dispatch_id
        )

        self.assertEqual(payload["dispatch_id"], dispatch_id)
        self.assertEqual(payload["target_service"], target_service)
        self.assertEqual(payload["status"], "dispatched")
        
        anomalies = payload["anomalies"]
        self.assertGreaterEqual(len(anomalies), 1)
        
        matched = False
        for anomaly in anomalies:
            if anomaly.get("source") == random_source:
                self.assertEqual(anomaly.get("severity"), random_severity)
                self.assertEqual(anomaly.get("details"), random_details)
                matched = True
                break
        self.assertTrue(matched, "Logged anomaly was not found in the dispatched payload anomalies.")

        invalid_endpoint = ""
        dispatcher = AnomalyAlertDispatcher(endpoint=invalid_endpoint)
        with self.assertRaises(AnomalyAlertDispatcherError):
            dispatcher.dispatch_alert(
                severity=random_severity,
                message=f"Alert for {dispatch_id}",
                telemetry=random_telemetry
            )

if __name__ == "__main__":
    unittest.main()
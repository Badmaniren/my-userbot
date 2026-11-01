import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_alert_dispatcher import dispatch_alert, AnomalyAlertDispatcher
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAlertDispatcherIntegration(unittest.TestCase):
    def test_dispatch_alert_integration_flow(self):
        unique_id = str(uuid.uuid4())
        metric_value = random.uniform(10.0, 100.0)
        source_name = f"service_{uuid.uuid4().hex[:6]}"
        severity_level = random.choice(["INFO", "WARNING", "CRITICAL"])
        message_text = f"Test anomaly message {unique_id}"

        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "repo")
            log_path = os.path.join(temp_dir, "anomalies.log")
            os.makedirs(repo_path, exist_ok=True)

            audit_hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=50.0)
            
            audit_hub.log_anomaly(
                source=source_name,
                severity=severity_level,
                details={"info": message_text},
                telemetry_snapshot={"metric": metric_value}
            )

            payload = dispatch_alert(
                audit_hub=audit_hub,
                target_service=source_name,
                dispatch_id=unique_id
            )

            self.assertEqual(payload["dispatch_id"], unique_id)
            self.assertEqual(payload["target_service"], source_name)
            self.assertEqual(payload["status"], "dispatched")
            
            anomalies = payload["anomalies"]
            self.assertIsInstance(anomalies, list)
            self.assertGreaterEqual(len(anomalies), 1)

            found = False
            for anomaly in anomalies:
                if anomaly.get("source") == source_name and anomaly.get("severity") == severity_level:
                    found = True
                    self.assertEqual(anomaly["details"]["info"], message_text)
                    self.assertEqual(anomaly["telemetry_snapshot"]["metric"], metric_value)
                    break
            
            self.assertTrue(found, "Logged anomaly should be present in the dispatched payload anomalies list.")

if __name__ == "__main__":
    unittest.main()
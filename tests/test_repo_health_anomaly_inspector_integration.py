import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_anomaly_inspector_real_integration(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        negative_metric_val = -float(random.randint(1, 50))
        high_metric_val = float(random.randint(150, 300))
        threshold_val = 100.0

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        custom_pulse_payload = {
            "metrics": {
                "error_rate": negative_metric_val,
                "latency_ms": high_metric_val,
                "stable_metric": 50.0
            }
        }

        result = inspector.inspect(
            repo_id=unique_repo_id,
            pulse_payload=custom_pulse_payload,
            threshold=threshold_val
        )

        self.assertEqual(result["repo_id"], unique_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)
        self.assertGreater(result["deviation_score"], 0.0)

        found_negative = False
        found_high = False
        for anomaly in result["anomalies"]:
            if anomaly["metric"] == "error_rate" and anomaly["value"] == negative_metric_val:
                found_negative = True
            if anomaly["metric"] == "latency_ms" and anomaly["value"] == high_metric_val:
                found_high = True

        self.assertTrue(found_negative)
        self.assertTrue(found_high)

    def test_anomaly_inspector_automatic_pulse_fetch(self):
        unique_repo_id = f"target-repo-{uuid.uuid4()}"
        inspector = RepoHealthAnomalyInspector()
        
        result = inspector.inspect(repo_id=unique_repo_id)

        self.assertEqual(result["repo_id"], unique_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)

if __name__ == "__main__":
    unittest.main()
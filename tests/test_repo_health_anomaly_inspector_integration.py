import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_integration_real_pulse_flow(self):
        repo_id = str(uuid.uuid4())
        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        
        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(150, 300))
        threshold = 100.0
        
        custom_pulse_payload = {
            "metrics": {
                "test_error_rate": negative_val,
                "test_latency": high_val,
                "test_normal": 50.0
            }
        }
        
        result = inspector.inspect(repo_id=repo_id, pulse_payload=custom_pulse_payload, threshold=threshold)
        
        self.assertEqual(result["repo_id"], repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)
        self.assertGreater(result["deviation_score"], 0.0)
        
        anomaly_metrics = [a["metric"] for a in result["anomalies"]]
        self.assertIn("test_error_rate", anomaly_metrics)
        self.assertIn("test_latency", anomaly_metrics)
        self.assertNotIn("test_normal", anomaly_metrics)

if __name__ == "__main__":
    unittest.main()
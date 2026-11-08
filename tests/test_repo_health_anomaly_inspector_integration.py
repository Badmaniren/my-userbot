import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_integration_real_pulse(self):
        random_repo_id = str(uuid.uuid4())
        
        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        
        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(150, 300))
        normal_val = float(random.randint(1, 50))
        threshold_val = 100.0
        
        custom_payload = {
            "repo_id": random_repo_id,
            "metrics": {
                "cpu_load": normal_val,
                "error_rate": negative_val,
                "latency_ms": high_val
            }
        }
        
        result = inspector.inspect(repo_id=random_repo_id, pulse_payload=custom_payload, threshold=threshold_val)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["repo_id"], random_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        
        anomalies = result["anomalies"]
        self.assertEqual(len(anomalies), 2)
        
        anomaly_metrics = [a["metric"] for a in anomalies]
        self.assertIn("error_rate", anomaly_metrics)
        self.assertIn("latency_ms", anomaly_metrics)
        
        expected_deviation_score = abs(negative_val) + (high_val - threshold_val)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score)

if __name__ == "__main__":
    unittest.main()
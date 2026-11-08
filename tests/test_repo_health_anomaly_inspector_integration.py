import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_anomaly_inspector_integration_flow(self):
        random_repo_id = str(uuid.uuid4())
        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(105, 200))
        threshold_val = 100.0

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        self.assertIsInstance(inspector.logger, RepoLogger)

        custom_payload = {
            "repo_id": random_repo_id,
            "metrics": {
                "error_rate": negative_val,
                "latency_ms": high_val,
                "normal_metric": 50.0
            }
        }

        result = inspector.inspect(repo_id=random_repo_id, pulse_payload=custom_payload, threshold=threshold_val)

        self.assertEqual(result["repo_id"], random_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        metrics_found = {anomaly["metric"] for anomaly in result["anomalies"]}
        self.assertIn("error_rate", metrics_found)
        self.assertIn("latency_ms", metrics_found)
        
        expected_deviation = abs(negative_val) + (high_val - threshold_val)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation)

        fallback_result = inspector.inspect(repo_id=random_repo_id, pulse_payload=None)
        self.assertEqual(fallback_result["repo_id"], random_repo_id)
        self.assertEqual(fallback_result["status"], "inspected")
        self.assertIn("is_anomaly", fallback_result)

if __name__ == "__main__":
    unittest.main()
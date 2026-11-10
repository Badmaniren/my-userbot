import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def setUp(self):
        self.pulse_engine = RepoHealthPulseEngine()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine)

    def test_inspect_real_integration_flow(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        
        random_negative_metric = -float(random.randint(1, 100))
        random_high_metric = float(random.randint(150, 500))
        random_normal_metric = float(random.randint(0, 50))
        
        custom_pulse_payload = {
            "repo_id": unique_repo_id,
            "metrics": {
                "error_rate": random_negative_metric,
                "latency_ms": random_high_metric,
                "cpu_usage": random_normal_metric
            }
        }
        
        threshold_value = 100.0

        result = self.inspector.inspect(
            repo_id=unique_repo_id,
            pulse_payload=custom_pulse_payload,
            threshold=threshold_value
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), unique_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))
        
        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)
        
        metrics_found = [a["metric"] for a in anomalies]
        self.assertIn("error_rate", metrics_found)
        self.assertIn("latency_ms", metrics_found)
        self.assertNotIn("cpu_usage", metrics_found)

        self.assertGreater(result.get("deviation_score", 0.0), 0.0)

    def test_inspect_implicit_pulse_engine_call(self):
        unique_repo_id = f"target-{uuid.uuid4()}"
        
        result = self.inspector.inspect(repo_id=unique_repo_id, threshold=999.0)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), unique_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)


if __name__ == "__main__":
    unittest.main()
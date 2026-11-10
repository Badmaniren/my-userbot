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
        self.random_repo_id = f"repo-{uuid.uuid4()}"

    def test_inspect_real_integration_flow(self):
        negative_metric = -1 * float(random.randint(1, 100))
        high_metric = float(random.randint(101, 1000))
        threshold_val = 50.0

        custom_payload = {
            "repo_id": self.random_repo_id,
            "metrics": {
                "cpu_load": 15.5,
                "error_rate": negative_metric,
                "latency_ms": high_metric
            }
        }

        result = self.inspector.inspect(
            repo_id=self.random_repo_id,
            pulse_payload=custom_payload,
            threshold=threshold_val
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.random_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))
        
        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)
        
        metrics_with_anomalies = [a["metric"] for a in anomalies]
        self.assertIn("error_rate", metrics_with_anomalies)
        self.assertIn("latency_ms", metrics_with_anomalies)
        
        self.assertGreater(result.get("deviation_score", 0.0), 0.0)

    def test_inspect_without_payload_relies_on_pulse_engine(self):
        result = self.inspector.inspect(repo_id=self.random_repo_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.random_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)


if __name__ == "__main__":
    unittest.main()
import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def test_inspect_real_integration_flow(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_negative_metric = -float(random.randint(1, 100))
        random_high_metric = float(random.randint(150, 500))
        threshold_value = 100.0

        pulse_payload = {
            "repo_id": unique_repo_id,
            "metrics": {
                "error_rate": random_negative_metric,
                "latency_ms": random_high_metric,
                "stable_metric": 50.0
            }
        }

        pulse_engine = RepoHealthPulseEngine()
        logger = RepoLogger(repo_path=".")
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)
        inspector.logger = logger

        result = inspector.inspect(
            repo_id=unique_repo_id,
            pulse_payload=pulse_payload,
            threshold=threshold_value
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), unique_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))
        
        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)

        metric_names = [a.get("metric") for a in anomalies]
        self.assertIn("error_rate", metric_names)
        self.assertIn("latency_ms", metric_names)
        self.assertNotIn("stable_metric", metric_names)

        self.assertGreater(result.get("deviation_score", 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
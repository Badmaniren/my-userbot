import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def test_inspect_real_integration_with_pulse_engine(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_negative_metric = -float(random.randint(1, 100))
        random_high_metric = float(random.randint(150, 500))
        random_threshold = float(random.randint(50, 100))

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        custom_payload = {
            "repo_id": unique_repo_id,
            "metrics": {
                "error_rate": random_negative_metric,
                "latency_ms": random_high_metric,
                "stable_metric": float(random.randint(0, 40))
            }
        }

        result = inspector.inspect(
            repo_id=unique_repo_id,
            pulse_payload=custom_payload,
            threshold=random_threshold
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), unique_repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))

        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)

        anomaly_metrics = [a["metric"] for a in anomalies]
        self.assertIn("error_rate", anomaly_metrics)
        self.assertIn("latency_ms", anomaly_metrics)
        self.assertNotIn("stable_metric", anomaly_metrics)

        self.assertGreater(result.get("deviation_score", 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
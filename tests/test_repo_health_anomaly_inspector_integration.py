import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def test_inspect_real_integration_flow(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_negative_val = -float(random.randint(1, 50))
        random_high_val = float(random.randint(150, 300))
        threshold_val = 100.0

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        payload = {
            "repo_id": unique_repo_id,
            "metrics": {
                "error_rate": random_negative_val,
                "latency_ms": random_high_val,
                "stable_metric": 42.0
            }
        }

        result = inspector.inspect(
            repo_id=unique_repo_id,
            pulse_payload=payload,
            threshold=threshold_val
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

        self.assertGreater(result.get("deviation_score", 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
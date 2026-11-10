import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.pulse_engine = RepoHealthPulseEngine()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine)

    def test_inspect_integration_real_data(self):
        negative_metric_key = f"metric_neg_{uuid.uuid4().hex[:6]}"
        high_metric_key = f"metric_high_{uuid.uuid4().hex[:6]}"
        normal_metric_key = f"metric_norm_{uuid.uuid4().hex[:6]}"

        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(150, 300))
        normal_val = float(random.randint(1, 50))
        threshold_val = 100.0

        custom_pulse_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                negative_metric_key: negative_val,
                high_metric_key: high_val,
                normal_metric_key: normal_val
            }
        }

        result = self.inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=custom_pulse_payload,
            threshold=threshold_val
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))

        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)

        anomaly_metrics = [a["metric"] for a in anomalies]
        self.assertIn(negative_metric_key, anomaly_metrics)
        self.assertIn(high_metric_key, anomaly_metrics)
        self.assertNotIn(normal_metric_key, anomaly_metrics)

        expected_deviation = abs(negative_val) + (high_val - threshold_val)
        self.assertAlmostEqual(result.get("deviation_score"), expected_deviation)

    def test_inspect_integration_implicit_pulse_engine(self):
        result = self.inspector.inspect(repo_id=self.repo_id, threshold=50.0)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)


if __name__ == "__main__":
    unittest.main()
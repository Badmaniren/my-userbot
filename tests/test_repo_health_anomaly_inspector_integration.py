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
        high_metric_name = f"metric_load_{uuid.uuid4().hex[:6]}"
        negative_metric_name = f"metric_error_{uuid.uuid4().hex[:6]}"
        normal_metric_name = f"metric_stable_{uuid.uuid4().hex[:6]}"

        threshold_value = float(random.randint(50, 100))
        high_value = threshold_value + float(random.randint(10, 50))
        negative_value = -float(random.randint(1, 20))
        normal_value = float(random.randint(0, int(threshold_value)))

        custom_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                high_metric_name: high_value,
                negative_metric_name: negative_value,
                normal_metric_name: normal_value
            }
        }

        result = self.inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=custom_payload,
            threshold=threshold_value
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertEqual(result.get("status"), "inspected")
        self.assertTrue(result.get("is_anomaly"))

        anomalies = result.get("anomalies", [])
        self.assertGreaterEqual(len(anomalies), 2)

        anomaly_metrics = [a["metric"] for a in anomalies]
        self.assertIn(high_metric_name, anomaly_metrics)
        self.assertIn(negative_metric_name, anomaly_metrics)
        self.assertNotIn(normal_metric_name, anomaly_metrics)

        expected_deviation = abs(negative_value) + (high_value - threshold_value)
        self.assertAlmostEqual(result.get("deviation_score", 0.0), expected_deviation)


if __name__ == "__main__":
    unittest.main()
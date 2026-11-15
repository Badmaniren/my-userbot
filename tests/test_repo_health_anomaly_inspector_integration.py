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
        random_negative_metric = f"metric_error_{uuid.uuid4().hex[:6]}"
        random_high_metric = f"metric_load_{uuid.uuid4().hex[:6]}"
        
        neg_value = -float(random.randint(1, 100))
        high_value = float(random.randint(150, 500))
        threshold_value = 100.0

        pulse_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                random_negative_metric: neg_value,
                random_high_metric: high_value,
                "normal_metric": 42.0
            }
        }

        result = self.inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=pulse_payload,
            threshold=threshold_value
        )

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreaterEqual(len(result["anomalies"]), 2)
        self.assertGreater(result["deviation_score"], 0.0)

        anomaly_metrics = [a["metric"] for a in result["anomalies"]]
        self.assertIn(random_negative_metric, anomaly_metrics)
        self.assertIn(random_high_metric, anomaly_metrics)

    def test_inspect_integration_engine_fallback(self):
        random_fallback_id = f"fallback-{uuid.uuid4()}"
        
        inspector_default = RepoHealthAnomalyInspector()
        
        result = inspector_default.inspect(repo_id=random_fallback_id)

        self.assertIsInstance(result, dict)
        self.assertIn("repo_id", result)
        self.assertIn("status", result)
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)
        self.assertEqual(result["status"], "inspected")


if __name__ == "__main__":
    unittest.main()
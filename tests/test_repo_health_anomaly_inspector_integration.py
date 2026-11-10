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

    def test_inspect_integration_real_data_flow(self):
        random_metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        negative_value = float(-random.randint(1, 100))
        high_value = float(random.randint(150, 500))
        threshold_val = 100.0

        custom_payload = {
            "repo_id": self.repo_id,
            "metrics": {
                random_metric_name: negative_value,
                "stable_metric": 42.0,
                "over_threshold_metric": high_value
            }
        }

        result = self.inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=custom_payload,
            threshold=threshold_val
        )

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)
        self.assertGreater(result["deviation_score"], 0.0)

        anomaly_metrics = [a["metric"] for a in result["anomalies"]]
        self.assertIn(random_metric_name, anomaly_metrics)
        self.assertIn("over_threshold_metric", anomaly_metrics)
        self.assertNotIn("stable_metric", anomaly_metrics)

    def test_inspect_integration_fallback_pulse_engine(self):
        fallback_repo_id = f"fallback-{uuid.uuid4()}"
        
        result = self.inspector.inspect(repo_id=fallback_repo_id, threshold=50.0)

        self.assertEqual(result["repo_id"], fallback_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)


if __name__ == "__main__":
    unittest.main()
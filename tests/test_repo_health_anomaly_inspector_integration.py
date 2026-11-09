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
        self.repo_id = f"repo-{uuid.uuid4()}"

    def test_inspect_integration_real_pulse(self):
        random_negative_value = -float(random.randint(1, 100))
        random_high_value = float(random.randint(150, 500))
        threshold_value = 100.0

        custom_payload = {
            "metrics": {
                "commit_velocity": random_negative_value,
                "issue_backlog": random_high_value,
                "stable_metric": 50.0
            }
        }

        result = self.inspector.inspect(
            repo_id=self.repo_id,
            pulse_payload=custom_payload,
            threshold=threshold_value
        )

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)
        self.assertGreater(result["deviation_score"], 0.0)

        anomaly_metrics = [anomaly["metric"] for anomaly in result["anomalies"]]
        self.assertIn("commit_velocity", anomaly_metrics)
        self.assertIn("issue_backlog", anomaly_metrics)
        self.assertNotIn("stable_metric", anomaly_metrics)


if __name__ == "__main__":
    unittest.main()
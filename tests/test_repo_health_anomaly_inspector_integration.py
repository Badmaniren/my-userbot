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

    def test_inspect_integration_real_pulse_and_logging(self):
        random_metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        random_negative_value = float(-random.randint(1, 100))
        
        custom_payload = {
            "repo_id": self.random_repo_id,
            "metrics": {
                random_metric_name: random_negative_value,
                "stable_metric": random.randint(1, 50)
            }
        }

        result = self.inspector.inspect(repo_id=self.random_repo_id, pulse_payload=custom_payload, threshold=10.0)

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)

        found_anomaly = False
        for anomaly in result["anomalies"]:
            if anomaly["metric"] == random_metric_name:
                found_anomaly = True
                self.assertEqual(anomaly["value"], random_negative_value)
                self.assertEqual(anomaly["deviation"], "negative")

        self.assertTrue(found_anomaly, "Случайно сгенерированная аномальная метрика не обнаружена инспектором")
        self.assertGreater(result["deviation_score"], 0.0)

    def test_inspect_fallback_to_pulse_engine(self):
        result = self.inspector.inspect(repo_id=self.random_repo_id, pulse_payload=None)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertIn("status", result)
        self.assertIn("is_anomaly", result)
        self.assertIn("anomalies", result)
        self.assertIn("deviation_score", result)


if __name__ == "__main__":
    unittest.main()
import unittest
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):
    def test_inspect_real_integration(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_threshold = round(random.uniform(5.0, 15.0), 2)
        random_normal_val = round(random.uniform(0.0, random_threshold), 2)
        random_high_val = round(random.uniform(random_threshold + 1.0, 50.0), 2)
        random_neg_val = round(random.uniform(-50.0, -0.1), 2)

        pulse_engine = RepoHealthPulseEngine()
        inspector = RepoHealthAnomalyInspector(pulse_engine=pulse_engine)

        # Проверяем сквозное взаимодействие без моков: инспектор вызывает реальный движок и логгер
        payload = {
            "repo_id": unique_repo_id,
            "metrics": {
                "cpu_load": random_normal_val,
                "error_rate": random_high_val,
                "latency_spike": random_neg_val
            }
        }

        result = inspector.inspect(repo_id=unique_repo_id, pulse_payload=payload, threshold=random_threshold)

        self.assertEqual(result["repo_id"], unique_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertGreater(len(result["anomalies"]), 0)
        self.assertGreater(result["deviation_score"], 0.0)

        # Проверка детекции конкретных типов аномалий
        anomaly_metrics = [a["metric"] for a in result["anomalies"]]
        self.assertIn("error_rate", anomaly_metrics)
        self.assertIn("latency_spike", anomaly_metrics)
        self.assertNotIn("cpu_load", anomaly_metrics)


if __name__ == "__main__":
    unittest.main()